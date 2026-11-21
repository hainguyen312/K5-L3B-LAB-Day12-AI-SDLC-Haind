# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

> Nguồn: PRD-0 (lab board, phát hành 08:02) mục D/E/F/G. Lúc đầu agent không đọc được PRD nên đặt 11 giả định
> (#1–#11). Có PRD rồi, nhóm đối chiếu lại từng dòng: **6/11 giả định sai** và đã sửa luật + test.
> Dòng ghi "PRD" = đã có câu trả lời chính thức. Dòng ghi "GIẢ ĐỊNH" = PRD chưa nói, nhóm tự chốt (skill `clarify-log`).

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 18:00 | Tick oxy chạm 0 có tính là 1 tick ngạt? | **PRD F:** có ("kể cả bước vừa chạm 0"); ngạt lần đầu ở t+59. Giả định ban đầu ĐÚNG. | PRD |
| 2 | 2026-11-21 18:00 | Lên mặt nước có xóa đếm ngạt? | **PRD F:** có; nổi lên đúng bước đáng lẽ ngạt thì hồi oxy, không ngạt. ĐÚNG. | PRD |
| 3 | 2026-11-21 18:05 | Giỏ không đủ chỗ cho cả mẻ cá? | **PRD F:** `hold_full`, giữ đàn, không thử đàn khác. ĐÚNG. | PRD |
| 4 | 2026-11-21 18:05 | Bắt trượt có tốn hồi chiêu? | **PRD F:** KHÔNG ("không có đàn trong tầm thì không có sự kiện bắt hay hồi chiêu"); `hold_full` cũng không đặt hồi. Giả định ban đầu **SAI → ĐÃ ĐỔI**. | PRD |
| 5 | 2026-11-21 18:10 | Ngất thì kho/sự kiện? | **PRD E/F:** bỏ giỏ LIFO; `faint {cause:"choke", lost:[kind… nhặt sau bỏ trước], hp:0}`; kho rỗng. Payload ban đầu **SAI → ĐÃ ĐỔI**. | PRD |
| 6 | 2026-11-21 18:15 | Thứ tự một tick của quán? | **PRD F:** timer → bếp → đi + 1 interact → khách trả tiền/rời theo id bàn (hết ca: dọn + `quan_end`) → khách mới. Ban đầu đặt "khách rời" TRƯỚC interact → **SAI → ĐÃ ĐỔI** (giờ phục vụ đúng tick kiên nhẫn về 0 vẫn hợp lệ). | PRD |
| 7 | 2026-11-21 18:15 | Khách chọn món? Hết bàn? | **PRD F:** chọn đều theo seed trong món đủ nguyên liệu khả dụng (tồn − giữ), duyệt id món theo Unicode; hết bàn thì **bỏ lượt, không event** (bỏ `no_table` agent tự thêm); `no_dish` data `{}`. **ĐÃ ĐỔI**. | PRD |
| 8 | 2026-11-21 18:20 | Trừ kho lúc nào? | **PRD F:** giữ chỗ khi gọi, tiêu đúng phần giữ khi bắt đầu nấu; khách rời nhả phần giữ, nguyên liệu đã dùng không hoàn. ĐÚNG. | PRD |
| 9 | 2026-11-21 18:20 | Bếp idle nấu đơn nào? | **PRD F:** đơn `reserved` cũ nhất theo `order_tick` rồi id bàn (ban đầu: id khách nhỏ nhất → **ĐÃ ĐỔI**). | PRD |
| 10 | 2026-11-21 18:25 | Boa? | **PRD F:** `floor(tiền món × tip_rate)` nếu kiên nhẫn còn (sau bước 1) / tối đa ≥ `tip_min_patience_ratio`; ban đầu dùng `round` → **SAI → ĐÃ ĐỔI**. Nhóm tính bằng phân số chính xác để tránh lỗi số thực. | PRD |
| 11 | 2026-11-21 18:25 | Interact chọn đối tượng? | **PRD F:** (khoảng cách, bếp trước bàn, id); đối tượng được chọn không tương tác được → bỏ lượt. ĐÚNG. | PRD |
| 12 | 2026-11-21 19:00 | Hết ca: khách đang ăn, khách chờ? | **PRD F:** khách ăn trả ngay (`paid` reason `closing`, kể cả vừa được giao), khách chờ rời `closing`, không trừ uy tín, rồi `quan_end`. | PRD |
| 13 | 2026-11-21 19:00 | Bếp idle có nấu khi tay đang cầm món không? | GIẢ ĐỊNH: có — PRD chỉ yêu cầu "tay trống" khi lấy món ở bếp ready, không ràng buộc lúc bắt đầu nấu. | Haind |
| 14 | 2026-11-21 19:00 | Khách ăn xong đúng tick hết ca: reason gì? | GIẢ ĐỊNH: `finished_eating` (timer ăn đã về 0 trước khi xét đóng ca). | Haind |
| 15 | 2026-11-21 19:05 | Snapshot khách trước khi chốt giá/boa? | GIẢ ĐỊNH: `base_price: null` tới lúc bắt đầu nấu, `tip: null` tới lúc phục vụ, `eat_ticks_left: 0` khi còn chờ (bộ đếm chưa kích hoạt = 0); khách đang ăn giữ nguyên `patience_ticks_left` lúc được phục vụ. | Haind |
| 16 | 2026-11-21 19:05 | Id khách mới? | GIẢ ĐỊNH: họ `C` (C1, C2…), nối sau hậu tố lớn nhất đã nạp; `order_id` = id khách (PRD D). | Haind |
| 17 | 2026-11-21 19:05 | "Cooldown L đặt ở t dùng lại từ t+L" tính theo tick nào? | GIẢ ĐỊNH: theo tick của event — bắt ở event tick t thì lần bắt kế tiếp sớm nhất có event tick t+L (L = 30). Test `test_cooldown_reuse_from_t_plus_L`. | Haind |
