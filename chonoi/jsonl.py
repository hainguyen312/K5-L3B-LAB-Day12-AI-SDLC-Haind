"""Ghi JSONL tất định: làm tròn 3 chữ số khi XUẤT (tính toán dùng giá trị chính xác).

Ngoại lệ v1.2: độ tươi (`ExactFloat`) xuất đủ độ chính xác để snapshot quán khớp CHÍNH XÁC file kho (Ticket-03).
"""

import json


class ExactFloat(float):
    """Số thực không làm tròn khi xuất JSONL (dùng cho fresh)."""


def _clean(v):
    if isinstance(v, ExactFloat):
        return float(v)
    if isinstance(v, float):
        r = round(v, 3)
        return 0.0 if r == 0 else r  # tránh -0.0
    if isinstance(v, dict):
        return {k: _clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    return v


def dumps(obj) -> str:
    return json.dumps(_clean(obj), ensure_ascii=False, separators=(",", ":"))


class JsonlWriter:
    def __init__(self, path: str):
        self._f = open(path, "w", encoding="utf-8", newline="\n")

    def write(self, obj):
        self._f.write(dumps(obj) + "\n")

    def close(self):
        self._f.close()
