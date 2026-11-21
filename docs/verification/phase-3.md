# Ma trận truy vết Phase 3 (Ticket-03 "Mùa Nước Nổi", Test Contract v1.2)

Chạy lại toàn bộ: `bash .agents/skills/verify-phase/verify.sh 3` → [`docs/proof/phase-3/verify.txt`](../proof/phase-3/verify.txt) (118 test, tất định byte, smoke ngưỡng 30, smoke bàn giao file, smoke tích hợp, day, nhiều Ngày, regression P1 + P2, `RESULT: PASS` ở commit `20983f0`).
Test mới: [`tests/test_rules_p3.py`](../../tests/test_rules_p3.py). Tác động + thứ tự tích hợp: [ADR-0002](../adr/0002-kho-ca-the-do-tuoi-v12.md).

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P3-01 contract 1.2, khối `freshness` {100, 0.5, 0.25, 30} | `Contract12.test_version_and_freshness_block` | verify.txt | đạt |
| AC-P3-02 giỏ hao 0.5/s, kẹp 0, `spoiled` đúng một lần, cùng tick theo id; ca kiểm ngưỡng của ticket (fresh 30 → spoiled tick 1) | `GatherFreshness.test_prd_threshold_example_spoils_on_first_step`, `test_decay_half_per_second_clamped_and_spoiled_once_by_id` + script | [threshold-30.jsonl](../proof/phase-3/threshold-30.jsonl) | đạt |
| AC-P3-03 hàng mới fresh 100, hao từ bước sau; id I1, I2… theo thứ tự vào giỏ, tiếp sau id fixture, tăng xuyên Ngày; hàng ươn vẫn chiếm ô; pause dừng hao | `test_new_items_fresh_100_ids_continue_after_fixture`, `test_spoiled_still_occupies_slot`, `test_pause_stops_decay`, `DayFreshness.test_ids_continue_across_days` | verify.txt | đạt |
| AC-P3-04 file kho cá thể sắp theo id, ghi một lần, ngất ghi `[]`, `gather_end.inventory` cùng schema; smoke bàn giao so chính xác id/kind/fresh; ngưỡng giữ nguyên qua ghi–đọc | `FileHandover.*` + script | [handover-kho.json](../proof/phase-3/handover-kho.json), [handover-quan.jsonl](../proof/phase-3/handover-quan.jsonl), [integration-*](../proof/phase-3/integration-kho.json) | đạt |
| AC-P3-05 kho đếm / sai schema / kind lạ / id trùng / fresh ngoài miền → mã 2 (file và scenario) | `test_count_inventory_and_bad_items_exit_2`, smoke `test_inv_bad_schema_exit_2` | verify.txt | đạt |
| AC-P3-06 kho quán hao 0.25/s kể cả hàng đang giữ; hàng ươn không dùng nấu | `QuanFreshness.test_stock_decays_quarter_per_second_including_reserved`, `test_spoiled_not_cookable_no_dish` | verify.txt | đạt |
| AC-P3-07 giữ theo id: tươi nhất, hòa theo id, bỏ qua hàng ươn; fixture `reserved` sai (id không có, hàng ươn, khác công thức, dùng chung) → 2 | `test_reserve_freshest_tie_by_id_and_skip_spoiled`, `test_rules_p1.QuanFixtures.*` | verify.txt | đạt |
| AC-P3-08 phần giữ có hàng vừa ươn → nhả, giữ lại đúng một lần; thiếu → `unfulfillable`, khách chờ tiếp; nhiều đơn theo order_tick rồi id bàn | `test_rereserve_once_when_reserved_item_spoils`, `test_rereserve_fails_unfulfillable_by_order_tick_then_table` | verify.txt | đạt |
| AC-P3-09 giá chốt floor(giá × TB fresh / 100) chính xác; `cook_started.items` cá thể sắp kind rồi id; boa floor(giá đã chốt × 0.2) | `test_price_by_freshness_exact_floor_and_tip` (50 → 30, không 29), `test_cook_items_sorted_kind_then_id_mean_price`, `test_tip_on_fresh_price` | verify.txt | đạt |
| AC-P3-10 `day`: bàn giao cùng tick không hao thêm, quán hao từ bước sau, Shop không hao, mẫu hold Ngày kế cấp id mới | `DayFreshness.test_day_handover_no_extra_decay_and_shop_no_decay`, `test_rules_p2.Day.test_dock_handover…` | [days-2-upgrade.jsonl](../proof/phase-3/days-2-upgrade.jsonl) | đạt |
| AC-P3-11 HUD hiện độ tươi / hàng ươn (thanh dưới mỗi ô giỏ, ✗ khi < 30, "tươi N%" + "ươn N" ở kho quán/Shop/EveningIntro) | đọc code `chonoi/web/index.html` (`freshSummary`), `node --check`, `test_live*` | — | **đạt một phần**: chưa xem bằng mắt trên trình duyệt |
| AC-P3-12 regression P1–P2 còn hiệu lực | script (`regression-p1.txt`, `regression-p2.txt`) | [regression-p1.txt](../proof/phase-3/regression-p1.txt), [regression-p2.txt](../proof/phase-3/regression-p2.txt) | đạt — fixture đổi sang cá thể, lý do bên dưới |
| AC-P3-13 DoD: commit + tag `phase-3` trước 2:30 | `git log --author`, `git tag` | 7 commit P3 của hainguyen312 (`806501d`…), tag `phase-3`; bằng chứng chạy ở `20983f0` | đạt một phần: đủ commit + tag theo thứ tự tích hợp ADR-0002; **nhóm 1 người**; tag muộn so với mốc 2:30 |

## Test cũ thay bởi luật mới
| Test | Thay đổi | Lý do (Ticket-03 [THAY THẾ]) |
|---|---|---|
| `test_smoke_p1` (`test_time_ends…`, `test_inv_01_*`, `test_inv_bad_schema_exit_2`, `test_inventory_*`, `test_scenario_out_of_domain_exit_2`) | fixture `hold`/`stock`/file kho dạng cá thể; so file kho bằng id/kind + fresh ±0.01; thêm ca kho đếm → 2 | kho đếm → kho cá thể |
| `test_python_starter_units.test_session_steps_gather_and_dock` | `hold` dạng cá thể | như trên |
| `test_rules_p1` (gather, quán, fixture) | `lost` là cá thể theo LIFO; `reserved` là mảng id; giá vòng phục vụ 40 → 39, boa 8 → 7 | giữ theo id; giá theo tươi (nấu sau 1 lần hao 1/240) |
| `test_rules_p2` (Cá Sấu, quán v1.1, day) | `lost` cá thể; giá `lau_mam` ở B2 200 → 199; id hold Ngày 2 = I4…I6 | giá theo tươi; id mới cho mẫu hold từ Ngày 2 |

## Đánh giá ngắn
- **Đạt:** toàn bộ lõi v1.2, 118 test xanh; ca kiểm ngưỡng và smoke bàn giao của ticket chạy đúng y ví dụ.
- **Chưa đạt / rủi ro:** HUD chưa kiểm bằng mắt (hành động retro P2 vẫn treo); thứ tự id trong `reserved` (#33) và cách xử lý nhiều đơn ươn cùng lúc (#34) là giả định; không làm mở rộng dòng lũ / khách đặt trước.
