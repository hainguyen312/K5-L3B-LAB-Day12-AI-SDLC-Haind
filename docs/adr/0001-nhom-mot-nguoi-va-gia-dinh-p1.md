# ADR-0001: Nhóm một người, sửa `team`/`team_size` trong contract và chốt giả định luật Phase 1

- Trạng thái: chấp nhận
- Ngày, người quyết: 2026-11-21, hainguyen312 (PO + Integrator)

## Bối cảnh
Đề yêu cầu nhóm 4–6 người; nhóm Haind chỉ có 1 người. `game.contract.json` bị khóa (AGENTS.md: không sửa khi chưa báo cả nhóm).
PRD-0 có chỗ mơ hồ (thứ tự xử lý trong tick, nhặt một phần mẻ, thời điểm trừ kho/tính boa).

## Các lựa chọn đã cân nhắc
1. Giữ `team_size: 4` → sai với TEAM.md, `check_team.py` báo lệch.
2. Đặt `team_size: 1` → đúng thực tế; `check_team.py` vẫn cảnh báo "4–6 người" (cảnh báo, CI không chặn).

## Quyết định
Chọn 2: `team: "Haind"`, `team_size: 1`. Không đổi tuning. Các câu hỏi luật ghi ở `docs/clarify.md` (#1–#12 đã có trả lời từ PRD-0; #13–#17 là giả định của nhóm) và khóa bằng test.

## Hệ quả
| Module / file | Tác động |
|---|---|
| `game.contract.json` | chỉ đổi `team`, `team_size` |
| `tools/check_team.py` | cảnh báo số thành viên (đã biết) |
| `chonoi/sim/*`, `tests/test_rules_p1.py` | hành vi theo giả định; PO đổi thì sửa luật + test cùng commit |
