"""Soak headless (Ticket-04 mục 2), nhóm Haind:

    python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Chạy N Ngày trong MỘT tiến trình headless bằng bot tất định (chỉ đọc trạng thái mô phỏng, không dùng đồng hồ thực
hay random). Mỗi Ngày đi qua gather -> quan -> shop; kế hoạch D1–D5 lặp ở Ngày 6–10; tiền, tổng thu, uy tín, cấp nâng
cấp, số Ngày và id cá thể đi tiếp xuyên suốt (cùng `DaySim` với `--mode day`).

soak.json: {days, days_completed, crashes, results[{day, earned, reputation, score}] lúc Shop đóng, duration_s}.
`duration_s` là thời gian thực (bỏ qua khi so tất định). Mã thoát: 0 khi đạt, 1 khi có crash / chưa đủ Ngày, 2 khi
tham số sai. Soak không ghi bảng xếp hạng.

Bot (không phải luật, chỉ là người chơi tự động):
  sáng — bơi trên mặt nước tới nút hái sẵn sàng gần nhất (ưu tiên loại có trong kế hoạch), hái, chờ mọc lại; đủ giỏ
         hoặc sắp hết giờ thì về bến cập bến;
  tối  — tay có món -> tới bàn của đơn đó phục vụ; bếp có món chín -> lấy; còn đơn reserved và bếp rảnh -> nấu;
  Shop — mua Bình oxy, rồi Áo phao nếu đủ tiền, rồi đóng Shop.
"""

import argparse
import json
import math
import sys
import time
import traceback

from .contract import load_contract
from .errors import BadInput
from .inputs import InputState
from .runner import Session

DAY_TICKS = 22_200


class Bot:
    def __init__(self, tuning):
        self.t = tuning
        self._held = False  # interact đang giữ (thả một tick để tạo cạnh lên mới)
        self._done_held = False

    def _press(self, want):
        edge = want and not self._held
        self._held = edge
        return edge

    @staticmethod
    def _toward(pos, target, dead=0.05):
        dx, dy = target[0] - pos[0], target[1] - pos[1]
        d = math.hypot(dx, dy)
        if d <= dead:
            return (0.0, 0.0), d
        k = min(1.0, d / 0.6) / d  # chậm lại khi gần đích để không vượt quá
        return (dx * k, dy * k), d

    def next(self, sim) -> InputState:
        sub = sim.sub
        move, want, buy, done = (0.0, 0.0), False, None, False
        if sub.phase == "gather":
            move, want = self._gather(sim, sub)
        elif sub.phase == "quan":
            move, want = self._quan(sub)
        else:
            buy, done = self._shop(sub)
        edges = set()
        if self._press(want):
            edges.add("interact")
        if done and not self._done_held:
            edges.add("shop_done")
        self._done_held = done
        held = {"interact": self._held, "catch": False, "pause": False, "shop_done": done, "attack": False,
                "photo": False}
        return InputState(move, held, edges, buy)

    def _gather(self, sim, g):
        t = g.t
        x = g.pos[0]
        dock = t["dock_pos"]
        back = abs(x - dock[0]) / t["swim_speed"] * 60 + 180  # tick cần để về bến + dự phòng
        if g.time_left_ticks <= back or len(g.hold) >= t["hold_capacity"]:
            mv, d = self._toward(g.pos, dock)
            return mv, d <= t["dock_radius"] - 0.5
        need = set(sim.plan_today()["ingredients"])
        ready = [n for n in g.nodes if n["regrow_ticks"] == 0]
        pool = [n for n in ready if n["kind"] in need] or ready
        if pool:
            node = min(pool, key=lambda n: (abs(n["pos"][0] - x), n["id"]))
            mv, d = self._toward(g.pos, node["pos"])
            return mv, d <= t["interact_radius"] - 0.5
        soon = min(g.nodes, key=lambda n: (n["regrow_ticks"], abs(n["pos"][0] - x)))
        return self._toward(g.pos, soon["pos"])[0], False

    def _quan(self, q):
        r = q.t["interact_radius"]
        if q.hand is not None:
            c = next((c for c in q.customers if c["id"] == q.hand["order_id"]), None)
            if c is not None:
                tb = next(tb for tb in q.tables if tb["id"] == c["table_id"])
                mv, d = self._toward(q.pos, tb["pos"])
                return mv, d <= r / 2
        ready = [s for s in q.stoves if s["state"] == "ready"]
        idle = [s for s in q.stoves if s["state"] == "idle"]
        orders = any(c["state"] == "waiting" and c["order_status"] == "reserved" for c in q.customers)
        target = None
        if q.hand is None and ready:
            target = min(ready, key=lambda s: math.dist(q.pos, s["pos"]))
        elif orders and idle:
            target = min(idle, key=lambda s: math.dist(q.pos, s["pos"]))
        if target is None:
            return self._toward(q.pos, q.stoves[0]["pos"])[0], False
        mv, d = self._toward(q.pos, target["pos"])
        return mv, d <= r / 2

    def _shop(self, s):
        k = s.phase_tick  # số bước Shop đã chạy
        ups = s.shop["upgrades"]
        if k < 2:
            kind = ("oxygen", "hp")[k]
            lv = s.upgrades.get(kind, 0)
            if lv < len(ups[kind]) and s.money >= ups[kind][lv]["price"]:
                return kind, False
            return None, False
        return None, True


def run_soak(seed, days, tuning):
    t0 = time.perf_counter()
    results, crashes, done = [], 0, 0
    try:
        sess = Session("day", tuning, {}, seed, days=days)
        bot = Bot(tuning)
        limit = days * DAY_TICKS + 10
        while not sess.done and sess.tick < limit:
            rows = sess.step(bot.next(sess.sim))
            for row in rows:
                if row["name"] == "shop_end":
                    results.append({"day": row["day"], "earned": sess.sim.earned,
                                    "reputation": round(float(sess.sim.reputation), 6), "score": sess._score()})
        done = sess.sim.days_completed
    except Exception:  # crash = ngoại lệ trong mô phỏng; ghi stderr, vẫn xuất soak.json
        crashes += 1
        sys.stderr.write(traceback.format_exc())
    return {"days": days, "days_completed": done, "crashes": crashes, "results": results,
            "duration_s": round(time.perf_counter() - t0, 3)}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.soak")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--days", type=int, required=True)
    p.add_argument("--out", required=True)
    try:
        a = p.parse_args(argv)
    except SystemExit:
        return 2
    if a.days < 1:
        sys.stderr.write("--days phải >= 1\n")
        return 2
    try:
        tuning = load_contract()["tuning"]
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    res = run_soak(a.seed, a.days, tuning)
    try:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    print(json.dumps({k: res[k] for k in ("days", "days_completed", "crashes", "duration_s")}, ensure_ascii=False))
    return 0 if res["crashes"] == 0 and res["days_completed"] == res["days"] else 1


if __name__ == "__main__":
    sys.exit(main())
