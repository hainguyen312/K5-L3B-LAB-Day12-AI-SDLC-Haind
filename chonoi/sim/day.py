"""Chế độ `day` (Ticket-02 mục 2, 4.3–4.5), nhóm Haind: vòng gather -> quan -> shop qua 1..5 Ngày.

DayIntro / EveningIntro / DayResult / Summary là màn hình của cửa sổ chơi, KHÔNG tốn tick headless (clarify #25):
một Ngày không pause dài tối đa 10.800 + 10.800 + 600 = 22.200 tick.

Đổi pha (cùng tick với sự kiện kết thúc; pha mới chỉ chạy gameplay từ bước sau):
  dựng Ngày: day_start -> day_plan -> phase_start(gather)        [tick 0 với Ngày 1]
  gather_end (kể cả fainted, kho rỗng) -> dựng quán với kho bàn giao -> phase_start(quan)
  quan_end -> dựng Shop (kho dư) -> phase_start(shop)
  shop_end -> days_completed + 1 -> dựng Ngày kế (sao upgrades -> active_upgrades) hoặc kết thúc days_complete
Tiền, earned, uy tín, cấp nâng cấp giữ qua Ngày; oxy/Máu theo cấp đang áp dụng; giỏ làm mới; kho dư bỏ sau Shop.
v1.2: bàn giao cá thể (id, kind, fresh) trong cùng tick chuyển pha, không hao thêm; Shop không hao tươi.
Sự kiện trả về dạng (name, data, phase, day): sự kiện kết thúc mang pha cũ, phase_start mang pha mới.
"""

from .gather import GatherSim
from .quan import QuanSim
from .shop import ShopSim


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, days=1):
        self.tuning = tuning
        self.templates = {"gather": scenario.get("gather", {}), "quan": scenario.get("quan", {})}
        st = scenario.get("day") or {}
        q = tuning["quan"]
        self.money = st.get("money", 0)
        self.earned = st.get("earned", 0)
        self.reputation = st.get("reputation", q["reputation_initial"])
        self.upgrades = dict(st.get("upgrades", {}))
        self.plan = st.get("day_plan", tuning["day_plan"])
        self.active_upgrades = {}
        self.streams, self.ids = streams, ids
        self.days = days
        self.day = 0
        self.days_completed = 0
        self.done = False
        self.reason = None
        self.sub = None
        self.initial_events = self._start_day()

    # --- trạng thái chung (runner đọc) ---------------------------------------------------
    @property
    def phase(self):
        return self.sub.phase

    @property
    def phase_tick(self):
        return self.sub.phase_tick

    @property
    def time_left_ticks(self):
        return self.sub.time_left_ticks

    def _sync(self):
        self.money, self.earned, self.reputation = self.sub.money, self.sub.earned, self.sub.reputation

    def plan_today(self) -> dict:
        p = self.plan[(self.day - 1) % len(self.plan)]  # soak > 5 Ngày: D1–D5 lặp lại (Ticket-04 mục 2)
        return {"dishes": dict(p["dishes"]), "ingredients": dict(p["ingredients"])}

    def snapshot(self) -> dict:
        s = self.sub.snapshot()
        bought = self.sub.upgrades if self.sub.phase == "shop" else self.upgrades  # cấp vừa mua hiển thị ngay
        s.update(day=self.day, day_plan=self.plan_today(), upgrades=dict(sorted(bought.items())),
                 active_upgrades=dict(sorted(self.active_upgrades.items())))
        return s

    # --- dựng pha --------------------------------------------------------------------------
    def _level(self, kind, field, default):
        lv = self.active_upgrades.get(kind, 0)
        return self.tuning["shop"]["upgrades"][kind][lv - 1][field] if lv else default

    def _start_day(self):
        self.day += 1
        self.active_upgrades = dict(self.upgrades)  # chỉ khi dựng Ngày mới mới sao cấp đã mua
        g = self.tuning["gather"]
        ctx = {"money": self.money, "earned": self.earned, "reputation": self.reputation,
               "oxygen_max_s": self._level("oxygen", "oxygen_max_s", g["oxygen_max_s"]),
               "hp_max": self._level("hp", "hp_max", g["hp_max"])}
        tpl = self.templates["gather"]
        if self.day > 1 and tpl.get("hold"):
            # v1.2: Ngày đầu giữ nguyên id của mẫu; các Ngày kế cấp id mới theo thứ tự mảng, giữ kind/fresh ban đầu
            tpl = dict(tpl, hold=[{"id": self.ids.new("I"), "kind": it["kind"], "fresh": it["fresh"]} for it in tpl["hold"]])
        self.sub = GatherSim(self.tuning, tpl, self.streams, self.ids, day=self.day, ctx=ctx)
        return [("day_start", {}, "gather", self.day), ("day_plan", self.plan_today(), "gather", self.day),
                ("phase_start", {}, "gather", self.day)]

    def _open_quan(self, stock):
        self._sync()
        ctx = {"money": self.money, "earned": self.earned, "reputation": self.reputation,
               "dishes": list(self.plan_today()["dishes"])}
        self.sub = QuanSim(self.tuning, self.templates["quan"], self.streams, self.ids, inventory=stock, ctx=ctx)
        return [("phase_start", {}, "quan", self.day)]

    def _open_shop(self):
        self._sync()
        self.sub = ShopSim(self.tuning, self.money, self.earned, self.reputation, self.upgrades, self.sub.stock)
        return [("phase_start", {}, "shop", self.day)]

    # --- một bước --------------------------------------------------------------------------
    def step(self, inp):
        sub = self.sub
        out = [(n, d, sub.phase, self.day) for n, d in sub.step(inp)]
        if not sub.done:
            return out
        if sub.phase == "gather":
            out += self._open_quan(sub.inventory_items())
        elif sub.phase == "quan":
            out += self._open_shop()
        else:
            self._sync()
            self.upgrades = dict(sub.upgrades)
            self.days_completed += 1
            if self.day < self.days:
                out += self._start_day()
            else:
                self.done = True
                self.reason = "days_complete"
        return out
