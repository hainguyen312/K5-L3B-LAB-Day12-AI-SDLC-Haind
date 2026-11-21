---
name: verify-phase
description: Chạy toàn bộ kiểm chứng của một phase (unittest, tất định byte, luồng gather->kho->quan) và lưu bằng chứng vào docs/proof/phase-N/. Dùng trước khi gắn tag phase-N hoặc sau khi agent sửa luật.
---

# verify-phase

## Khi nào dùng
- Trước khi gắn tag `phase-N` (bắt buộc).
- Sau mỗi lần agent sửa `chonoi/sim/*`, `chonoi/scenario.py` hoặc `game.contract.json`.

## Cách chạy
```bash
bash .agents/skills/verify-phase/verify.sh <N>      # ví dụ: 1
```
Script ghi vào `docs/proof/phase-N/`:
- `verify.txt` — log unittest đầy đủ, kết quả tất định (hash 16 ký tự), kho tích hợp, dòng `end` của quán, `RESULT: PASS|FAIL`.
- `gather-dock.jsonl`, `kho.json`, `quan-from-kho.jsonl` — đầu ra thật của luồng tích hợp.

Mã thoát khác 0 = có bước hỏng → KHÔNG gắn tag, sửa luật trước.

## Sau khi chạy
1. Mở `docs/verification/phase-N.md`, cập nhật cột "Bằng chứng" trỏ tới file trong `docs/proof/phase-N/`.
2. Ghi kết quả (đạt / chưa đạt) trung thực; test đỏ thì ghi lý do, không sửa test cho xanh.
