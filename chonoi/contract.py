"""Đọc game.contract.json và kiểm dải hợp lệ của tuning (Test Contract v1.2: PRD-0 mục A, Ticket-02 mục 4.1,
Ticket-03 "Contract v1.2" — khối freshness)."""

import json
import os

from .errors import BadInput

NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
INGREDIENTS = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game.contract.json")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _between(name, v, lo, hi):
    if not _num(v) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải trong [{lo}, {hi}], đang là {v!r}")


def load_contract(path=DEFAULT_PATH) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được {path}: {e}")
    if c.get("contract_version") != "1.2":
        raise BadInput("contract_version phải là \"1.2\"")
    validate_tuning(c.get("tuning"))
    return c


def _int_between(name, v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải là số nguyên trong [{lo}, {hi}], đang là {v!r}")


def _pos_in(name, pos, bounds, keys):
    if (not isinstance(pos, list) or len(pos) != 2 or not all(_num(c) for c in pos)):
        raise BadInput(f"tuning.{name} phải là [số, số]")
    for c, k in zip(pos, keys):
        lo, hi = bounds[k]
        if not (lo <= c <= hi):
            raise BadInput(f"tuning.{name} nằm ngoài vùng {k} ∈ [{lo}, {hi}]")


def _bounds(name, b, keys):
    if not isinstance(b, dict) or set(b) != set(keys):
        raise BadInput(f"tuning.{name}.bounds phải có đúng khóa {list(keys)}")
    for k in keys:
        v = b[k]
        if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v) and v[0] == 0 and v[1] > 0):
            raise BadInput(f"tuning.{name}.bounds.{k} phải là [0, số dương]")


