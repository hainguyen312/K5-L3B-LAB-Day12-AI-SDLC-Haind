"""Benchmark có render (Ticket-04 mục 1), nhóm Haind:

    python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json [--warmup 3] [--browser PATH] [--visible]

Cảnh đo: buổi sáng lõi chuẩn (độ tươi, cá bơi, Cá Sấu Năm Chèo, hiệu ứng mặc định), Út Sen đứng yên ở bến, cửa sổ
1280×720. Lệnh dựng đúng server chơi thử (`chonoi.live`, cùng lớp sim với headless), mở Chrome/Chromium headless ở
`/?bench=1`; trang vẽ bằng canvas như khi chơi, đo thời gian từng khung bằng requestAnimationFrame (làm nóng `warmup` s,
đo `duration` s) rồi POST về `/bench`. Python tính:
  frames, measured_s  số khung và số giây thực trong khoảng đo sau làm nóng
  avg_fps             frames / measured_s
  p1_low_fps          max(1, ceil(0.01 × frames)) khung chậm nhất -> nghịch đảo thời gian trung bình (giây)
  load_ms             ms từ lúc lệnh khởi chạy tới khung hình đầu tiên của cảnh đo
Trình duyệt: biến môi trường CHONOI_BROWSER, `--browser`, hoặc tự tìm Chrome/Chromium; không có thì mở trình duyệt mặc
định (cửa sổ thật). Mã thoát: 0 ghi được bench.json, 1 quá thời gian / lỗi, 2 tham số sai.
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
import webbrowser

T_START_MS = time.time() * 1000  # mốc "khởi chạy" cho load_ms (lấy ngay khi nạp module)

from .contract import load_contract  # noqa: E402
from .errors import BadInput  # noqa: E402
from .live import LiveGame, LiveServer  # noqa: E402

MAC_PATHS = ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
             "/Applications/Chromium.app/Contents/MacOS/Chromium",
             "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge")
LINUX_NAMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge")


def find_browser(explicit=None):
    for cand in (explicit, os.environ.get("CHONOI_BROWSER")):
        if cand:
            return cand
    for p in MAC_PATHS:
        if os.path.exists(p):
            return p
    for n in LINUX_NAMES:
        p = shutil.which(n)
        if p:
            return p
    return None


def summarize(deltas_ms, load_ms):
    """Năm trường của bench.json từ thời gian từng khung (ms) trong khoảng đo."""
    frames = len(deltas_ms)
    if frames == 0:
        raise ValueError("không đo được khung hình nào")
    measured_s = sum(deltas_ms) / 1000.0
    n = max(1, math.ceil(0.01 * frames))
    slowest = sorted(deltas_ms, reverse=True)[:n]
    p1 = 1.0 / (sum(slowest) / n / 1000.0)
    return {"avg_fps": round(frames / measured_s, 2), "p1_low_fps": round(p1, 2), "frames": frames,
            "measured_s": round(measured_s, 3), "load_ms": int(round(load_ms))}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.bench")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--duration", type=float, required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--warmup", type=float, default=3.0)
    p.add_argument("--browser")
    p.add_argument("--visible", action="store_true", help="mở cửa sổ thật thay vì headless")
    try:
        a = p.parse_args(argv)
    except SystemExit:
        return 2
    if a.duration <= 0 or a.warmup < 0:
        sys.stderr.write("--duration phải > 0, --warmup >= 0\n")
        return 2
    try:
        tuning = load_contract()["tuning"]
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    game = LiveGame("gather", tuning, {}, a.seed)  # cảnh chuẩn, không input: đứng yên ở bến
    server = LiveServer(game, port=0)
    server.start()
    url = f"{server.url}?bench=1&duration={a.duration}&warmup={a.warmup}&t0={T_START_MS:.0f}"
    browser = find_browser(a.browser)
    proc, profile = None, tempfile.mkdtemp(prefix="chonoi-bench-")
    try:
        if browser:
            args = [browser, f"--user-data-dir={profile}", "--window-size=1280,720", "--no-first-run",
                    "--no-default-browser-check", "--disable-background-timer-throttling",
                    "--disable-renderer-backgrounding", "--disable-backgrounding-occluded-windows",
                    # tránh chờ Keychain / dịch vụ mạng nền khi khởi động (đo được ~60 s chờ trên macOS nếu thiếu)
                    "--use-mock-keychain", "--password-store=basic", "--disable-background-networking",
                    "--disable-component-update", "--disable-sync", "--no-service-autorun", "--disable-extensions",
                    "--no-proxy-server", "--proxy-bypass-list=*"]  # trang ở 127.0.0.1: không dò proxy (WPAD)
            if not a.visible:
                args.append("--headless=new")
            proc = subprocess.Popen(args + [url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            sys.stderr.write("không tìm thấy Chrome/Chromium — mở trình duyệt mặc định (cửa sổ 1280×720 nếu được)\n")
            webbrowser.open(url)
        deadline = time.time() + a.warmup + a.duration + 90
        while game.bench_result is None and time.time() < deadline:
            time.sleep(0.2)
        if game.bench_result is None:
            sys.stderr.write("quá thời gian chờ kết quả benchmark từ trình duyệt\n")
            return 1
        r = game.bench_result
        res = summarize(r["deltas_ms"], r["load_ms"])
        res["viewport"] = r.get("viewport")
        if game.first_get_ms is not None:  # chẩn đoán: thời gian trình duyệt khởi động tới lúc tải trang
            res["browser_start_ms"] = int(game.first_get_ms - T_START_MS)
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump({k: res[k] for k in ("avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms")}, f)
            f.write("\n")
        print(json.dumps(res, ensure_ascii=False))
        return 0
    except (OSError, ValueError) as e:
        sys.stderr.write(f"lỗi benchmark: {e}\n")
        return 1
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        server.stop()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
