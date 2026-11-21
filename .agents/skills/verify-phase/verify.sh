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

[ $status -eq 0 ] && echo "## RESULT: PASS" >> "$OUT/verify.txt" || echo "## RESULT: FAIL" >> "$OUT/verify.txt"
tail -n 6 "$OUT/verify.txt"
exit $status
