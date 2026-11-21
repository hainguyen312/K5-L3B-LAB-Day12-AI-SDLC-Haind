#!/usr/bin/env bash
# verify-phase: chạy toàn bộ kiểm chứng của một phase và lưu bằng chứng vào docs/proof/phase-N/.
# Dùng: bash .agents/skills/verify-phase/verify.sh 1
set -u
PHASE="${1:?cần số phase, ví dụ: 1}"
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT="$ROOT/docs/proof/phase-$PHASE"
mkdir -p "$OUT"
cd "$ROOT"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
status=0

{
  echo "# verify phase $PHASE — $(git rev-parse --short HEAD 2>/dev/null || echo no-git) — python $(python3 -V 2>&1)"
  echo "## unittest"
} > "$OUT/verify.txt"
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v >>"$OUT/verify.txt" 2>&1 || status=1

# Tất định: cùng seed -> giống từng byte (gather và quan)
echo '{"frames":[{"tick":0,"move":[1,0.4]},{"tick":180,"catch":true},{"tick":400,"move":[-1,-1]}]}' > "$TMP/in.json"
for mode in gather quan; do
  for i in 1 2; do
    python3 -m chonoi.headless --mode $mode --seed 7 --ticks 1200 --inputs "$TMP/in.json" --out "$TMP/$mode$i.jsonl" || status=1
  done
  if cmp -s "$TMP/${mode}1.jsonl" "$TMP/${mode}2.jsonl"; then
    echo "## determinism $mode: OK ($(shasum -a 256 "$TMP/${mode}1.jsonl" | cut -c1-16))" >> "$OUT/verify.txt"
  else
    echo "## determinism $mode: FAIL" >> "$OUT/verify.txt"; status=1
  fi
done

# Luồng tích hợp gather -> kho -> quan (ví dụ PRD-0 mục G)
# v1.2: giỏ là cá thể {id, kind, fresh}
echo '{"gather":{"hold":[{"id":"I1","kind":"ca_loc","fresh":100},{"id":"I2","kind":"bong_sung","fresh":100},{"id":"I3","kind":"bong_sung","fresh":100}]}}' > "$TMP/sc.json"
echo '{"frames":[{"tick":0,"interact":true}]}' > "$TMP/dock.json"  # dùng lại ở smoke bàn giao P3
python3 -m chonoi.headless --mode gather --seed 42 --ticks 1 --scenario "$TMP/sc.json" --inputs "$TMP/dock.json" \
  --inventory-out "$OUT/kho.json" --out "$OUT/gather-dock.jsonl" || status=1
python3 -m chonoi.headless --mode quan --seed 42 --ticks 10800 --inventory "$OUT/kho.json" --snapshot-every 600 \
  --out "$OUT/quan-from-kho.jsonl" || status=1
echo "## integration: kho.json = $(cat "$OUT/kho.json")" >> "$OUT/verify.txt"
echo "## quan end: $(tail -n 1 "$OUT/quan-from-kho.jsonl")" >> "$OUT/verify.txt"

