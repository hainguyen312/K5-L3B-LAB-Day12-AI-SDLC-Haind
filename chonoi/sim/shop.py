"""Shop cuối Ngày (Ticket-02 mục 2 "Shop và nâng cấp", mục 4.5 "Shop"), nhóm Haind.

Một bước: đồng hồ (phase_tick +1, time_left -1) -> xử lý tối đa MỘT lệnh `buy` của frame -> cạnh `shop_done`
-> shop_end(done); không thì hết max_ticks -> shop_end(time).
Mua cấp kế tiếp: đã tối đa -> buy_failed(max_level); thiếu tiền -> buy_failed(funds); đủ đúng giá vẫn mua được.
Trừ vào money, giữ earned/điểm. Cấp vừa mua ghi vào `upgrades` ngay, chỉ áp dụng (active) từ Ngày kế.
Lệnh không hỗ trợ (kể cả weapon/net/buy:/sell: của mở rộng nhóm chưa bật) -> buy_failed(unknown).
"""

SUPPORTED = ("oxygen", "hp")


class ShopSim:
    mode = "day"
    phase = "shop"

    def __init__(self, tuning, money, earned, reputation, upgrades, stock):
        self.shop = tuning["shop"]
        self.phase_tick = 0
        self.time_left_ticks = int(self.shop["max_ticks"])
        self.money, self.earned, self.reputation = money, earned, reputation
        self.upgrades = dict(upgrades)
        self.stock = {k: v for k, v in sorted(stock.items()) if v > 0}  # kho dư từ ca, bỏ sau Shop
        self.done = False
        self.reason = None

    def snapshot(self) -> dict:
        return {"stock": dict(self.stock)}

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        if inp.buy is not None:
            events.append(self._buy(inp.buy))
        if inp.pressed("shop_done"):
            self._close("done", events)
        elif self.time_left_ticks <= 0:
            self._close("time", events)
        return events

    def _buy(self, cmd):
        if cmd not in SUPPORTED:
            return ("buy_failed", {"action": cmd, "reason": "unknown"})
        levels = self.shop["upgrades"][cmd]
        cur = self.upgrades.get(cmd, 0)
        if cur >= len(levels):
            return ("buy_failed", {"action": cmd, "reason": "max_level"})  # giả định: clarify #20
        price = int(levels[cur]["price"])
        if self.money < price:
            return ("buy_failed", {"action": cmd, "reason": "funds"})
        self.money -= price
        self.upgrades[cmd] = cur + 1
        return ("bought", {"upgrade": cmd, "level": cur + 1, "price": price, "money": self.money})

    def _close(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("shop_end", {"reason": reason}))
