"""Buổi sáng — Lặn & Hái (`gather`), nhóm Haind. Test Contract v1.1 (PRD-0 mục F + Ticket-02 mục 1.1, 1.2, 4.5).

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Thứ tự MỘT bước (Ticket-02 mục 4.5):
  1. đồng hồ (phase_tick +1), timer ca, hồi bắt, giảm bất tử, hồi nút (1 -> 0: node_regrown theo id)
  2. bơi + chặn mép (dive/surface); oxy theo d CUỐI bước; ngạt (xuyên bất tử, không rơi hàng); Máu 0 -> faint +
     gather_end(fainted), dừng
  3. Cá Sấu theo id (patrol / chase / recoil), rồi tối đa MỘT hit: con gần nhất trong hit_radius (hòa -> id), người
     chơi ở d >= ngưỡng loài, hết bất tử -> -1 Máu, bỏ floor(giỏ × loss_ratio) theo LIFO, bất tử, con đó recoil từ
     bước sau; Máu 0 -> faint(cause monster) + gather_end(fainted), dừng
  4. cạnh interact: bến trước (docked, dừng); ngoài bến, ở mặt nước hái nút ready gần nhất (hòa -> id)
  5. cạnh catch (dưới nước, hết hồi) theo vị trí cá TRƯỚC khi cá bơi: đàn gần nhất (hòa -> id); đủ chỗ cả đàn ->
     fish_caught + hồi chiêu; thiếu chỗ -> hold_full (giữ đàn, không hồi); không có đàn -> không gì cả
  6. timer ca về 0 -> gather_end(time), giữ giỏ, dừng
  7. còn giờ: cá bơi (đổi hướng theo seed ở bước bơi thứ 120, 240… trước khi di chuyển, phản xạ mép), rồi sinh
     tối đa một đàn ở phase_tick = 360·k (k >= 1)
Giỏ: mảng theo thứ tự nhặt (cuối mảng là mới nhất, LIFO), không vượt hold_capacity.
Số liệu chỉ đọc từ game.contract.json; ngẫu nhiên qua luồng `fish_spawn` (sinh) và `fish_turn` (đổi hướng).
"""

import math

from ..ids import id_key, sort_by_id
from ..inventory import hold_to_items
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


def _unit(dx, dy):
    n = math.hypot(dx, dy)
    return (dx / n, dy / n) if n > 0 else (1.0, 0.0)