def _validate_gather(g):
    """Dải hợp lệ P1 theo PRD mục 13.2."""
    _between("gather.duration_s", g.get("duration_s"), 60, 600)
    _bounds("gather", g.get("bounds"), ("x", "d"))
    b = g["bounds"]
    _between("gather.dock_radius", g.get("dock_radius"), 0.5, 5)
    _between("gather.interact_radius", g.get("interact_radius"), 0.5, 5)
    _between("gather.catch_radius", g.get("catch_radius"), 0.5, 5)
    _between("gather.swim_speed", g.get("swim_speed"), 1, 10)
    _between("gather.catch_cooldown_s", g.get("catch_cooldown_s"), 0, 10)
    _between("gather.oxygen_max_s", g.get("oxygen_max_s"), 10, 120)
    _int_between("gather.ramp_max_ticks", g.get("ramp_max_ticks"), 0, 6)
    _int_between("gather.hold_capacity", g.get("hold_capacity"), 4, 30)
    _int_between("gather.hp_max", g.get("hp_max"), 1, 99)
    _int_between("gather.oxygen_refill_per_tick", g.get("oxygen_refill_per_tick"), 1, 10_000)
    _int_between("gather.choke_interval_ticks", g.get("choke_interval_ticks"), 1, 10_000)
    _int_between("gather.node_yield", g.get("node_yield"), 1, 12)
    _between("gather.regrow_s", g.get("regrow_s"), 0.1, 600)
    _between("gather.surface_depth", g.get("surface_depth"), 0, 5)
    _pos_in("gather.dock_pos", g.get("dock_pos"), b, ("x", "d"))
    _pos_in("gather.start_pos", g.get("start_pos"), b, ("x", "d"))
    if not _num(g.get("start_heading_deg")):
        raise BadInput("tuning.gather.start_heading_deg phải là số")
    fy = g.get("fish_yield")
    if not isinstance(fy, dict) or set(fy) != set(FISH_KINDS):
        raise BadInput(f"tuning.gather.fish_yield phải có đủ {FISH_KINDS}")
    for k, v in fy.items():
        _int_between(f"gather.fish_yield.{k}", v, 1, g["hold_capacity"])
    nodes = g.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise BadInput("tuning.gather.nodes phải là mảng không rỗng")
    seen, kinds = set(), set()
    for n in nodes:
        if not isinstance(n, dict) or not isinstance(n.get("id"), str) or n["id"] in seen:
            raise BadInput("tuning.gather.nodes: mỗi nút cần id duy nhất")
        seen.add(n["id"])
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: kind phải thuộc {NODE_KINDS}")
        kinds.add(n["kind"])
        _pos_in(f"gather.nodes.{n['id']}.pos", n.get("pos"), b, ("x", "d"))
        if n["pos"][1] != 0:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
    if kinds != set(NODE_KINDS):
        raise BadInput(f"tuning.gather.nodes phải có ít nhất một nút mỗi loại {NODE_KINDS}")
    # --- v1.1: cá bơi / sinh ---
    _int_between("gather.fish_initial", g.get("fish_initial"), 1, 36)
    _int_between("gather.fish_max", g.get("fish_max"), g["fish_initial"], 36)
    _between("gather.fish_speed", g.get("fish_speed"), 0.1, 10)
    _int_between("gather.fish_turn_ticks", g.get("fish_turn_ticks"), 1, 100_000)
    _int_between("gather.fish_spawn_ticks", g.get("fish_spawn_ticks"), 1, 100_000)
    _between("gather.fish_spawn_clearance", g.get("fish_spawn_clearance"), 0, 50)
    fx = g.get("fish_x")
    if not (isinstance(fx, list) and len(fx) == 2 and all(_num(c) for c in fx) and b["x"][0] <= fx[0] < fx[1] <= b["x"][1]):
        raise BadInput("tuning.gather.fish_x phải là [lo, hi] trong vùng nước")
    sx = g.get("fish_spawn_x")
    if not (isinstance(sx, list) and sx and all(_num(c) and fx[0] <= c <= fx[1] for c in sx)):
        raise BadInput("tuning.gather.fish_spawn_x phải là danh sách x trong fish_x")
    for key in ("fish_depths", "fish_spawn_depths", "fish_weights"):
        if not isinstance(g.get(key), dict) or set(g[key]) != set(FISH_KINDS):
            raise BadInput(f"tuning.gather.{key} phải có đủ {FISH_KINDS}")
    for k in FISH_KINDS:
        band = g["fish_depths"][k]
        if not (isinstance(band, list) and len(band) == 2 and all(_num(c) for c in band)
                and g["surface_depth"] < band[0] < band[1] <= b["d"][1]):
            raise BadInput(f"tuning.gather.fish_depths.{k} phải là [lo, hi] dưới mặt nước")
        sd = g["fish_spawn_depths"][k]
        if not (isinstance(sd, list) and sd and all(_num(c) and band[0] <= c <= band[1] for c in sd)):
            raise BadInput(f"tuning.gather.fish_spawn_depths.{k} phải nằm trong fish_depths")
        if not (_num(g["fish_weights"][k]) and g["fish_weights"][k] > 0):
            raise BadInput(f"tuning.gather.fish_weights.{k} phải > 0")
    _validate_monsters(g.get("monsters"), b)


