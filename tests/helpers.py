"""Tiện ích test: chạy headless, đọc JSONL, dựng fixture, so sánh có dung sai."""

import json
import math
import os
import shlex
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return path


def frames(*fr):
    return {"frames": list(fr)}


def headless_cmd():
    """Lệnh headless khai trong game.contract.json — test chạy qua đây nên dùng được với MỌI ngôn ngữ."""
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return shlex.split(json.load(f)["headless_cmd"])


def run_headless(*args, cwd=ROOT):
    """Chạy `<headless_cmd> <args>`; trả (mã thoát, stderr)."""
    p = subprocess.run([*headless_cmd(), *args], cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stderr


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def snapshots(rows):
    return [r for r in rows if r["type"] == "snapshot"]


def events(rows, name=None):
    return [r for r in rows if r["type"] == "event" and (name is None or r["name"] == name)]


def close(a, b, tol=0.1):
    return abs(a - b) <= tol


def dist(p, q):
    return math.dist(p, q)


class Workdir:
    """Thư mục tạm tự dọn: with Workdir() as w: w.path('x.json')."""

    def __enter__(self):
        self._d = tempfile.TemporaryDirectory()
        return self

    def __exit__(self, *a):
        self._d.cleanup()

    def path(self, name):
        return os.path.join(self._d.name, name)


# --- v1.2 (Ticket-03): kho / giỏ là mảng cá thể {id, kind, fresh} ---------------------------------------------
def items(*kinds, fresh=100, start=1):
    """Cá thể I<start>, I<start+1>… theo thứ tự `kinds` (thứ tự vào giỏ)."""
    return [{"id": f"I{start + i}", "kind": k, "fresh": fresh} for i, k in enumerate(kinds)]


def stock(start=1, fresh=100, **counts):
    """Kho quán dạng cá thể từ số lượng theo loại: stock(ca_loc=1, bong_sung=2)."""
    kinds = [k for k, n in counts.items() for _ in range(n)]
    return items(*kinds, fresh=fresh, start=start)


def kinds(arr):
    return [it["kind"] for it in arr]


def kind_counts(arr):
    c = {}
    for it in arr:
        c[it["kind"]] = c.get(it["kind"], 0) + 1
    return {k: c[k] for k in sorted(c)}
