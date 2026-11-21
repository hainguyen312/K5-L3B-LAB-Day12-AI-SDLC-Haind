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
echo '{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}' > "$TMP/sc.json"
echo '{"frames":[{"tick":0,"interact":true}]}' > "$TMP/dock.json"
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
ok = s0["tick"] == 0 and s0["stock"] == {"bong_sung": 2, "ca_loc": 1}
print("## integration tick-0 stock:", s0["stock"], "OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
PY
  # smoke day --days 1 (thời gian chạy <= 20 s)
  t0=$(python3 -c 'import time;print(time.time())')
  python3 -m chonoi.headless --mode day --seed 7 --days 1 --ticks 30000 --snapshot-every 600 --out "$OUT/day-1.jsonl" || status=1
  t1=$(python3 -c 'import time;print(time.time())')
  echo "## day --days 1: $(tail -n 1 "$OUT/day-1.jsonl")" >> "$OUT/verify.txt"
  echo "## day --days 1 thời gian: $(python3 -c "print(round($t1-$t0,2))") s (yêu cầu <= 20 s)" >> "$OUT/verify.txt"
  # nhiều Ngày: cập bến ngay, mua Bình oxy trong Shop Ngày 1, kiểm cấp áp dụng ở Ngày 2
  echo '{"day":{"money":200,"earned":200},"gather":{"hold":["ca_loc","bong_sung","bong_sung"],"random_fish":false}}' > "$TMP/d.json"
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

[ $status -eq 0 ] && echo "## RESULT: PASS" >> "$OUT/verify.txt" || echo "## RESULT: FAIL" >> "$OUT/verify.txt"
tail -n 6 "$OUT/verify.txt"
exit $status
