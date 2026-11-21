# Changelog

## Unreleased

## v1.0.0 / phase-4 — Ticket-04 Phát hành (Test Contract v1.3)
### Added
- `contract_version 1.3`, `bench_cmd` (`python3 -m chonoi.bench`), `soak_cmd` (`python3 -m chonoi.soak`) ở gốc manifest; gameplay/tuning/kho/JSONL giữ nguyên v1.2.
- Benchmark có render: server chơi thử + Chrome headless 1280×720, `?bench=1` đo requestAnimationFrame (làm nóng 3 s), xuất `avg_fps, p1_low_fps, frames, measured_s, load_ms`.
- Soak headless N Ngày bằng bot tất định; kế hoạch D1–D5 lặp ở Ngày 6–10; `soak.json {days, days_completed, crashes, results, duration_s}`.
- Cảnh báo chữ + biểu tượng: ⚠ Thủy quái gần, ⚠ Oxy sắp hết (< 25%), 😠 Khách sắp giận (kiên nhẫn < 25%); chế độ tương phản cao (H / `?contrast=1`).
- `tools/screenshot.py` (ảnh canvas qua Chrome headless) — bằng chứng HUD ở `docs/proof/phase-4/`.
- README v1.0.0 (yêu cầu môi trường, ≤ 3 lệnh, điều khiển, lệnh test/headless/bench/soak), `CREDITS.md`, `LICENSE`, `docs/release-notes-v1.0.0.md`.
- `tests/test_p4.py`; `verify-phase 4` (bench, soak x2, regression P1–P3).
### Fixed
- Nhãn thanh oxy khó đọc trên nền tối; hộp cảnh báo che người chơi giữa màn hình (phát hiện khi xem ảnh chụp).

## phase-3 — Ticket-03 "Mùa Nước Nổi" (Test Contract v1.2)
### ⚠ BREAKING CHANGE — kho cá thể có độ tươi
- File kho / `gather_end.inventory`: `{"items": {"ca_loc": 1}}` → `{"items": [{"id": "I1", "kind": "ca_loc", "fresh": 99.99}]}` (sắp theo id). **Kho đếm giờ trả mã 2.**
- Scenario: `gather.hold` và `quan.stock` là mảng cá thể `{id, kind, fresh}`; `customers[].reserved` là mảng id cá thể.
- JSONL: `hold`, `stock` (quán, Shop) là mảng cá thể; `cook_started.items`, `lost` là mảng cá thể; event mới `spoiled`.
- Giá món chốt theo độ tươi: `floor(giá niêm yết × TB fresh / 100)`; boa tính trên giá đã chốt.
### Cách cập nhật fixture
- `"hold": ["ca_loc", "bong_sung"]` → `"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "bong_sung", "fresh": 100}]` (trong test dùng `helpers.items("ca_loc", "bong_sung")`).
- `"stock": {"bong_sung": 2}` → mảng cá thể (`helpers.stock(bong_sung=2)` → I1, I2 fresh 100).
- `"reserved": {"bong_sung": 2}` → `"reserved": ["I1", "I2"]`; đơn không có món: `"reserved": []`.
- So kho: so `id`/`kind` chính xác, `fresh` với dung sai ±0.01 (hoặc so nguyên mảng với file vừa ghi).
### Added
- `chonoi/items.py` (cá thể, độ tươi chính xác bằng phân số), hao 0.5/s giỏ, 0.25/s kho quán, ngưỡng ươn 30, giữ lại khi hàng vừa ươn, `unfulfillable`.
- HUD độ tươi (thanh từng ô giỏ, ✗ hàng ươn, "tươi N%" trong kho quán/Shop).
- `tests/test_rules_p3.py` (20 test), `verify-phase 3` (ca ngưỡng 30, smoke bàn giao file, regression P1–P2).

## phase-2 — Ticket-02 (Test Contract v1.1)
### Added
- Số chuẩn v1.1: `contract_version 1.1`, N5/N6 (kèo nèo), cá kèo, B2, T2–T4, 6 món, `day_plan` D1–D5, `shop`.
- Cá bơi 1.5 m/s, phản xạ mép, đổi hướng theo seed mỗi 120 bước bơi; 8 đàn đầu ca, sinh mỗi 360 tick (trần 12, cách > 1 m, trọng số 40/30/30).
- Cá Sấu Năm Chèo (M1, M2 từ Ngày 3): patrol / chase / recoil, `monster_hit` (−1 Máu, bỏ nửa giỏ LIFO, bất tử 90), `faint` cause monster.
- `--mode day` (`chonoi/sim/day.py`), Shop (`chonoi/sim/shop.py`): nâng cấp oxygen/hp, `bought`/`buy_failed`/`shop_end`, `days_completed`, `days_complete`.
- Pause ở mọi mode (`paused`/`resumed`, `state: paused`, `tick` ≠ `sim_tick`).
- Cửa sổ chơi `python3 -m chonoi.live` (mặc định `day`): menu chính, DayIntro/EveningIntro/DayResult/Summary, Shop, menu pause, HUD theo Ticket-02.
- `tests/test_rules_p2.py` (29 test), `tests/test_live_day.py`; `verify-phase 2` (integration.*, day smoke, nhiều Ngày, regression P1).
### Changed
- 6 test P1 cập nhật theo luật v1.1 (lý do trong `docs/verification/phase-2.md`).

## phase-1 — PRD-0
### Added
- `gather` theo PRD-0 F: oxy, ngạt (lần đầu ở t+59), `choke`, ngất (`faint` bỏ giỏ LIFO, kho rỗng), `dive`/`surface`, hái nút ở mặt nước + mọc lại, bắt cá (yield, hồi chiêu chỉ khi bắt được), `hold_full {action, required, free}`.
- `quan` theo PRD-0 D/E/F: payload món `{order_id, dish_id, base_price}`, `order_status` (reserved/assigned/unfulfillable/served), lịch khách theo `phase_tick`, giữ chỗ, nấu/lấy/phục vụ, boa `floor` (phân số chính xác), trả tiền, rời bàn, đóng ca (`closing`), `quan_end`.
- Kiểm fixture quán mức luật (mục D) → mã 2.
- `tests/test_rules_p1.py` (36 test), skill `verify-phase`, `clarify-log`; bằng chứng `docs/proof/phase-1/`.
- HUD quán: hiện tên món trên bếp, kho khả dụng (tồn − giữ), thanh kiên nhẫn chỉ khi khách chờ.
### Changed
- `game.contract.json`: `team = "Haind"`, `team_size = 1` (ADR-0001). Không đổi tuning.
