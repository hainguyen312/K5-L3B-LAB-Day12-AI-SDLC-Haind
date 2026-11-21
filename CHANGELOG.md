# Changelog

## Unreleased

## phase-1 — PRD-0
### Added
- `gather` theo PRD-0 F: oxy, ngạt (lần đầu ở t+59), `choke`, ngất (`faint` bỏ giỏ LIFO, kho rỗng), `dive`/`surface`, hái nút ở mặt nước + mọc lại, bắt cá (yield, hồi chiêu chỉ khi bắt được), `hold_full {action, required, free}`.
- `quan` theo PRD-0 D/E/F: payload món `{order_id, dish_id, base_price}`, `order_status` (reserved/assigned/unfulfillable/served), lịch khách theo `phase_tick`, giữ chỗ, nấu/lấy/phục vụ, boa `floor` (phân số chính xác), trả tiền, rời bàn, đóng ca (`closing`), `quan_end`.
- Kiểm fixture quán mức luật (mục D) → mã 2.
- `tests/test_rules_p1.py` (36 test), skill `verify-phase`, `clarify-log`; bằng chứng `docs/proof/phase-1/`.
- HUD quán: hiện tên món trên bếp, kho khả dụng (tồn − giữ), thanh kiên nhẫn chỉ khi khách chờ.
### Changed
- `game.contract.json`: `team = "Haind"`, `team_size = 1` (ADR-0001). Không đổi tuning.
