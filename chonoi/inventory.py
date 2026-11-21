"""File kho (Contract G) — v1.2 (Ticket-03): kho CÁ THỂ {"items": [{"id", "kind", "fresh"}, ...]}.

Đọc: chọn schema theo contract_version 1.2; kho đếm (object), sai schema, kind lạ, id trùng, fresh ngoài [0, 100]
-> BadInput (mã 2). Trả danh sách cá thể (fresh là Fraction, xem chonoi/items.py).
Ghi: sắp theo id, fresh ghi đủ độ chính xác (repr float, đọc lại ra đúng giá trị nhờ lưới 1/240), qua file tạm cùng
thư mục rồi thay thế nguyên tử, byte-ổn-định. Kho rỗng: {"items": []}.
"""

import json
import os
import tempfile

from . import items as itm
from .errors import BadInput

KINDS_P1 = itm.KINDS  # giữ tên cũ cho mã đang dùng


def read_inventory(path: str) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return itm.validate(data["items"], "file kho items")


def write_inventory(path: str, items: list):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": itm.out_list(items)}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
