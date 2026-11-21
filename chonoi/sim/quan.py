"""Buổi tối — Mở Quán (nhóm Haind), theo PRD-0 mục D/E/F (Quán). Nhìn từ trên xuống, vị trí `[x, z]`.

Thứ tự MỘT bước:
  1. đồng hồ (phase_tick +1), timer ca, nấu, ăn, kiên nhẫn (khách waiting); ready_ticks +1 chỉ cho món đã ready
     ở đầu bước;
  2. bếp theo id: nấu xong -> ready (ready_ticks = 0), `dish_ready`; burn_s = null;
  3. đi lại, rồi tối đa MỘT interact chọn theo (khoảng cách, bếp trước bàn, id); đối tượng không tương tác được
     -> bỏ lượt:
       bếp idle   -> lấy đơn reserved cũ nhất (order_tick, rồi id bàn), tiêu nguyên liệu giữ, chốt giá, `cook_started`
       bếp ready  -> giao món cho tay trống, bếp về idle, `dish_picked`
       bàn        -> tay cầm đúng order_id -> khách ăn (timer đầy), chốt boa, `served`
  4. theo id bàn: khách ăn xong trả tiền (`paid` finished_eating) rồi rời; còn giờ: khách waiting kiên nhẫn 0 rời
     (`customer_left` patience, uy tín + left_reputation_delta); hết ca: khách đang ăn trả ngay (`paid` closing),
     khách chờ rời (`customer_left` closing, không trừ uy tín), rồi `quan_end`;
     khách rời -> nhả giữ chỗ, bỏ món của đơn (bếp/tay); boa dương -> uy tín + tip_reputation khi thu tiền;
  5. còn giờ: lượt khách ở first_customer_tick rồi mỗi customer_interval_s*60 (theo phase_tick); hết bàn -> bỏ lượt;
     bàn trống id nhỏ nhất; chọn đều theo seed trong các món đủ nguyên liệu khả dụng (tồn - giữ chỗ) -> giữ chỗ,
     `customer_arrived`; không món -> `no_dish`.
Chế độ day (Ticket-02 mục 2, 4.5): tiền/earned/uy tín nối từ Ngày trước; khách chọn trong các món CỦA KẾ HOẠCH
Ngày (lọc theo id món trước khi lọc nguyên liệu khả dụng); quán chạy riêng dùng cả 6 món.
Số liệu chỉ đọc từ game.contract.json; ngẫu nhiên chỉ qua luồng RNG `customer_dish`.
"""

import math
from fractions import Fraction

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from ..inventory import KINDS_P1
from .ramp import ramp_velocity

TICK = 60.0
CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left", "eat_ticks_left",
                 "order_status", "reserved", "base_price", "tip"}
STOVE_KEYS = {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}
ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")