def _validate_monsters(mo, b):
    if not isinstance(mo, dict) or not {"species", "spawns", "invuln_ticks", "loss_ratio"} <= set(mo):
        raise BadInput("tuning.gather.monsters cần species, spawns, invuln_ticks, loss_ratio")
    _int_between("gather.monsters.invuln_ticks", mo["invuln_ticks"], 0, 100_000)
    _between("gather.monsters.loss_ratio", mo["loss_ratio"], 0, 1)
    keys = {"patrol_speed", "chase_speed", "detect_radius", "exit_radius", "depths", "hit_radius", "recoil_ticks",
            "recoil_dist"}
    if not isinstance(mo["species"], dict) or not mo["species"]:
        raise BadInput("tuning.gather.monsters.species phải là object không rỗng")
    for name, sp in mo["species"].items():
        if not isinstance(sp, dict) or set(sp) != keys:
            raise BadInput(f"tuning.gather.monsters.species.{name} phải có đúng {sorted(keys)}")
        for k in ("patrol_speed", "chase_speed", "detect_radius", "exit_radius", "hit_radius", "recoil_dist"):
            if not (_num(sp[k]) and sp[k] > 0):
                raise BadInput(f"tuning.gather.monsters.species.{name}.{k} phải > 0")
        _int_between(f"gather.monsters.species.{name}.recoil_ticks", sp["recoil_ticks"], 1, 100_000)
        dep = sp["depths"]
        if not (isinstance(dep, list) and len(dep) == 2 and all(_num(c) for c in dep) and b["d"][0] <= dep[0] < dep[1] <= b["d"][1]):
            raise BadInput(f"tuning.gather.monsters.species.{name}.depths sai")
    seen = set()
    for m in mo["spawns"] if isinstance(mo["spawns"], list) else [None]:
        if not isinstance(m, dict) or not isinstance(m.get("id"), str) or m["id"] in seen:
            raise BadInput("tuning.gather.monsters.spawns: mỗi con cần id duy nhất")
        seen.add(m["id"])
        if m.get("kind") not in mo["species"]:
            raise BadInput(f"tuning.gather.monsters.spawns.{m['id']}: kind không có trong species")
        _int_between(f"gather.monsters.spawns.{m['id']}.from_day", m.get("from_day"), 1, 5)
        wps = m.get("waypoints")
        if not (isinstance(wps, list) and len(wps) == 2):
            raise BadInput(f"tuning.gather.monsters.spawns.{m['id']}: cần đúng 2 waypoint")
        for i, wp in enumerate([m.get("pos")] + wps):
            _pos_in(f"gather.monsters.spawns.{m['id']}.pos/waypoint{i}", wp, b, ("x", "d"))


def _validate_day(t):
    menu = t["menu"]
    dp = t.get("day_plan")
    if not isinstance(dp, list) or len(dp) != 5:
        raise BadInput("tuning.day_plan phải là mảng 5 Ngày")
    for i, d in enumerate(dp, 1):
        if not isinstance(d, dict) or d.get("day") != i:
            raise BadInput(f"tuning.day_plan[{i - 1}].day phải là {i}")
        check_plan_entry(d, menu, f"tuning.day_plan[{i - 1}]")
    shop = t.get("shop")
    if not isinstance(shop, dict) or not {"max_ticks", "upgrades"} <= set(shop):
        raise BadInput("tuning.shop cần max_ticks, upgrades")
    _int_between("shop.max_ticks", shop["max_ticks"], 1, 100_000)
    ups = shop["upgrades"]
    field = {"oxygen": "oxygen_max_s", "hp": "hp_max"}
    if not isinstance(ups, dict) or not set(field) <= set(ups):
        raise BadInput("tuning.shop.upgrades cần oxygen và hp")
    for kind, f in field.items():
        lv = ups[kind]
        if not isinstance(lv, list) or not lv:
            raise BadInput(f"tuning.shop.upgrades.{kind} phải là mảng cấp")
        for i, u in enumerate(lv, 1):
            if not isinstance(u, dict) or u.get("level") != i or set(u) != {"level", "price", f}:
                raise BadInput(f"tuning.shop.upgrades.{kind}[{i - 1}] phải là {{level={i}, price, {f}}}")
            _int_between(f"shop.upgrades.{kind}[{i - 1}].price", u["price"], 1, 10 ** 9)
            if not (_num(u[f]) and u[f] > 0):
                raise BadInput(f"tuning.shop.upgrades.{kind}[{i - 1}].{f} phải > 0")


def check_plan_entry(d, menu, where):
    """Kiểm một mục kế hoạch Ngày; trả ingredients tính lại (tổng công thức × số suất)."""
    dishes = d.get("dishes")
    if not isinstance(dishes, dict) or not dishes:
        raise BadInput(f"{where}.dishes phải là map id món -> số nguyên dương")
    ing = {}
    for dish, n in dishes.items():
        if dish not in menu:
            raise BadInput(f"{where}.dishes: món lạ {dish}")
        if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
            raise BadInput(f"{where}.dishes.{dish} phải là số nguyên dương")
        for k, v in menu[dish]["recipe"].items():
            ing[k] = ing.get(k, 0) + v * n
    ing = {k: ing[k] for k in sorted(ing)}
    if "ingredients" in d and d["ingredients"] != ing:
        raise BadInput(f"{where}.ingredients phải bằng tổng công thức × số suất: {ing}")
    return ing


