# Ma trận truy vết Phase 2 (Ticket-02, Test Contract v1.1)

Chạy lại toàn bộ: `bash .agents/skills/verify-phase/verify.sh 2` → [`docs/proof/phase-2/verify.txt`](../proof/phase-2/verify.txt) (98 test, tất định byte, smoke tích hợp, smoke day, nhiều Ngày, regression P1, `RESULT: PASS` ở commit `844d867`).
Test: [`tests/test_rules_p2.py`](../../tests/test_rules_p2.py), [`tests/test_live_day.py`](../../tests/test_live_day.py); regression [`tests/test_rules_p1.py`](../../tests/test_rules_p1.py), [`tests/test_smoke_p1.py`](../../tests/test_smoke_p1.py).

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P2-01 contract 1.1, số chuẩn, 6 nguyên liệu, 6 món, N5/N6, B2, T2–T4, day_plan D1–D5 | `StandardData.test_contract_v11_standard_numbers` (36 cặp loài–vị trí, 30 vị trí hình học, số ô D1–D5) | [verify.txt](../proof/phase-2/verify.txt) | đạt |
| AC-P2-02 đầu ca 8 đàn ở 8 điểm khác nhau, theo seed | `Fish.test_initial_8_schools_at_distinct_spawn_points` | verify.txt | đạt |
| AC-P2-03 cá bơi 1.5 m/s, phản xạ mép x/d, chạm góc đảo cả hai, đổi hướng theo seed ở bước bơi 120 | `test_swim_speed_and_age`, `test_reflect_x_edge_and_depth_band`, `test_turn_by_seed_at_swim_step_120` | verify.txt | đạt |
| AC-P2-04 sinh mỗi 360 tick sau khi bơi, trần 12, điểm hợp lệ; random_fish=false tắt bơi/sinh; bắt theo vị trí trước khi bơi | `test_spawn_every_360_after_swim_cap_and_clearance`, `test_random_fish_false_static_no_spawn`, `test_catch_uses_position_before_swim`, `test_ca_keo_yield_and_keo_neo_node` | verify.txt | đạt |
| AC-P2-05 Cá Sấu: bố trí Ngày 1 (M1), patrol 1 m/s đổi waypoint, chase 3 m/s khi d ≥ 10 và ≤ 10 m, về patrol khi lên d < 10 | `Crocodile.test_default_layout_day1_and_patrol`, `test_chase_when_deep_and_close_then_exit_when_shallow` | verify.txt | đạt |
| AC-P2-06 hit: −1 Máu, bỏ floor(giỏ/2) LIFO, bất tử 90, recoil 60 bước × 2/60 m, trùng tâm +x, không hit khi nông/bất tử | `test_hit_loses_hp_drops_half_lifo_invuln_recoil`, `test_same_center_recoils_plus_x`, `test_no_hit_when_shallow_or_invulnerable` | verify.txt | đạt |
| AC-P2-07 Máu 0 do chạm → faint cause monster (lost = phần giỏ còn lại), kho rỗng | `test_monster_faint_lists_remaining_hold` | verify.txt | đạt |
| AC-P2-08 M2 từ Ngày 3; Máu hồi đầy mỗi Ngày; fixture monsters sai → mã 2 | `Day.test_three_days_m2_from_day3_and_hp_refill`, `Crocodile.test_bad_monster_fixture_exit_2` | verify.txt | đạt |
| AC-P2-09 quán 4 bàn (bàn trống id nhỏ nhất), lịch 120 + 900k, B2 nấu được, quán riêng dùng 6 món | `QuanV11.*` | verify.txt | đạt |
| AC-P2-10 trong day, khách chỉ gọi món của kế hoạch | `test_dock_handover_plan_filter_and_shop_buy_applies_next_day` | verify.txt | đạt |
| AC-P2-11 `--mode day`: day_start → day_plan → phase_start(gather) ở tick 0; gather_end/phase_start(quan), quan_end/phase_start(shop) cùng tick; shop_end(time) sau 600; end `days_complete`, `days_completed`; Ngày ≤ 22.200 tick, chạy ≤ 20 s | `Day.test_one_day_phase_sequence` + script | [day-1.jsonl](../proof/phase-2/day-1.jsonl), verify.txt (0.54 s) | đạt |
| AC-P2-12 Shop: bought / buy_failed (funds, max_level, unknown), đủ đúng giá vẫn mua, trừ money giữ earned, cấp hiển thị ngay, áp dụng từ Ngày kế (oxy 2.700 tick) | `test_dock_handover_plan_filter_and_shop_buy_applies_next_day`, `test_buy_max_level_unknown_and_exact_price` + script | [days-2-upgrade.jsonl](../proof/phase-2/days-2-upgrade.jsonl) | đạt |
| AC-P2-13 ngất vẫn mở quán với kho rỗng | `test_faint_still_opens_quan_with_empty_stock` | verify.txt | đạt |
| AC-P2-14 pause: paused/resumed, chỉ tăng tick ngoài, timer + lịch đứng yên, bỏ cạnh hành động, state `paused` | `Pause.*`, `test_live_day` (pause trong cửa sổ chơi) | verify.txt | đạt |
| AC-P2-15 scenario day: money ≤ earned, khai cả hai, cấm quan.stock/reputation, day_plan tính lại ingredients, mâu thuẫn lúc mở quán → 2; CLI `--days` 1..5 chỉ với day | `test_day_scenario_conflicts_exit_2`, `test_runtime_conflict_at_quan_open_exit_2`, `test_cli_days_rules` | verify.txt | đạt |
| AC-P2-16 tất định byte (gather, quan, day) | script + `test_day_deterministic` | verify.txt | đạt |
| AC-P2-17 smoke tích hợp gather --inventory-out → quan --inventory, kho tick 0 | script | [integration-gather.jsonl](../proof/phase-2/integration-gather.jsonl), [integration-kho.json](../proof/phase-2/integration-kho.json), [integration-quan.jsonl](../proof/phase-2/integration-quan.jsonl) | đạt |
| AC-P2-18 regression P1 với số chuẩn | `tests.test_smoke_p1` + `tests.test_rules_p1` | [regression-p1.txt](../proof/phase-2/regression-p1.txt) | đạt — 6 test đổi vì luật mới, lý do bên dưới |
| AC-P2-19 cửa sổ chơi: menu (Chơi/Thoát), DayIntro (tự qua 4 s), EveningIntro, DayResult, Shop, Summary, pause (Tiếp tục/Về menu) | `tests/test_live_day.py` (menu → intro → chơi → pause), `node --check` client | verify.txt | đạt một phần — luồng và API đã test; **chưa xem bằng mắt trên trình duyệt** |
| AC-P2-20 HUD sáng/tối theo danh sách Ticket-02 mục 2, chữ ≥ 18 px, ≥ 30 FPS ở 1280×720 | đọc code `chonoi/web/index.html` (hàm `text()` kẹp cỡ chữ ≥ 18) | — | **chưa kiểm chứng**: chưa đo FPS, chưa chụp màn hình |
| AC-P2-21 DoD: commit từng người, tag `phase-2` trước 1:55 | `git log --author`, `git tag` | 7 commit P2 của hainguyen312 (`b5391ed`…), tag `phase-2`; bằng chứng chạy ở `844d867` | đạt một phần: đủ commit + tag; **nhóm 1 người**; tag muộn so với mốc 1:55 của lab |