if [ "$PHASE" -ge 2 ]; then
  # Ticket-02 phút 20: smoke tích hợp gather --inventory-out -> quan --inventory, lưu integration.*
  cp "$OUT/kho.json" "$OUT/integration-kho.json" && mv "$OUT/gather-dock.jsonl" "$OUT/integration-gather.jsonl" \
    && mv "$OUT/quan-from-kho.jsonl" "$OUT/integration-quan.jsonl" && rm -f "$OUT/kho.json"
  python3 - "$OUT/integration-quan.jsonl" >> "$OUT/verify.txt" <<'PY' || status=1
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1])]
s0 = [r for r in rows if r["type"] == "snapshot"][0]
kho = json.load(open(sys.argv[1].replace("integration-quan.jsonl", "integration-kho.json")))["items"]
ok = s0["tick"] == 0 and s0["stock"] == kho and sorted(i["kind"] for i in kho) == ["bong_sung", "bong_sung", "ca_loc"]
print("## integration tick-0 stock == file kho (id/kind/fresh):", "OK" if ok else "FAIL", s0["stock"])
sys.exit(0 if ok else 1)
PY
  # smoke day --days 1 (thời gian chạy <= 20 s)
  t0=$(python3 -c 'import time;print(time.time())')
  python3 -m chonoi.headless --mode day --seed 7 --days 1 --ticks 30000 --snapshot-every 600 --out "$OUT/day-1.jsonl" || status=1
  t1=$(python3 -c 'import time;print(time.time())')
  echo "## day --days 1: $(tail -n 1 "$OUT/day-1.jsonl")" >> "$OUT/verify.txt"
  echo "## day --days 1 thời gian: $(python3 -c "print(round($t1-$t0,2))") s (yêu cầu <= 20 s)" >> "$OUT/verify.txt"
  # nhiều Ngày: cập bến ngay, mua Bình oxy trong Shop Ngày 1, kiểm cấp áp dụng ở Ngày 2
  echo '{"day":{"money":200,"earned":200},"gather":{"hold":[{"id":"I1","kind":"ca_loc","fresh":100}],"random_fish":false}}' > "$TMP/d.json"
  echo '{"frames":[{"tick":0,"interact":true},{"tick":1,"interact":false},{"tick":10801,"buy":"oxygen"},{"tick":10802,"shop_done":true}]}' > "$TMP/di.json"
  python3 -m chonoi.headless --mode day --seed 7 --days 2 --scenario "$TMP/d.json" --inputs "$TMP/di.json" --ticks 40000 \
    --snapshot-every 1000 --out "$OUT/days-2-upgrade.jsonl" || status=1
  python3 - "$OUT/days-2-upgrade.jsonl" >> "$OUT/verify.txt" <<'PY' || status=1
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1])]
ev = {r["name"]: r for r in rows if r["type"] == "event" and r["name"] in ("bought", "shop_end")}
d2 = [r for r in rows if r["type"] == "snapshot" and r.get("day") == 2 and r["phase"] == "gather"][0]
ok = ev["bought"]["data"]["level"] == 1 and d2["active_upgrades"] == {"oxygen": 1} and d2["player"]["oxygen_max_ticks"] == 2700
print("## days 2: bought", ev["bought"]["data"], "| Ngày 2 active", d2["active_upgrades"], "oxygen_max_ticks",
      d2["player"]["oxygen_max_ticks"], "| end", rows[-1]["reason"], rows[-1]["days_completed"], "OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
PY
  # regression P1 với số chuẩn
  PYTHONPATH=tests:. python3 -m unittest tests.test_smoke_p1 tests.test_rules_p1 >> "$OUT/regression-p1.txt" 2>&1 || status=1
  echo "## regression P1: $(tail -n 1 "$OUT/regression-p1.txt")" >> "$OUT/verify.txt"
fi

if [ "$PHASE" -ge 3 ]; then
  # Ticket-03: ca kiểm ngưỡng (fresh 30 -> spoiled ở tick 1) và smoke bàn giao file (so chính xác id/kind/fresh)
  echo '{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":30}],"random_fish":false,"monsters":[]}}' > "$TMP/t30.json"
  python3 -m chonoi.headless --mode gather --seed 1 --ticks 1 --scenario "$TMP/t30.json" --out "$OUT/threshold-30.jsonl" || status=1
  echo '{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":100}],"random_fish":false,"monsters":[]}}' > "$TMP/h.json"
  python3 -m chonoi.headless --mode gather --seed 1 --ticks 5 --scenario "$TMP/h.json" --inputs "$TMP/dock.json" \
    --inventory-out "$OUT/handover-kho.json" --out "$OUT/handover-gather.jsonl" || status=1
  python3 -m chonoi.headless --mode quan --seed 1 --ticks 0 --inventory "$OUT/handover-kho.json" --out "$OUT/handover-quan.jsonl" || status=1
  python3 - "$OUT" >> "$OUT/verify.txt" <<'PY' || status=1
import json, os, sys
d = sys.argv[1]
rd = lambda n: [json.loads(l) for l in open(os.path.join(d, n))]
sp = [r for r in rd("threshold-30.jsonl") if r["type"] == "event"]
want = [{"type": "event", "tick": 1, "phase": "gather", "name": "spoiled",
         "data": {"item_id": "I1", "kind": "ca_linh", "location": "hold"}}]
ok1 = sp == want
kho = json.load(open(os.path.join(d, "handover-kho.json")))["items"]
q0 = [r for r in rd("handover-quan.jsonl") if r["type"] == "snapshot"][0]
ok2 = q0["stock"] == kho and kho[0]["id"] == "I1" and abs(kho[0]["fresh"] - (100 - 1 / 120)) < 1e-9
print("## threshold-30: spoiled tick 1", "OK" if ok1 else f"FAIL {sp}")
print("## handover file -> quan tick 0 khớp chính xác:", "OK" if ok2 else "FAIL", kho)
sys.exit(0 if ok1 and ok2 else 1)
PY
  PYTHONPATH=tests:. python3 -m unittest tests.test_rules_p2 >> "$OUT/regression-p2.txt" 2>&1 || status=1
  echo "## regression P2: $(tail -n 1 "$OUT/regression-p2.txt")" >> "$OUT/verify.txt"
fi

if [ "$PHASE" -ge 4 ]; then
  # Ticket-04: benchmark có render (cần Chrome/Chromium; không có thì ghi SKIP), soak 10 Ngày x2 (so tính lặp)
  if python3 -c "from chonoi.bench import find_browser; import sys; sys.exit(0 if find_browser() else 1)"; then
    python3 -m chonoi.bench --seed 42 --duration 30 --out "$OUT/bench.json" > "$OUT/bench-run.txt" 2>&1 || status=1
    echo "## bench: $(cat "$OUT/bench.json" 2>/dev/null)" >> "$OUT/verify.txt"
  else
    echo "## bench: SKIP (không có Chrome/Chromium trên máy này)" >> "$OUT/verify.txt"
  fi
  python3 -m chonoi.soak --seed 7 --days 10 --out "$OUT/soak.json" > /dev/null || status=1
  python3 -m chonoi.soak --seed 7 --days 10 --out "$TMP/soak2.json" > /dev/null || status=1
  python3 - "$OUT/soak.json" "$TMP/soak2.json" >> "$OUT/verify.txt" <<'PY' || status=1
import json, sys
a, b = (json.load(open(p)) for p in sys.argv[1:3])
ta, tb = a.pop("duration_s"), b.pop("duration_s")
ok = a == b and a["days_completed"] == a["days"] == 10 and a["crashes"] == 0
print(f"## soak 10 Ngày: days_completed={a['days_completed']} crashes={a['crashes']} lặp lại giống nhau={a == b}"
      f" ({ta}s / {tb}s)", "OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
PY
  PYTHONPATH=tests:. python3 -m unittest tests.test_rules_p3 >> "$OUT/regression-p3.txt" 2>&1 || status=1
  echo "## regression P3: $(tail -n 1 "$OUT/regression-p3.txt")" >> "$OUT/verify.txt"
fi

[ $status -eq 0 ] && echo "## RESULT: PASS" >> "$OUT/verify.txt" || echo "## RESULT: FAIL" >> "$OUT/verify.txt"
tail -n 6 "$OUT/verify.txt"
exit $status