def _reflect(v, lo, hi):
    """Phản xạ phần quãng đường vượt mép; trả (giá trị, có chạm mép không)."""
    if v > hi:
        return max(lo, 2 * hi - v), True
    if v < lo:
        return min(hi, 2 * lo - v), True
    return v, False


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day=1, ctx=None):
        """`ctx` (chế độ day): money, earned, reputation, oxygen_max_s, hp_max đang áp dụng."""
        ctx = ctx or {}
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        self.day = day
        self.phase_tick = 0
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(ctx.get("oxygen_max_s", t["oxygen_max_s"]) * TICK))
        self.hp_max = int(ctx.get("hp_max", t["hp_max"]))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", self.hp_max)
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.hold = list(scenario.get("hold", []))
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        for n in self.nodes:
            ids.reserve(n["id"])
        # cá: random_fish=false tắt cá mặc định + bơi + sinh (cá fixture đứng yên);
        # cờ bật mà khai fish thì thay đàn ban đầu, vẫn bơi/sinh
        self.fish_live = scenario.get("random_fish", True)
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": float(f.get("heading_deg", 0)), "age_ticks": f.get("age_ticks", 0)}
                     for f in scenario.get("fish", [])]
        for f in self.fish:
            ids.reserve(f["id"])
        if "fish" not in scenario and self.fish_live:
            for _ in range(int(t["fish_initial"])):
                self._spawn_fish()
        # Cá Sấu: fixture thay danh sách; không khai thì bố trí đúng Ngày (gather độc lập = Ngày 1)
        mo = t["monsters"]
        if "monsters" in scenario:
            src = scenario["monsters"]
        else:
            src = [dict(m, target_idx=1) for m in mo["spawns"] if m["from_day"] <= day]
        self.monsters = sort_by_id([{
            "id": m["id"], "kind": m["kind"], "pos": [float(c) for c in m["pos"]],
            "waypoints": [[float(c) for c in w] for w in m["waypoints"]], "target_idx": m.get("target_idx", 1),
            "state": m.get("state", "patrol"), "state_ticks_left": m.get("state_ticks_left", 0),
            "recoil_dir": list(m["recoil_dir"]) if m.get("recoil_dir") is not None else None} for m in src])
        for m in self.monsters:
            ids.reserve(m["id"])
        self.money = ctx.get("money", 0)
        self.earned = ctx.get("earned", 0)
        self.reputation = ctx.get("reputation", tuning["quan"]["reputation_initial"])
        self.done = False
        self.reason = None

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> dict:
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.hp_max, "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self.hold, "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"],
                      "age_ticks": f["age_ticks"]} for f in sort_by_id(self.fish)],
            "monsters": [{k: m[k] for k in ("id", "kind", "pos", "waypoints", "target_idx", "state",
                                            "state_ticks_left", "recoil_dir")} for m in self.monsters],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ, cooldown, bất tử, hồi nút
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        # 2. bơi, dive/surface, oxy, ngạt
        was_surface = self._at_surface()
        self._move(inp)
        now_surface = self._at_surface()
        if was_surface and not now_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif now_surface and not was_surface:
            events.append(("surface", {"pos": list(self.pos)}))
        if self._oxygen(events):
            return events
        # 3. Cá Sấu + tối đa một hit
        if self._monsters(events):
            return events
        # 4. interact: bến trước, rồi hái (chỉ ở mặt nước)
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if now_surface:
                self._harvest(events)
        # 5. bắt cá theo vị trí cá trước khi bơi
        if inp.pressed("catch") and self.catch_cd_ticks == 0 and not now_surface:
            self._catch(events)
        # 6. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events
        # 7. cá bơi rồi sinh theo lịch
        if self.fish_live:
            self._swim_fish()
            every = int(self.t["fish_spawn_ticks"])
            if self.phase_tick % every == 0 and len(self.fish) < int(self.t["fish_max"]):
                f = self._spawn_fish()
                if f is not None:
                    events.append(("fish_spawned", {"id": f["id"], "kind": f["kind"], "pos": list(f["pos"])}))
        return events

    # --- oxy / Máu ----------------------------------------------------------------
    def _oxygen(self, events) -> bool:
        """Cập nhật oxy/ngạt/Máu. Trả True nếu ngất (buổi kết thúc)."""
        t = self.t
        if self._at_surface():
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + int(t["oxygen_refill_per_tick"]))
            self.zero_oxy_ticks = 0  # mặt nước reset ngạt
            return False
        before = self.oxygen_ticks
        self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
        if before > 0 and self.oxygen_ticks == 0:
            events.append(("oxygen_empty", {"oxygen_ticks": 0}))
        if self.oxygen_ticks > 0:
            self.zero_oxy_ticks = 0
            return False
        self.zero_oxy_ticks += 1  # kể cả bước vừa chạm 0
        if self.zero_oxy_ticks < int(t["choke_interval_ticks"]):
            return False
        self.zero_oxy_ticks = 0
        self.hp = max(0, self.hp - 1)  # ngạt xuyên bất tử, không làm rơi hàng
        events.append(("choke", {"hp": self.hp}))
        if self.hp > 0:
            return False
        self._faint("choke", events)
        return True

    def _faint(self, cause, events):
        lost = list(reversed(self.hold))  # bỏ giỏ theo LIFO: nhặt sau bỏ trước
        self.hold = []
        events.append(("faint", {"cause": cause, "lost": lost, "hp": 0}))
        self._finish("fainted", events)

    # --- Cá Sấu ----------------------------------------------------------------------
    def _monsters(self, events) -> bool:
        mo = self.t["monsters"]
        species = mo["species"]
        px, pd = self.pos
        fresh = set()  # vừa hết recoil: xét phát hiện/chạm từ bước kế
        for m in self.monsters:
            sp = species[m["kind"]]
            if m["state"] == "recoil":
                step = sp["recoil_dist"] / sp["recoil_ticks"]
                self._monster_move(m, m["pos"][0] + m["recoil_dir"][0] * step, m["pos"][1] + m["recoil_dir"][1] * step)
                m["state_ticks_left"] -= 1
                if m["state_ticks_left"] <= 0:
                    m["state"], m["state_ticks_left"], m["recoil_dir"] = "patrol", 0, None
                    fresh.add(m["id"])
                continue
            thr = sp["depths"][0]
            dist = math.dist(self.pos, m["pos"])  # giả định: clarify #21 — xét bằng khoảng cách đầu bước
            if m["state"] == "patrol" and pd >= thr and dist <= sp["detect_radius"]:
                m["state"] = "chase"
            elif m["state"] == "chase" and (dist > sp["exit_radius"] or pd < thr):
                m["state"] = "patrol"
            if m["state"] == "chase":
                step = sp["chase_speed"] / TICK
                ux, uy = _unit(px - m["pos"][0], pd - m["pos"][1])
                s = min(step, dist)
                self._monster_move(m, m["pos"][0] + ux * s, m["pos"][1] + uy * s)
            else:
                step = sp["patrol_speed"] / TICK
                wx, wy = m["waypoints"][m["target_idx"]]
                dw = math.dist(m["pos"], (wx, wy))
                if dw <= step + 1e-9:  # sai số số thực: 60 + 239/60 cách 64 đúng một bước
                    self._monster_move(m, wx, wy)
                    m["target_idx"] = 1 - m["target_idx"]  # đổi mục tiêu cho bước sau
                else:
                    ux, uy = _unit(wx - m["pos"][0], wy - m["pos"][1])
                    self._monster_move(m, m["pos"][0] + ux * step, m["pos"][1] + uy * step)
        if self.invuln_ticks > 0:
            return False
        cands = []
        for m in self.monsters:
            sp = species[m["kind"]]
            if m["state"] == "recoil" or m["id"] in fresh or pd < sp["depths"][0]:
                continue
            d = math.dist(self.pos, m["pos"])
            if d <= sp["hit_radius"]:
                cands.append((d, id_key(m["id"]), m))
        if not cands:
            return False
        _, _, m = min(cands, key=lambda c: c[:2])
        n_lost = math.floor(len(self.hold) * mo["loss_ratio"])
        lost = list(reversed(self.hold[len(self.hold) - n_lost:])) if n_lost else []
        if n_lost:
            self.hold = self.hold[:len(self.hold) - n_lost]
        self.hp = max(0, self.hp - 1)
        self.invuln_ticks = int(mo["invuln_ticks"])
        sp = species[m["kind"]]
        m["state"], m["state_ticks_left"] = "recoil", int(sp["recoil_ticks"])
        m["recoil_dir"] = list(_unit(m["pos"][0] - px, m["pos"][1] - pd))  # trùng tâm dùng +x
        events.append(("monster_hit", {"monster_id": m["id"], "hp": self.hp, "lost": lost, "pos": list(self.pos)}))
        if self.hp > 0:
            return False
        self._faint("monster", events)
        return True

    def _monster_move(self, m, x, d):
        b = self.t["bounds"]
        lo, hi = self.t["monsters"]["species"][m["kind"]]["depths"]
        m["pos"] = [min(b["x"][1], max(b["x"][0], x)), min(hi, max(lo, d))]

    # --- cá ----------------------------------------------------------------------------
    def _swim_fish(self):
        t = self.t
        step = t["fish_speed"] / TICK
        turn = int(t["fish_turn_ticks"])
        xlo, xhi = t["fish_x"]
        rng = self.rng.get("fish_turn")
        for f in sort_by_id(self.fish):
            f["age_ticks"] += 1
            if f["age_ticks"] % turn == 0:
                f["heading_deg"] = rng.random() * 360.0
            dlo, dhi = t["fish_depths"][f["kind"]]
            x0 = min(xhi, max(xlo, f["pos"][0]))  # giả định: clarify #23 — cá fixture ngoài miền kéo vào miền
            d0 = min(dhi, max(dlo, f["pos"][1]))
            h = math.radians(f["heading_deg"])
            x, fx = _reflect(x0 + step * math.cos(h), xlo, xhi)
            d, fd = _reflect(d0 + step * math.sin(h), dlo, dhi)
            hd = f["heading_deg"]
            if fx:
                hd = 180.0 - hd
            if fd:
                hd = -hd
            f["pos"], f["heading_deg"] = [x, d], hd % 360.0

    def _spawn_fish(self):
        """Sinh một đàn: loài theo trọng số (chuẩn hóa trên loài còn điểm hợp lệ), điểm đều, hướng theo seed.
        giả định: clarify #19 (thứ tự duyệt loài/điểm và cách rút số ngẫu nhiên)."""
        t = self.t
        clear = t["fish_spawn_clearance"]
        valid = {}
        for kind in sorted(t["fish_spawn_depths"]):
            pts = [(x, d) for x in t["fish_spawn_x"] for d in t["fish_spawn_depths"][kind]
                   if all(math.dist((x, d), f["pos"]) > clear for f in self.fish)]
            if pts:
                valid[kind] = sorted(pts)
        if not valid:
            return None
        rng = self.rng.get("fish_spawn")
        kinds = list(valid)
        total = sum(t["fish_weights"][k] for k in kinds)
        r = rng.random() * total
        kind = kinds[-1]
        for k in kinds:
            r -= t["fish_weights"][k]
            if r < 0:
                kind = k
                break
        x, d = rng.choice(valid[kind])
        f = {"id": self.ids.new("F"), "kind": kind, "pos": [float(x), float(d)],
             "heading_deg": rng.random() * 360.0, "age_ticks": 0}
        self.fish.append(f)
        return f

    # --- hái / bắt ---------------------------------------------------------------------
    def _space(self) -> int:
        return int(self.t["hold_capacity"]) - len(self.hold)

    def _nearest(self, coll, radius):
        """Phần tử gần nhất trong bán kính; bằng nhau thì id nhỏ (sort_by_id ổn định)."""
        best, best_d = None, None
        for e in sort_by_id(coll):
            d = math.dist(self.pos, e["pos"])
            if d <= radius and (best_d is None or d < best_d):
                best, best_d = e, d
        return best

    def _harvest(self, events):
        ready = [n for n in self.nodes if n["regrow_ticks"] == 0]
        node = self._nearest(ready, self.t["interact_radius"])
        if node is None:
            return
        count = int(self.t["node_yield"])
        if self._space() < count:
            events.append(("hold_full", {"action": "gather", "node_id": node["id"], "required": count,
                                         "free": self._space()}))
            return
        self.hold.extend([node["kind"]] * count)
        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
        events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "amount": count}))

    def _catch(self, events):
        fish = self._nearest(self.fish, self.t["catch_radius"])
        if fish is None:
            return
        count = int(self.t["fish_yield"][fish["kind"]])
        if self._space() < count:
            events.append(("hold_full", {"action": "catch", "fish_id": fish["id"], "required": count,
                                         "free": self._space()}))
            return
        self.hold.extend([fish["kind"]] * count)
        self.fish = [f for f in self.fish if f["id"] != fish["id"]]
        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
        events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "yield": count}))

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
