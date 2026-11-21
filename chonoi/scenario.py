"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json

from .errors import BadInput
from .inventory import KINDS_P1, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks", "monsters"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
FISH_KEYS = {"id", "kind", "pos", "heading_deg", "age_ticks"}
MONSTER_KEYS = {"id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir"}
MONSTER_STATES = ("patrol", "chase", "recoil")  # stunned chỉ có khi bật mở rộng Lao (nhóm chưa bật)
DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan", "day"}:
        raise BadInput("scenario chỉ được có khối 'gather', 'quan' hoặc 'day'")
    allowed_blocks = {"day", "gather", "quan"} if mode == "day" else {mode}
    if set(data) - allowed_blocks:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối {sorted(allowed_blocks)}")
    if mode == "day":
        out = {k: _load_block(data.get(k, {}), k, tuning) for k in ("gather", "quan")}
        if "stock" in out["quan"] or "reputation" in out["quan"]:
            raise BadInput("chạy day cấm quan.stock và quan.reputation (dựng hàng bằng gather.hold)")
        out["day"] = _validate_day(data.get("day", {}), tuning)
        return out
    return _load_block(data.get(mode, {}), mode, tuning)


def _load_block(block, mode, tuning):
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning)
    return block


def _validate_day(b, tuning):
    """Khối day (Ticket-02 mục 4.3): trạng thái xuyên Ngày."""
    from .contract import check_plan_entry
    if not isinstance(b, dict):
        raise BadInput("khối day phải là object")
    extra = set(b) - DAY_KEYS
    if extra:
        raise BadInput(f"trường lạ trong day: {sorted(extra)}")
    q = tuning["quan"]
    for k in ("money", "earned"):
        if k in b:
            _nonneg_int(f"day.{k}", b[k])
    money, earned = b.get("money", 0), b.get("earned", 0)
    if money > 0 and not ("money" in b and "earned" in b):
        raise BadInput("có tiền đầu kỳ thì khai cả day.money và day.earned")
    if not (0 <= money <= earned):
        raise BadInput("cần 0 <= day.money <= day.earned")
    if "reputation" in b:
        r = b["reputation"]
        if not _num(r) or not (q["reputation_min"] <= r <= q["reputation_max"]):
            raise BadInput("day.reputation ngoài [reputation_min, reputation_max]")
    ups = b.get("upgrades", {})
    shop_ups = tuning["shop"]["upgrades"]
    if not isinstance(ups, dict):
        raise BadInput("day.upgrades phải là map id nâng cấp -> cấp")
    for k, lv in ups.items():
        if k not in ("oxygen", "hp"):
            raise BadInput(f"day.upgrades: nâng cấp lạ/chưa bật {k}")
        if isinstance(lv, bool) or not isinstance(lv, int) or not (0 <= lv <= len(shop_ups[k])):
            raise BadInput(f"day.upgrades.{k} phải là cấp trong [0, {len(shop_ups[k])}]")
    plan = [dict(d) for d in tuning["day_plan"]]
    if "day_plan" in b:
        if not isinstance(b["day_plan"], list):
            raise BadInput("day.day_plan phải là mảng")
        seen = set()
        for i, d in enumerate(b["day_plan"]):
            if not isinstance(d, dict) or set(d) - {"day", "dishes", "ingredients"} or "dishes" not in d:
                raise BadInput(f"day.day_plan[{i}] phải là {{day, dishes[, ingredients]}}")
            n = d.get("day")
            if isinstance(n, bool) or not isinstance(n, int) or not (1 <= n <= 5) or n in seen:
                raise BadInput(f"day.day_plan[{i}].day phải là số Ngày 1..5, không trùng")
            seen.add(n)
            ing = check_plan_entry(d, tuning["menu"], f"day.day_plan[{i}]")
            plan[n - 1] = {"day": n, "dishes": dict(d["dishes"]), "ingredients": ing}
    return {"money": money, "earned": earned,
            "reputation": b.get("reputation", q["reputation_initial"]),
            "upgrades": {k: v for k, v in sorted(ups.items()) if v > 0}, "day_plan": plan}


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài vùng nước ({axis} ∈ [{lo}, {hi}])")


def _validate_gather(b, tuning):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        h = b["hold"]
        if not isinstance(h, list) or any(k not in KINDS_P1 for k in h):
            raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax = int(round(g["oxygen_max_s"] * 60))
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= g["hp_max"]):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        if p["zero_oxy_ticks"] > 59:
            raise BadInput("player.zero_oxy_ticks phải trong [0, 59]")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    for n in b.get("nodes", []):
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    for f in b.get("fish", []):
        extra = set(f) - FISH_KEYS
        if extra:
            raise BadInput(f"fish.{f['id']}: trường lạ {sorted(extra)}")
        if "age_ticks" in f:
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")
    if "monsters" in b:
        _check_ids("monsters", b["monsters"])
        for m in b["monsters"]:
            _validate_monster(m, g, bounds)


def _validate_monster(m, g, bounds):
    mid = m["id"]
    extra = set(m) - MONSTER_KEYS
    if extra:
        raise BadInput(f"monsters.{mid}: trường lạ {sorted(extra)}")
    species = g["monsters"]["species"]
    if m.get("kind") not in species:
        raise BadInput(f"monsters.{mid}: kind phải thuộc {sorted(species)}")
    sp = species[m["kind"]]
    _pos(f"monsters.{mid}.pos", m.get("pos"), bounds)
    lo, hi = sp["depths"]
    if not (lo <= m["pos"][1] <= hi):
        raise BadInput(f"monsters.{mid}.pos ngoài dải độ sâu của loài [{lo}, {hi}]")
    wps = m.get("waypoints")
    if not (isinstance(wps, list) and len(wps) == 2):
        raise BadInput(f"monsters.{mid}: cần đúng 2 waypoint")
    for i, wp in enumerate(wps):
        _pos(f"monsters.{mid}.waypoints[{i}]", wp, bounds)
    if m.get("target_idx", 1) not in (0, 1) or isinstance(m.get("target_idx", 1), bool):
        raise BadInput(f"monsters.{mid}.target_idx phải là 0 hoặc 1")
    state = m.get("state", "patrol")
    if state not in MONSTER_STATES:
        raise BadInput(f"monsters.{mid}.state phải thuộc {MONSTER_STATES}")
    ticks = m.get("state_ticks_left", 0)
    _nonneg_int(f"monsters.{mid}.state_ticks_left", ticks)
    rd = m.get("recoil_dir")
    if state == "recoil":
        if ticks < 1:
            raise BadInput(f"monsters.{mid}: recoil cần state_ticks_left > 0")
        if not (isinstance(rd, list) and len(rd) == 2 and all(_num(c) for c in rd)
                and abs((rd[0] ** 2 + rd[1] ** 2) ** 0.5 - 1) <= 1e-6):
            raise BadInput(f"monsters.{mid}.recoil_dir phải là vector đơn vị khi recoil")
    else:
        if ticks != 0 or rd is not None:
            raise BadInput(f"monsters.{mid}: chỉ recoil mới có state_ticks_left/recoil_dir")


def _validate_quan(b, tuning):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        validate_items(b["stock"])
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = tuning["quan"]["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")
    table_ids = [c.get("table_id") for c in b.get("customers", [])]
    known = {t["id"] for t in tuning["quan"]["tables"]} | {t.get("id") for t in b.get("tables", [])}
    for c in b.get("customers", []):
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known:
            raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")