def _ticks(seconds) -> int:
    return int(round(seconds * TICK))


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, ctx=None):
        """`ctx` (chế độ day): money, earned, reputation, dishes (id món của kế hoạch Ngày)."""
        ctx = ctx or {}
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        self.patience_max = _ticks(t["patience_s"])
        self.eat_ticks = max(1, _ticks(t["eat_s"]))
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2); stock gồm cả phần giữ chỗ
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.duration_ticks = _ticks(t["duration_s"])
        self.time_left_ticks = scenario.get("time_left_ticks", self.duration_ticks)
        self.phase_tick = 0
        self.rep_min, self.rep_max = t["reputation_min"], t["reputation_max"]
        self.reputation = scenario.get("reputation", ctx.get("reputation", t["reputation_initial"]))
        self.dishes = sorted(ctx["dishes"]) if ctx.get("dishes") else sorted(self.menu)
        if not (isinstance(self.reputation, (int, float)) and not isinstance(self.reputation, bool)
                and math.isfinite(self.reputation) and self.rep_min <= self.reputation <= self.rep_max):
            raise BadInput("reputation phải là số trong [reputation_min, reputation_max]")
        self.random_customers = scenario.get("random_customers", True)
        if not isinstance(self.random_customers, bool):
            raise BadInput("random_customers phải là boolean")
        self.tables = self._merge(t["tables"], scenario.get("tables", []), {"id", "pos"})
        self.stoves = [self._load_stove(s) for s in self._merge(t["stoves"], scenario.get("stoves", []), STOVE_KEYS)]
        self.hand = self._load_payload("hand", scenario.get("hand"))
        self.customers = self._load_customers(scenario.get("customers", []))
        for c in self.customers:
            if c["dish_id"] not in self.dishes:
                raise BadInput(f"customers.{c['id']}: món {c['dish_id']} không thuộc kế hoạch Ngày")
        self._validate_links()
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = ctx.get("money", 0)
        self.earned = ctx.get("earned", 0)
        self.shift_earned = 0
        self.done = False
        self.reason = None

    # --- dựng / kiểm scenario mức luật (mục D) ------------------------------------------
    def _merge(self, defaults, updates, allowed):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            extra = set(u) - allowed
            if extra:
                raise BadInput(f"{u['id']}: trường lạ {sorted(extra)}")
            if "pos" in u:
                self._check_pos(u["id"], u["pos"])
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _check_pos(self, name, pos):
        b = self.t["bounds"]
        ok = isinstance(pos, list) and len(pos) == 2 and all(
            isinstance(c, (int, float)) and not isinstance(c, bool) for c in pos)
        if not ok or not all(b[a][0] <= c <= b[a][1] for c, a in zip(pos, ("x", "z"))):
            raise BadInput(f"{name}.pos ngoài miền quán")

    def _load_payload(self, where, d):
        """Payload món {order_id, dish_id, base_price} hoặc None."""
        if d is None:
            return None
        if not isinstance(d, dict) or set(d) != {"order_id", "dish_id", "base_price"}:
            raise BadInput(f"{where}: payload món phải là {{order_id, dish_id, base_price}} hoặc null")
        if not isinstance(d["order_id"], str) or d["dish_id"] not in self.menu:
            raise BadInput(f"{where}: order_id/dish_id không hợp lệ")
        if not _is_int(d["base_price"]) or d["base_price"] <= 0:
            raise BadInput(f"{where}: base_price phải là số nguyên dương")
        return dict(d)

    def _load_stove(self, s):
        out = {"id": s["id"], "pos": s["pos"], "state": s.get("state", "idle"),
               "dish": self._load_payload(f"stoves.{s['id']}.dish", s.get("dish")),
               "cook_ticks_left": s.get("cook_ticks_left", 0), "ready_ticks": s.get("ready_ticks", 0)}
        for k in ("cook_ticks_left", "ready_ticks"):
            if not _is_int(out[k]) or out[k] < 0:
                raise BadInput(f"stoves.{s['id']}.{k} phải là số nguyên không âm")
        st = out["state"]
        if st not in ("idle", "cooking", "ready"):
            raise BadInput(f"stoves.{s['id']}: state phải là idle/cooking/ready")
        if st == "idle" and (out["dish"] is not None or out["cook_ticks_left"] or out["ready_ticks"]):
            raise BadInput(f"stoves.{s['id']}: bếp idle không có món/timer")
        if st != "idle" and out["dish"] is None:
            raise BadInput(f"stoves.{s['id']}: bếp {st} phải có món")
        if st == "cooking" and (out["cook_ticks_left"] < 1 or out["ready_ticks"]):
            raise BadInput(f"stoves.{s['id']}: bếp cooking cần cook_ticks_left > 0")
        if st == "ready" and out["cook_ticks_left"]:
            raise BadInput(f"stoves.{s['id']}: bếp ready không còn cook_ticks_left")
        return out

    def _load_customers(self, raw):
        out = []
        for c in raw:
            cid = c["id"]
            extra = set(c) - CUSTOMER_KEYS
            if extra:
                raise BadInput(f"customers.{cid}: trường lạ {sorted(extra)}")
            dish = c.get("dish_id")
            if dish not in self.menu:
                raise BadInput(f"customers.{cid}: dish_id phải là món trong menu")
            state = c.get("state", "waiting")
            status = c.get("order_status", "reserved")
            if state not in ("waiting", "eating") or status not in ORDER_STATUSES:
                raise BadInput(f"customers.{cid}: state/order_status không hợp lệ")
            cu = {"id": cid, "table_id": c["table_id"], "dish_id": dish, "order_tick": c.get("order_tick", 0),
                  "state": state, "order_status": status,
                  "patience_ticks_left": c.get("patience_ticks_left", self.patience_max),
                  "eat_ticks_left": c.get("eat_ticks_left", 0),
                  "reserved": c.get("reserved"), "base_price": c.get("base_price"), "tip": c.get("tip")}
            if not _is_int(cu["order_tick"]) or cu["order_tick"] < 0:
                raise BadInput(f"customers.{cid}: order_tick phải là số nguyên không âm")
            if not _is_int(cu["patience_ticks_left"]) or not (0 <= cu["patience_ticks_left"] <= self.patience_max):
                raise BadInput(f"customers.{cid}: patience_ticks_left phải trong [0, {self.patience_max}]")
            if not _is_int(cu["eat_ticks_left"]) or not (0 <= cu["eat_ticks_left"] <= self.eat_ticks):
                raise BadInput(f"customers.{cid}: eat_ticks_left phải trong [0, {self.eat_ticks}]")
            if cu["reserved"] is not None:
                r = cu["reserved"]
                if not isinstance(r, dict) or any(k not in KINDS_P1 or not _is_int(v) or v < 0 for k, v in r.items()):
                    raise BadInput(f"customers.{cid}: reserved phải là map kind -> số nguyên không âm")
                cu["reserved"] = {k: v for k, v in sorted(r.items()) if v > 0}
            for k in ("base_price", "tip"):
                if cu[k] is not None and (not _is_int(cu[k]) or cu[k] < 0):
                    raise BadInput(f"customers.{cid}: {k} phải là số nguyên không âm")
            recipe = dict(sorted(self.menu[dish]["recipe"].items()))
            if state == "eating":
                if status != "served" or cu["eat_ticks_left"] < 1 or cu["base_price"] is None or cu["tip"] is None:
                    raise BadInput(f"customers.{cid}: khách eating phải served, có timer ăn dương, base_price, tip")
                if cu["reserved"]:
                    raise BadInput(f"customers.{cid}: khách eating không giữ chỗ")
                cu["reserved"] = {}
            else:
                if status == "served" or cu["eat_ticks_left"] or cu["tip"] is not None:
                    raise BadInput(f"customers.{cid}: khách waiting không thể served/có timer ăn/tip")
                if status == "reserved":
                    if cu["reserved"] is None:
                        cu["reserved"] = None  # cấp theo công thức ở bước sau (theo order_tick rồi id bàn)
                    elif cu["reserved"] != recipe:
                        raise BadInput(f"customers.{cid}: giữ khác công thức")
                elif cu["reserved"]:
                    raise BadInput(f"customers.{cid}: đơn {status} có phần giữ rỗng")
                else:
                    cu["reserved"] = {}
            out.append(cu)
        # cấp giữ chỗ còn thiếu theo order_tick rồi id bàn
        for cu in sorted(out, key=lambda c: (c["order_tick"], id_key(c["table_id"]))):
            if cu["reserved"] is None:
                cu["reserved"] = dict(sorted(self.menu[cu["dish_id"]]["recipe"].items()))
        return sort_by_id(out)

    def _validate_links(self):
        need = self._reserved_total()
        for k, v in need.items():
            if self.stock.get(k, 0) < v:
                raise BadInput(f"giữ chỗ {k}={v} quá tồn ({self.stock.get(k, 0)})")
        by_id = {c["id"]: c for c in self.customers}
        holders = [(f"stoves.{s['id']}", s["dish"]) for s in self.stoves if s["dish"] is not None]
        if self.hand is not None:
            holders.append(("hand", self.hand))
        seen = set()
        for where, d in holders:
            c = by_id.get(d["order_id"])
            if c is None:
                raise BadInput(f"{where}: order_id {d['order_id']} không có khách (liên kết thiếu)")
            if d["dish_id"] != c["dish_id"]:
                raise BadInput(f"{where}: món không khớp đơn {c['id']}")
            if c["order_status"] != "assigned":
                raise BadInput(f"{where}: đơn {c['id']} không ở trạng thái assigned")
            if d["order_id"] in seen:
                raise BadInput(f"bếp và tay giữ cùng đơn {d['order_id']}")
            seen.add(d["order_id"])
        for c in self.customers:
            if c["order_status"] == "assigned" and c["id"] not in seen:
                raise BadInput(f"customers.{c['id']}: đơn assigned phải có đúng một món ở bếp hoặc tay")

    # --- giao diện cho runner -----------------------------------------------------------
    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos, "vel": self.vel},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s[k] for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": [{k: c[k] for k in sorted(CUSTOMER_KEYS)} for c in sort_by_id(self.customers)],
        }

    def step(self, inp):
        events = []
        # 1. đồng hồ và timer
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        ready_at_start = [s for s in self.stoves if s["state"] == "ready"]
        for s in self.stoves:
            if s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
        for s in ready_at_start:
            s["ready_ticks"] += 1
        for c in self.customers:
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
            else:
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
        # 2. bếp theo id
        for s in self.stoves:
            if s["state"] == "cooking" and s["cook_ticks_left"] == 0:
                s["state"], s["ready_ticks"] = "ready", 0
                events.append(("dish_ready", self._dish_ev(s)))
        # 3. đi lại + tối đa một interact
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        # 4. khách rời / trả tiền theo id bàn; hết ca dọn quán
        closing = self.time_left_ticks <= 0
        for c in sorted(self.customers, key=lambda c: id_key(c["table_id"])):
            if c["state"] == "eating":
                if c["eat_ticks_left"] == 0:  # giả định: clarify #14 — ăn xong đúng tick đóng ca vẫn finished_eating
                    self._pay(c, "finished_eating", events)
                elif closing:
                    self._pay(c, "closing", events)
            elif closing:
                self._leave(c, "closing", events)
            elif c["patience_ticks_left"] == 0:
                self._leave(c, "patience", events)
        if closing:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return events
        # 5. lượt khách mới
        if self._due_arrival():
            self._spawn(events)
        return events

    # --- luật ------------------------------------------------------------------------------
    def _reserved_total(self) -> dict:
        tot = {}
        for c in self.customers:
            for k, v in (c.get("reserved") or {}).items():
                tot[k] = tot.get(k, 0) + v
        return {k: tot[k] for k in sorted(tot) if tot[k] > 0}

    def _available(self) -> dict:
        res = self._reserved_total()
        return {k: self.stock.get(k, 0) - res.get(k, 0) for k in self.stock}

    def _rep(self, delta):
        self.reputation = round(min(self.rep_max, max(self.rep_min, self.reputation + delta)), 9)

    @staticmethod
    def _dish_ev(s):
        return {"stove_id": s["id"], "order_id": s["dish"]["order_id"], "dish_id": s["dish"]["dish_id"]}

    def _interact(self, events):
        r = self.t["interact_radius"]
        cands = []
        for order, coll in ((0, self.stoves), (1, self.tables)):
            for o in coll:
                d = math.dist(self.pos, o["pos"])
                if d <= r:
                    cands.append((d, order, id_key(o["id"]), o))
        if not cands:
            return
        _, order, _, obj = min(cands, key=lambda x: x[:3])
        if order == 0:
            self._use_stove(obj, events)
        else:
            self._use_table(obj, events)

    def _use_stove(self, s, events):
        if s["state"] == "ready":
            if self.hand is not None:
                return
            ev = self._dish_ev(s)
            self.hand, s["state"], s["dish"], s["ready_ticks"] = s["dish"], "idle", None, 0
            events.append(("dish_picked", ev))
            return
        if s["state"] != "idle":
            return
        # giả định: clarify #13 — bắt đầu nấu không đòi tay trống
        orders = [c for c in self.customers if c["state"] == "waiting" and c["order_status"] == "reserved"]
        if not orders:
            return
        c = min(orders, key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        items = sorted(k for k, v in c["reserved"].items() for _ in range(v))
        for k, v in c["reserved"].items():
            self.stock[k] -= v
        c["reserved"], c["order_status"] = {}, "assigned"
        price = int(self.menu[c["dish_id"]]["price"])
        c["base_price"] = price
        s["state"], s["dish"] = "cooking", {"order_id": c["id"], "dish_id": c["dish_id"], "base_price": price}
        s["cook_ticks_left"], s["ready_ticks"] = max(1, _ticks(self.menu[c["dish_id"]]["cook_s"])), 0
        ev = self._dish_ev(s)
        ev.update(items=items, base_price=price)
        events.append(("cook_started", ev))

    def _use_table(self, tb, events):
        c = next((c for c in self.customers if c["table_id"] == tb["id"]), None)
        if c is None or c["state"] != "waiting" or self.hand is None or self.hand["order_id"] != c["id"]:
            return
        base = self.hand["base_price"]
        # so chính xác bằng phân số (tránh 0.29 * 100 = 28.999... của số thực)
        ratio = Fraction(c["patience_ticks_left"], self.patience_max)
        ok = ratio >= Fraction(str(self.t["tip_min_patience_ratio"]))
        tip = math.floor(base * Fraction(str(self.t["tip_rate"]))) if ok else 0
        self.hand = None
        c.update(state="eating", order_status="served", eat_ticks_left=self.eat_ticks, base_price=base, tip=tip)
        events.append(("served", {"order_id": c["id"], "table_id": tb["id"], "dish_id": c["dish_id"],
                                  "patience_ticks_left": c["patience_ticks_left"], "base_price": base, "tip": tip}))

    def _remove(self, c):
        self.customers = [x for x in self.customers if x["id"] != c["id"]]
        for s in self.stoves:  # bỏ món của đơn đang nấu / ready; nguyên liệu đã dùng không hoàn lại
            if s["dish"] is not None and s["dish"]["order_id"] == c["id"]:
                s["state"], s["dish"], s["cook_ticks_left"], s["ready_ticks"] = "idle", None, 0, 0
        if self.hand is not None and self.hand["order_id"] == c["id"]:
            self.hand = None

    def _pay(self, c, reason, events):
        amount = c["base_price"] + c["tip"]
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if c["tip"] > 0:
            self._rep(self.t["tip_reputation"])
        events.append(("paid", {"order_id": c["id"], "table_id": c["table_id"], "base_price": c["base_price"],
                                "tip": c["tip"], "amount": amount, "reason": reason}))
        self._remove(c)

    def _leave(self, c, reason, events):
        if reason == "patience":
            self._rep(self.t["left_reputation_delta"])
        self._remove(c)
        events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"], "reason": reason,
                                         "reputation": self.reputation}))

    def _due_arrival(self) -> bool:
        if not self.random_customers:
            return False
        first, every = int(self.t["first_customer_tick"]), max(1, _ticks(self.t["customer_interval_s"]))
        return self.phase_tick >= first and (self.phase_tick - first) % every == 0

    def _spawn(self, events):
        busy = {c["table_id"] for c in self.customers}
        free_tables = [tb for tb in self.tables if tb["id"] not in busy]
        if not free_tables:
            return
        avail = self._available()
        cookable = [d for d in self.dishes  # lọc theo kế hoạch trước, rồi nguyên liệu khả dụng
                    if all(avail.get(k, 0) >= v for k, v in self.menu[d]["recipe"].items())]
        if not cookable:
            events.append(("no_dish", {}))
            return
        dish = self.rng.get("customer_dish").choice(cookable)
        table = free_tables[0]
        cid = self.ids.new("C")  # giả định: clarify #16
        self.customers.append({
            "id": cid, "table_id": table["id"], "dish_id": dish, "order_tick": self.phase_tick, "state": "waiting",
            "order_status": "reserved", "patience_ticks_left": self.patience_max, "eat_ticks_left": 0,
            "reserved": dict(sorted(self.menu[dish]["recipe"].items())), "base_price": None, "tip": None})
        self.customers = sort_by_id(self.customers)
        events.append(("customer_arrived", {"order_id": cid, "table_id": table["id"], "dish_id": dish}))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
