# Changelog

## Unreleased

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
