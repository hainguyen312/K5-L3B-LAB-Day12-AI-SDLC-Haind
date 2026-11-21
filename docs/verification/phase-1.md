# Ma trận truy vết Phase 1 (PRD-0)

Chạy lại toàn bộ: `bash .agents/skills/verify-phase/verify.sh 1` → [`docs/proof/phase-1/verify.txt`](../proof/phase-1/verify.txt) (68 test, tất định byte 2 mode, smoke 2 tiến trình, `RESULT: PASS`).
Test luật: [`tests/test_rules_p1.py`](../../tests/test_rules_p1.py) — tên lớp/hàm ghi ở cột "Cách kiểm chứng".

| AC (mục PRD) | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P1-01 B/E: `--ticks 0` → snapshot tick 0 + 1 dòng `end` | smoke `test_con_01_ticks_zero_and_end_line` | [verify.txt](../proof/phase-1/verify.txt) | đạt |
| AC-P1-02 E: cùng seed → JSONL + kho giống từng byte | smoke `test_con_02_deterministic_bytes`; `test_deterministic_full_run`, `test_full_shift_deterministic`; so byte 1200 tick trong script | [verify.txt](../proof/phase-1/verify.txt) (`determinism gather/quan: OK`) | đạt |
| AC-P1-03 B/C/D: cờ/dữ liệu sai, fixture mâu thuẫn → mã 2, không ghi đầu ra | smoke `test_con_03_*`, `test_scenario_out_of_domain_exit_2`; `QuanFixtures.test_rule_conflicts_exit_2` (13 ca: quá tồn, khác công thức, assigned không món, bếp+tay cùng đơn, liên kết thiếu, món không khớp đơn…) | [verify.txt](../proof/phase-1/verify.txt) | đạt |
| AC-P1-04 D: fixture hợp lệ (assigned/eating/unfulfillable/reserved có order_tick) | `QuanFixtures.test_valid_fixtures` | [verify.txt](../proof/phase-1/verify.txt) | đạt |
| AC-P1-05 F: bơi, ramp ≤ 6 tick, chặn mép, hướng 90° = xuống | smoke `Movement.*` | [verify.txt](../proof/phase-1/verify.txt) | đạt |
| AC-P1-06 F: oxy −1 dưới nước, +6 mặt nước (d ≤ 0.5), kẹp | `GatherOxygen.test_drain_refill_clamp` | [verify.txt](../proof/phase-1/verify.txt) | đạt |
| AC-P1-07 F: `oxygen_empty`, ngạt lần đầu ở t+59, −1 Máu | `test_oxygen_empty_then_first_choke_at_t_plus_59` | [verify.txt](../proof/phase-1/verify.txt) | đạt |
| AC-P1-08 F: nổi lên đúng bước đáng lẽ ngạt → không ngạt | `test_surface_on_choke_step_refills_no_choke` | [verify.txt](../proof/phase-1/verify.txt) | đạt |
| AC-P1-09 F/G: Máu 0 → bỏ giỏ LIFO, `faint`, `gather_end fainted`, kho `{}` | `test_faint_drops_hold_lifo_and_empty_inventory` | [verify.txt](../proof/phase-1/verify.txt) | đạt |
| AC-P1-10 E: `dive`/`surface` chỉ khi đổi phía | `test_dive_and_surface_once_per_crossing` | [verify.txt](../proof/phase-1/verify.txt) | đạt |
| AC-P1-11 F: hái ở mặt nước, đúng mép bán kính, hòa theo id, mọc lại, hái ngay khi về 0 | `GatherHarvest.test_prd_example_node_on_radius_edge`, `test_regrow_event_and_harvest_again`, `test_tie_breaks_by_id`, `test_no_harvest_underwater_or_far` | [verify.txt](../proof/phase-1/verify.txt) | đạt |
| AC-P1-12 F: bắt cá: yield, xóa đàn, hồi chiêu t+L; trượt không hồi; thiếu chỗ `hold_full` giữ đàn | `GatherCatch.*` | [verify.txt](../proof/phase-1/verify.txt) | đạt |
| AC-P1-13 F/G: cập bến ưu tiên ở bước cuối; hái ở bước cuối vẫn vào kho; hết giờ giữ giỏ | `test_dock_has_priority_and_writes_inventory`, `test_harvest_on_last_step_counts`; smoke `test_time_ends_gather_and_keeps_hold` | [kho.json](../proof/phase-1/kho.json), [gather-dock.jsonl](../proof/phase-1/gather-dock.jsonl) | đạt |
| AC-P1-14 G: smoke 2 tiến trình, quán nhận đúng kho; chạm `--ticks` không ghi kho; kho sai schema → 2 | `PrdSmokeG.test_two_process_smoke`; smoke `Integration.*` | [quan-from-kho.jsonl](../proof/phase-1/quan-from-kho.jsonl) (tick 0 `stock: {"bong_sung":2,"ca_loc":1}`) | đạt |
| AC-P1-15 F: lịch khách theo `phase_tick` (kể cả rút ngắn ca), giữ chỗ, `no_dish`, hết bàn bỏ lượt | `QuanCustomers.*` | [verify.txt](../proof/phase-1/verify.txt) | đạt |
| AC-P1-16 F: hết kiên nhẫn → `customer_left patience`, uy tín −0.5, nhả giữ chỗ | `test_patience_leave_releases_reservation` | [verify.txt](../proof/phase-1/verify.txt) | đạt |
| AC-P1-17 F: nấu → chín → lấy → phục vụ → ăn → trả tiền, boa `floor`, uy tín +0.2 | `QuanService.test_full_loop_cook_pick_serve_pay`, `test_tip_threshold_uses_patience_after_step_1` | [verify.txt](../proof/phase-1/verify.txt) | đạt |
| AC-P1-18 F: phục vụ đúng tick kiên nhẫn về 0 hợp lệ; sai đơn bỏ lượt; khách rời bỏ món, không hoàn nguyên liệu | `test_serve_on_patience_zero_tick_is_valid`, `test_wrong_order_in_hand_not_served`, `test_customer_leaving_discards_dish_no_refund`, `test_ready_ticks_increase_while_on_stove` | [verify.txt](../proof/phase-1/verify.txt) | đạt |
| AC-P1-19 F/E: hết ca: khách ăn trả `closing`, khách chờ rời không trừ uy tín, `quan_end`; ví dụ `end` của PRD (72 / 3.2 / 372) | `QuanClosing.*` | [verify.txt](../proof/phase-1/verify.txt) | đạt |
| AC-P1-20 DoD: HUD đọc được (thời gian, oxy, Máu, giỏ / kho khả dụng, món gọi, kiên nhẫn, bếp, tay, tiền, uy tín) | chơi thử `python3 -m chonoi.live`; `tests/test_live.py` | [verify.txt](../proof/phase-1/verify.txt) | đạt một phần — HUD hình khối của starter + vá kho khả dụng; chưa có đồ họa thật |
| AC-P1-21 DoD: fork chung, mỗi người ≥ 3 commit, tag `phase-1` trước 1:00 | `git log --author`, `git tag` | repo `hainguyen312/K5-L3B-LAB-Day12-AI-SDLC-Haind`, 6 commit P1 của hainguyen312, tag `phase-1` | đạt một phần: đủ commit + tag; **nhóm 1 người** (đề yêu cầu 4–6); tag gắn muộn so với mốc 1:00 của lab |

## Đánh giá ngắn
- **Đạt:** toàn bộ luật lõi PRD-0 mục D–G cho gather và quan; 68 test xanh; tất định byte; smoke 2 tiến trình.
- **Chưa đạt / rủi ro:** nhóm 1 người; 5 giả định (#13–#17 trong `docs/clarify.md`) PRD chưa nói rõ; HUD vẫn là hình khối tạm.
- **Chỉnh cho phase sau:** luôn dán nguyên văn PRD/ticket vào prompt agent trước khi code (Phase 1 mất công làm lại 6 giả định sai).
