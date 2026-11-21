"""Cửa sổ chơi trực tiếp bằng TRÌNH DUYỆT, chỉ dùng thư viện chuẩn Python.

    python3 -m chonoi.live --mode gather|quan|day [--seed N] [--port 8000] [--days 5]

Máy chủ HTTP nhỏ (ThreadingHTTPServer) phục vụ `chonoi/web/index.html` và hai API:
    GET  /state  -> snapshot JSON hiện tại (cùng trường như dòng snapshot của headless) + `meta` + `events`
    POST /input  -> {"move": [a, b], "interact": bool, "catch": bool, "pause": bool, "shop_done": bool,
                     "buy": "oxygen"|"hp"}   (trạng thái phím đang giữ; buy là lệnh một lần)
    POST /restart -> chơi lại từ đầu (cùng seed, cùng scenario)
    POST /continue -> qua màn hình hiện tại (menu chính, DayIntro, EveningIntro, DayResult) · POST /quit -> thoát

Chế độ `day` có thêm màn hình (chỉ ở cửa sổ chơi, KHÔNG tốn tick headless): menu chính -> DayIntro (tự qua sau 4 s
hoặc khi nhấn phím) -> sáng -> EveningIntro -> tối -> DayResult -> Shop -> DayIntro … -> Summary. Khi đang ở màn
hình, mô phỏng không bước. Pause (Esc/P) đi qua nút `pause` của Test Contract nên dừng mọi timer, kể cả Shop.

Mô phỏng chạy 60 tick/s trong một luồng nền, dùng CÙNG lớp sim như headless (qua `runner.Session`).
Client chỉ ĐỌC snapshot và tự bỏ qua trường chưa có, nên luật do nhóm viết thêm trường nào cũng không vỡ.
Ngẫu nhiên vẫn đi qua `Streams` (seed); chỉ nhịp chạy theo đồng hồ thật, không đi vào luật.
"""

import argparse
import json
import os
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .contract import load_contract
from .errors import BadInput
from .inputs import LiveInputs
from .inventory import read_inventory
from .runner import Session
from .scenario import load_scenario

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
TICK_S = 1.0 / 60.0
MAX_BODY = 4096
MAX_BENCH_BODY = 4 * 1024 * 1024  # /bench gửi thời gian từng khung (Ticket-04 benchmark)
RECENT_EVENTS = 40
INTRO_S = 4.0