## Test cũ đổi vì luật mới (Ticket-02: "ghi lý do nếu test cũ cần cập nhật")
| Test | Lý do |
|---|---|
| `test_smoke_p1.test_gather_snapshot_has_gather_fields` | v1.1 đầu ca có `fish_initial = 8` đàn (P1: 6) |
| `test_smoke_p1.test_con_03_bad_input_exit_2` | v1.1 `attack` là nút hợp lệ (bỏ qua khi chưa bật mở rộng) → thay bằng nút lạ `dash`, thêm kiểm `attack`/`photo` → mã 0 |
| `test_smoke_p1.test_con_03_old_and_future_modes_rejected` | `day` đã là mode hợp lệ → thay bằng `night` |
| `test_python_starter_units.test_catch_is_a_v10_button_and_attack_is_not` | đổi thành `test_v11_buttons_accepted_unknown_rejected` (nút v1.1 + `buy`) |
| `test_rules_p1.test_cooldown_reuse_from_t_plus_L`, `test_regrow_event_and_harvest_again` | cá fixture giờ bơi / có `fish_spawned` → thêm `random_fish: false` |
| `test_rules_p1.test_no_table_skips_silently`, `test_rule_conflicts_exit_2` | quán có 4 bàn và bếp B2 thật → lấp đủ 4 bàn; dùng id bếp `B9` |

## Đánh giá ngắn
- **Đạt:** toàn bộ lõi Test Contract v1.1 chạy headless, 98 test xanh, một Ngày 0.54 s.
- **Chưa đạt / rủi ro:** chưa kiểm hiển thị/FPS bằng trình duyệt; 13 giả định mới (#18–#30), rủi ro lớn nhất là cách rút số ngẫu nhiên khi sinh cá (#19, test ẩn có thể dựng nhánh bằng fixture nên ít ảnh hưởng) và thứ tự phát hiện của Cá Sấu (#21); không làm mục mở rộng nào (nhóm 1 người, không bắt buộc).
