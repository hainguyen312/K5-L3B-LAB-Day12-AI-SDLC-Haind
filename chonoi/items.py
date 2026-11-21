"""Cá thể nguyên liệu và độ tươi (Test Contract v1.2, Ticket-03 mục 1), nhóm Haind.

Cá thể: {"id": "I<n>", "kind": <nguyên liệu>, "fresh": <0..100>}. Trong mô phỏng `fresh` là `Fraction` để phép so
ngưỡng 30 và phép floor giá chính xác tuyệt đối (hao 0.5/s ở giỏ = 1/120 mỗi tick, 0.25/s ở quán = 1/240 mỗi tick).
Khi XUẤT ra JSON thì đổi sang float (`out`). Khi ĐỌC, số thập phân nằm sát lưới 1/240 (sai số < 1e-6 đơn vị) được
đưa về đúng lưới, nên ghi file rồi đọc lại vẫn giữ nguyên giá trị và nhánh ở ngưỡng (ADR-0002).
"""

import math
from fractions import Fraction

from .errors import BadInput
from .ids import id_key, sort_by_id
from .jsonl import ExactFloat

KINDS = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")
GRID = 240  # đơn vị mỗi điểm tươi (gợi ý của Ticket-03)
ITEM_KEYS = {"id", "kind", "fresh"}


def frac(v) -> Fraction:
    """Số JSON (int/float) -> Fraction, đưa về lưới 1/240 nếu sát lưới."""
    f = Fraction(str(v)) if isinstance(v, float) else Fraction(v)
    u = f * GRID
    r = round(u)
    if abs(u - r) < Fraction(1, 10 ** 6):
        return Fraction(r, GRID)
    return f


def fresh_cfg(tuning):
    fr = tuning["freshness"]
    return {"initial": frac(fr["initial"]), "spoiled_below": frac(fr["spoiled_below"]),
            "gather_per_tick": frac(fr["gather_decay_per_s"]) / 60, "quan_per_tick": frac(fr["quan_decay_per_s"]) / 60}


def validate(arr, where="items", kinds=KINDS):
    """Kiểm mảng cá thể {id, kind, fresh}; trả bản sao với fresh là Fraction. Sai -> BadInput (mã 2)."""
    if not isinstance(arr, list):
        raise BadInput(f"{where} phải là mảng cá thể {{id, kind, fresh}} (contract v1.2; kho đếm không còn hợp lệ)")
    out, seen = [], set()
    for i, it in enumerate(arr):
        if not isinstance(it, dict) or set(it) != ITEM_KEYS:
            raise BadInput(f"{where}[{i}] phải có đúng khóa id, kind, fresh")
        iid, kind, fr = it["id"], it["kind"], it["fresh"]
        if not isinstance(iid, str) or not iid:
            raise BadInput(f"{where}[{i}].id phải là chuỗi khác rỗng")
        if iid in seen:
            raise BadInput(f"{where}: id trùng {iid}")
        seen.add(iid)
        if kind not in kinds:
            raise BadInput(f"{where}[{i}]: nguyên liệu lạ {kind!r}")
        if isinstance(fr, bool) or not isinstance(fr, (int, float)) or not math.isfinite(fr) or not (0 <= fr <= 100):
            raise BadInput(f"{where}[{i}].fresh phải hữu hạn trong [0, 100]")
        out.append({"id": iid, "kind": kind, "fresh": frac(fr)})
    return out


def out(it) -> dict:
    """Cá thể -> dict JSON (fresh float)."""
    return {"id": it["id"], "kind": it["kind"], "fresh": ExactFloat(it["fresh"])}


def out_list(items, by_id=True) -> list:
    return [out(it) for it in (sort_by_id(items) if by_id else items)]


def by_kind_then_id(items) -> list:
    return sorted(items, key=lambda it: (it["kind"], id_key(it["id"])))


def decay(items, per_tick, below, location, events):
    """Hao tươi một tick (kẹp 0); phát `spoiled` theo id cho cá thể vừa đi từ >= ngưỡng xuống < ngưỡng.
    Trả tập id vừa ươn."""
    just = []
    for it in items:
        before = it["fresh"]
        it["fresh"] = max(Fraction(0), before - per_tick)
        if before >= below > it["fresh"]:
            just.append(it)
    for it in sort_by_id(just):
        events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": location}))
    return {it["id"] for it in just}


def counts(items) -> dict:
    c = {}
    for it in items:
        c[it["kind"]] = c.get(it["kind"], 0) + 1
    return {k: c[k] for k in sorted(c)}