class LiveGame:
    """Một lượt chơi + luồng nền bước 60 tick/s. Mọi truy cập trạng thái đi qua khóa."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, inventory_out=None, days=5):
        self._args = (mode, tuning, scenario, seed, inventory, days if mode == "day" else 1)
        self.mode = mode
        self.tuning = tuning
        self.inventory_out = inventory_out
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self.bench_result = None
        self.first_get_ms = None
        self.shot_png = None
        self._reset()

    def _reset(self):
        self.session = Session(*self._args)
        self.inputs = LiveInputs()
        self.events = []
        self._saved = False
        self.error = None
        self.quit = False
        self.stats = {"days": [], "dishes": {}}
        self._screen(("menu" if self.mode == "day" else None))
        for row in self.session.initial_rows():
            self._observe(row)

    # --- màn hình + thống kê (chỉ cửa sổ chơi) -------------------------------------------
    def _screen(self, name):
        self.screen = name
        self.screen_t = time.monotonic()

    def _day_stats(self):
        return self.stats["days"][-1]

    def _observe(self, row):
        name, data = row["name"], row["data"]
        sim = self.session.sim
        if name == "day_start":
            self.stats["days"].append({"day": row["day"], "served": 0, "left": 0, "shift_money": 0, "tips": 0,
                                       "rep_start": sim.reputation, "rep_end": sim.reputation, "inventory": {}})
            if self.screen != "menu":
                self._screen("day_intro")
        elif not self.stats["days"]:
            return
        elif name == "gather_end":
            self._day_stats()["inventory"] = data["inventory"]["items"]
        elif name == "phase_start" and row["phase"] == "quan":
            self._screen("evening_intro")
        elif name == "phase_start" and row["phase"] == "shop":
            self._day_stats()["rep_end"] = sim.reputation
            self._screen("day_result")
        elif name == "served":
            self._day_stats()["served"] += 1
            self.stats["dishes"][data["dish_id"]] = self.stats["dishes"].get(data["dish_id"], 0) + 1
        elif name == "customer_left" and data.get("reason") == "patience":
            self._day_stats()["left"] += 1
        elif name == "paid":
            self._day_stats()["shift_money"] += data["amount"]
            self._day_stats()["tips"] += data["tip"]

    # --- luồng nền ----------------------------------------------------------------
    def start(self):
        self._thread = threading.Thread(target=self._loop, name="chonoi-sim", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self):
        nxt = time.perf_counter()
        while not self._stop.is_set():
            nxt += TICK_S
            with self._lock:
                try:
                    self._tick_once()
                except Exception:  # luật của nhóm lỗi: báo ra terminal + client, dừng bước (restart để chơi lại)
                    self.error = traceback.format_exc()
                    sys.stderr.write(self.error)
                    self.session.sim.done = True
                    self.session.sim.reason = "error"
            delay = nxt - time.perf_counter()
            if delay > 0:
                self._stop.wait(delay)
            elif delay < -0.25:  # chạy chậm quá thì bỏ bù, tránh chạy dồn
                nxt = time.perf_counter()

    def _tick_once(self):
        s = self.session
        if self.screen == "day_intro" and time.monotonic() - self.screen_t >= INTRO_S:
            self._screen(None)
        if self.screen is not None:
            return
        if s.done:
            if self.mode == "day":
                self._screen("summary")
            return
        for row in s.step(self.inputs.advance()):
            self.events.append(row)
            self._observe(row)
        del self.events[:-RECENT_EVENTS]
        if s.done and not self._saved:
            self._saved = True
            if self.inventory_out:
                try:
                    s.write_inventory_if_done(self.inventory_out)
                except OSError as e:
                    sys.stderr.write(f"lỗi ghi kho: {e}\n")

    # --- API cho handler -----------------------------------------------------------
    def state_json(self) -> bytes:
        with self._lock:
            snap = self.session.snapshot()
            phase = snap.get("phase", self.mode)
            snap["meta"] = dict(self.tuning.get(phase, {}), menu=self.tuning["menu"], shop=self.tuning["shop"])
            snap["ui"] = {"screen": self.screen, "elapsed": round(time.monotonic() - self.screen_t, 2),
                          "stats": self.stats}
            snap["events"] = list(self.events)
            snap["finished"] = self.session.done
            snap["reason"] = self.session.sim.reason if self.session.done else None
            snap["error"] = self.error
            return json.dumps(snap, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def set_input(self, body: dict):
        move = body.get("move")
        if move is not None:
            ok = (isinstance(move, list) and len(move) == 2 and
                  all(isinstance(c, (int, float)) and not isinstance(c, bool) and abs(c) <= 1 for c in move))
            if not ok:
                raise ValueError("move phải là [a, b] trong [-1, 1]")
        buttons = {}
        for b in ("interact", "catch", "pause", "shop_done"):
            if b in body:
                if not isinstance(body[b], bool):
                    raise ValueError(f"{b} phải là boolean")
                buttons[b] = body[b]
        buy = body.get("buy")
        if buy is not None and not (isinstance(buy, str) and buy):
            raise ValueError("buy phải là chuỗi khác rỗng")
        with self._lock:
            self.inputs.set(move, **buttons)
            if buy:
                self.inputs.queue_buy(buy)

    def advance_screen(self):
        with self._lock:
            if self.screen == "summary":
                return
            self._screen("day_intro" if self.screen == "menu" else None)  # Chơi -> DayIntro Ngày 1

    def request_quit(self):
        with self._lock:
            self.quit = True

    def restart(self):
        with self._lock:
            self._reset()


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    game: LiveGame = None  # gán trên lớp con trong make_server

    def log_message(self, fmt, *args):  # yên lặng
        pass

    def _send(self, code, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if self.game.first_get_ms is None and path in ("/", "/index.html"):
            self.game.first_get_ms = time.time() * 1000  # đo khởi động trình duyệt (benchmark)
        if path == "/state":
            self._send(200, self.game.state_json())
        elif path in ("/", "/index.html"):
            try:
                with open(os.path.join(WEB_DIR, "index.html"), "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except OSError:
                self._send(404, b'{"error":"thieu index.html"}')
        else:
            self._send(404, b'{"error":"khong co"}')

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n < 0 or n > (MAX_BENCH_BODY if path in ("/bench", "/shot") else MAX_BODY):
            self._send(400, b'{"error":"body sai"}')
            return
        raw = self.rfile.read(n) if n else b""
        try:
            if path == "/input":
                body = json.loads(raw.decode("utf-8") or "{}")
                if not isinstance(body, dict):
                    raise ValueError("body phải là object")
                self.game.set_input(body)
            elif path == "/restart":
                self.game.restart()
            elif path == "/continue":
                self.game.advance_screen()
            elif path == "/quit":
                self.game.request_quit()
            elif path == "/bench":
                body = json.loads(raw.decode("utf-8") or "{}")
                d = body.get("deltas_ms") if isinstance(body, dict) else None
                if not (isinstance(d, list) and all(isinstance(x, (int, float)) and x > 0 for x in d)
                        and isinstance(body.get("load_ms"), (int, float))):
                    raise ValueError("bench cần deltas_ms (số dương) và load_ms")
                self.game.bench_result = body
            elif path == "/shot":
                body = json.loads(raw.decode("utf-8") or "{}")
                png = body.get("png") if isinstance(body, dict) else None
                if not (isinstance(png, str) and png.startswith("data:image/png;base64,")):
                    raise ValueError("shot cần png dạng data URL")
                self.game.shot_png = png
            else:
                self._send(404, b'{"error":"khong co"}')
                return
        except (ValueError, UnicodeDecodeError) as e:
            self._send(400, json.dumps({"error": str(e)}).encode("utf-8"))
            return
        self._send(200, b'{"ok":true}')


class LiveServer:
    """Máy chủ + mô phỏng. port=0 -> cổng ngẫu nhiên (đọc `.port`)."""

    def __init__(self, game: LiveGame, host="127.0.0.1", port=8000):
        handler = type("Handler", (_Handler,), {"game": game})
        self.game = game
        self.httpd = ThreadingHTTPServer((host, port), handler)
        self.httpd.daemon_threads = True
        self.host = host
        self.port = self.httpd.server_address[1]
        self._thread = None

    @property
    def url(self):
        return f"http://{self.host}:{self.port}/"

    def start(self):
        self.game.start()
        self._thread = threading.Thread(target=self.httpd.serve_forever, name="chonoi-http", daemon=True)
        self._thread.start()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        if self._thread:
            self._thread.join(timeout=2)
        self.game.stop()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.live", description="Chơi trực tiếp trên trình duyệt (starter).")
    p.add_argument("--mode", default="day", choices=["gather", "quan", "day"])
    p.add_argument("--days", type=int, default=5, help="chỉ với day: số Ngày (1..5)")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--port", type=int, default=8000, help="0 = cổng ngẫu nhiên")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--scenario")
    p.add_argument("--inventory", help="chỉ với quan: nạp kho từ file")
    p.add_argument("--inventory-out", dest="inventory_out", help="chỉ với gather: ghi kho khi kết thúc buổi")
    a = p.parse_args(argv)
    try:
        if a.inventory and a.mode != "quan":
            raise BadInput("--inventory chỉ dùng với quan")
        if a.inventory_out and a.mode != "gather":
            raise BadInput("--inventory-out chỉ dùng với gather")
        if not (1 <= a.days <= 5):
            raise BadInput("--days phải từ 1 đến 5")
        tuning = load_contract()["tuning"]
        scenario = load_scenario(a.scenario, a.mode, tuning)
        inventory = read_inventory(a.inventory) if a.inventory else None
        if inventory is not None and "stock" in scenario:
            raise BadInput("vừa có quan.stock vừa có --inventory")
        game = LiveGame(a.mode, tuning, scenario, a.seed, inventory, a.inventory_out, days=a.days)
        server = LiveServer(game, a.host, a.port)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"không mở được cổng {a.port}: {e}\n")
        return 1
    server.start()
    print(f"Mở trình duyệt tại {server.url}  (chế độ {a.mode}, seed {a.seed}). Ctrl+C để dừng.", flush=True)
    try:
        while not game.quit:
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