def validate_tuning(t):
    if not isinstance(t, dict):
        raise BadInput("thiếu khối tuning")
    g, q, menu = t.get("gather"), t.get("quan"), t.get("menu")
    if not isinstance(g, dict) or not isinstance(q, dict) or not isinstance(menu, dict):
        raise BadInput("tuning phải có gather, quan, menu")
    _validate_gather(g)
    # Quán: dải hợp lệ P1 (PRD mục 13.2)
    _between("quan.duration_s", q.get("duration_s"), 60, 600)
    _bounds("quan", q.get("bounds"), ("x", "z"))
    _between("quan.patience_s", q.get("patience_s"), 20, 180)
    _between("quan.walk_speed", q.get("walk_speed"), 1, 10)
    _between("quan.interact_radius", q.get("interact_radius"), 0.5, 5)
    _int_between("quan.ramp_max_ticks", q.get("ramp_max_ticks", 6), 0, 6)
    _between("quan.eat_s", q.get("eat_s"), 0.1, 600)
    _between("quan.customer_interval_s", q.get("customer_interval_s"), 0.1, 600)
    _int_between("quan.first_customer_tick", q.get("first_customer_tick"), 1, int(q["duration_s"] * 60) - 1)
    if not (_num(q.get("tip_rate")) and q["tip_rate"] > 0 and _num(q.get("left_reputation_delta"))
            and q["left_reputation_delta"] < 0):
        raise BadInput("tip_rate phải > 0 và left_reputation_delta phải < 0")
    ratio = q.get("tip_min_patience_ratio")
    if not (_num(ratio) and 0 < ratio <= 1):
        raise BadInput("quan.tip_min_patience_ratio phải thuộc (0, 1]")
    if not (_num(q.get("tip_reputation")) and q["tip_reputation"] > 0):
        raise BadInput("quan.tip_reputation phải > 0")
    if q.get("burn_s") is not None:
        raise BadInput("burn_s phải là null ở Phase 1")
    _int_between("quan.carry_limit", q.get("carry_limit"), 1, 1)
    for key in ("stoves", "tables"):
        arr = q.get(key)
        if not isinstance(arr, list) or not arr or len({e.get("id") for e in arr}) != len(arr):
            raise BadInput(f"tuning.quan.{key} phải là mảng id duy nhất")
        for e in arr:
            _pos_in(f"quan.{key}.{e['id']}.pos", e.get("pos"), q["bounds"], ("x", "z"))
    for dish_id, d in menu.items():
        rec = d.get("recipe")
        if not isinstance(rec, dict) or not rec or any(k not in INGREDIENTS or isinstance(v, bool) or not isinstance(v, int)
                                                       or v <= 0 for k, v in rec.items()):
            raise BadInput(f"menu.{dish_id}.recipe phải là map nguyên liệu -> số nguyên dương")
        price, cook = d.get("price"), d.get("cook_s")
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0 or not _num(cook) or cook <= 0:
            raise BadInput(f"menu.{dish_id}: price (nguyên) và cook_s phải > 0")
    _validate_day(t)
    fr = t.get("freshness")
    if not isinstance(fr, dict) or set(fr) != {"initial", "gather_decay_per_s", "quan_decay_per_s", "spoiled_below"}:
        raise BadInput("tuning.freshness cần initial, gather_decay_per_s, quan_decay_per_s, spoiled_below")
    _between("freshness.initial", fr["initial"], 1, 100)
    _between("freshness.spoiled_below", fr["spoiled_below"], 0, fr["initial"])
    for k in ("gather_decay_per_s", "quan_decay_per_s"):
        _between(f"freshness.{k}", fr[k], 0, 100)
