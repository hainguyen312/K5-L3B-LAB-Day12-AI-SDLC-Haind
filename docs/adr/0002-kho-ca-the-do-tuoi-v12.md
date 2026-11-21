# ADR-0002: Kho cá thể có độ tươi (Test Contract v1.2, Change Request "Mùa Nước Nổi")

- Trạng thái: chấp nhận
- Ngày, người quyết: 2026-11-21, hainguyen312 (PO + Integrator)

## Bối cảnh
Ticket-03 [THAY THẾ] kho đếm `{"items": {kind: n}}` bằng kho cá thể `{"items": [{id, kind, fresh}]}`; giữ chỗ theo id;
giá theo độ tươi. Đây là breaking change ảnh hưởng mọi đầu bàn giao (file kho, `day`, scenario, JSONL, HUD, test).

## Các lựa chọn đã cân nhắc
1. **Hỗ trợ song song v1.1 + v1.2 qua adapter** rồi bật v1.2 sau: an toàn khi nhiều người làm song song, nhưng v1.2 bắt buộc
   trả mã 2 cho kho đếm nên adapter chỉ sống trong lúc chuyển.
2. **Chuyển thẳng sang v1.2 trong một nhánh tích hợp** (nhóm 1 người, không có người khác đang dựa vào v1.1): ít mã thừa.
3. Độ tươi dạng float vs **phân số chính xác**: float có thể lệch ở ngưỡng 30 và phép floor giá.

## Quyết định
- Chọn 2 + 3. Module chung `chonoi/items.py`: `fresh` là `Fraction` (hao 1/120 mỗi tick ở giỏ, 1/240 ở quán);
  khi đọc số thập phân sát lưới 1/240 (< 1e-6 đơn vị) thì đưa về lưới → ghi file rồi đọc lại giữ đúng giá trị và nhánh ngưỡng.
- `fresh` xuất JSONL KHÔNG làm tròn 3 chữ số (`ExactFloat`) để snapshot quán khớp chính xác file kho.
- Id cá thể dùng `IdAllocator` chung của lượt (họ `I`) → tăng xuyên pha và Ngày.

## Thứ tự tích hợp (giữ main chạy được)
1. `items.py` + `inventory.py` (schema, đọc/ghi) + contract 1.2 → 2. `gather.py` (giỏ cá thể, hao, spoiled) →
3. `quan.py` (kho cá thể, giữ theo id, giữ lại khi ươn, giá theo tươi) → 4. `shop.py`, `day.py` (bàn giao trong bộ nhớ, id mới
cho mẫu hold từ Ngày 2) → 5. migrate test P1–P2 + test P3 → 6. HUD → 7. `verify-phase 3`. Chỉ commit/push sau bước 7 (cả bộ xanh).

## Hệ quả — bảng tác động
| Module | File thực tế | Test giữ / đổi / thêm | Người |
|---|---|---|---|
| Adapter / schema | `chonoi/items.py` (mới), `chonoi/inventory.py`, `chonoi/jsonl.py` (`ExactFloat`), `game.contract.json`, `chonoi/contract.py`, `chonoi/scenario.py` | đổi: `test_smoke_p1.test_inv_*`, `test_inventory_*`; thêm: `test_rules_p3.FileHandover`, `Contract12` | hainguyen312 |
| Lặn | `chonoi/sim/gather.py` | đổi: fixture `hold` trong `test_rules_p1/p2` (cá thể, `lost` là cá thể); thêm: `GatherFreshness` | hainguyen312 |
| Quán | `chonoi/sim/quan.py` | đổi: `stock`/`reserved` trong `test_rules_p1/p2`, giá kỳ vọng tính theo tươi (40 → 39, 200 → 199); thêm: `QuanFreshness` | hainguyen312 |
| day / Shop | `chonoi/sim/day.py`, `chonoi/sim/shop.py` | đổi: `test_rules_p2.Day.*` (id Ngày 2 = I4…); thêm: `DayFreshness` | hainguyen312 |
| HUD | `chonoi/web/index.html` | giữ: `test_live`, `test_live_day` | hainguyen312 |
| QA | `.agents/skills/verify-phase/verify.sh`, `tests/helpers.py` (`items`, `stock`, `kinds`, `kind_counts`) | regression P1–P2 chạy lại trong `verify.sh 3` | hainguyen312 |
