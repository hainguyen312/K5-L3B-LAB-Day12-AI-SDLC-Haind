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
| 18 | 2026-11-21 21:00 | `attack`/`photo` khi nhóm chưa bật mở rộng? `buy` weapon/net/vendor? | **Ticket-02 4.2:** nút đúng kiểu mà mở rộng chưa bật thì bỏ qua (mã 0). GIẢ ĐỊNH: lệnh `buy` của mở rộng chưa bật coi là "lệnh không hỗ trợ" → `buy_failed` reason `unknown`. Test smoke P1 "attack → mã 2" đổi theo v1.1. | Ticket-02 + Haind |
| 19 | 2026-11-21 21:00 | Chọn loài/điểm/hướng "theo seed" cụ thể thế nào? | GIẢ ĐỊNH: luồng RNG `fish_spawn`: duyệt loài theo id (ca_keo, ca_linh, ca_loc), `r = random() × tổng trọng số loài còn điểm`; điểm chọn đều trong danh sách (x, d) đã sắp; hướng = `random() × 360`. Đổi hướng dùng luồng `fish_turn`, duyệt cá theo id. 8 đàn đầu ca dùng cùng thủ tục (khoảng cách > 1 m → 8 điểm khác nhau), không phát `fish_spawned`. | Haind |
| 20 | 2026-11-21 21:05 | Mua khi đã tối đa VÀ thiếu tiền: reason nào? | GIẢ ĐỊNH: `max_level` (xét cấp trước tiền). | Haind |
| 21 | 2026-11-21 21:05 | Cá Sấu xét phát hiện trước hay sau khi di chuyển? | GIẢ ĐỊNH: xét bằng khoảng cách ĐẦU bước của con đó (người chơi đã bơi xong), đổi trạng thái rồi di chuyển theo trạng thái mới ngay trong bước. Đuổi không vượt quá người chơi (bước = min(3/60, khoảng cách)). | Haind |
| 22 | 2026-11-21 21:10 | Con vừa hết recoil có gây hit cùng bước? | **Ticket-02 1.2:** không — "xét phát hiện/chạm từ bước kế". | Ticket-02 |
| 23 | 2026-11-21 21:10 | Cá fixture nằm ngoài dải độ sâu của loài mà cờ bơi bật? | GIẢ ĐỊNH: bước bơi đầu kéo vị trí vào miền (x ∈ fish_x, d ∈ dải loài) rồi mới bơi; không trả mã 2 để fixture P1 cũ vẫn chạy. | Haind |
| 24 | 2026-11-21 21:15 | Trong `day`, `gather.hold` áp cho Ngày 1 hay mọi Ngày? | **Ticket-02 4.3:** "day nhận gather và quan làm mẫu khởi tạo mỗi Ngày" → áp mọi Ngày. | Ticket-02 |
| 25 | 2026-11-21 21:15 | DayIntro/EveningIntro/DayResult có tốn tick headless? | GIẢ ĐỊNH: không — headless chỉ có pha gather/quan/shop (phase snapshot chỉ có 3 giá trị) và 1 Ngày tối đa đúng 22.200 tick = 10.800 + 10.800 + 600. Các màn hình chỉ có trong cửa sổ chơi. | Haind |
| 26 | 2026-11-21 21:20 | Mâu thuẫn fixture quán phát hiện lúc mở quán trong `day`? | **Ticket-02 4.3:** mã 2. Vì chỉ phát hiện được giữa lượt nên JSONL đã ghi một phần; nhóm vẫn trả mã 2. | Ticket-02 |
| 27 | 2026-11-21 21:20 | Có ép thêm snapshot ở tick đổi pha không? | GIẢ ĐỊNH: không; snapshot vẫn theo quy tắc tick 0 / bội số `--snapshot-every` / tick dừng. Nếu trùng tick đổi pha thì ghi pha mới với `phase_tick: 0`. | Haind |
| 28 | 2026-11-21 21:25 | Bước `resumed` có xử lý cạnh hành động cùng frame không? | GIẢ ĐỊNH: có — "chạy gameplay ngay trong bước đó" nên interact/catch/buy cùng frame được xử lý. | Haind |
| 29 | 2026-11-21 21:25 | HUD "Thủy quái!" khi nào? | GIẢ ĐỊNH: có con đang `chase`, hoặc người chơi ở d ≥ 10 và cách một con ≤ 12 m (viền tím cùng lúc). | Haind |
| 30 | 2026-11-21 21:30 | Shop có lệnh mua cùng frame `shop_done`? | **Ticket-02 4.5:** xử lý một buy trước cạnh shop_done, kể cả bước cuối. | Ticket-02 |
| 31 | 2026-11-21 22:00 | Độ tươi tính bằng số thực hay đơn vị nguyên? Ghi file bao nhiêu chữ số? | GIẢ ĐỊNH/thiết kế (ADR-0002): phân số chính xác trong mô phỏng; file kho ghi `repr` của float (đủ để đọc lại); khi đọc, giá trị sát lưới 1/240 được đưa về lưới. Kiểm bằng `test_file_sorted_by_id_and_threshold_survives_round_trip`. | Haind |
| 32 | 2026-11-21 22:00 | JSONL làm tròn 3 chữ số — áp cho fresh? | **Ticket-03:** smoke "so chính xác … độ tươi của snapshot quán với file" → nhóm KHÔNG làm tròn `fresh` trong JSONL (các số khác vẫn 3 chữ số). | Ticket-03 + Haind |
| 33 | 2026-11-21 22:05 | Thứ tự id trong `customers[].reserved` ở snapshot? | GIẢ ĐỊNH: sắp theo id (khóa tiền tố + hậu tố số). Khi giữ chỗ, chọn từng loại theo thứ tự id loại (Unicode), mỗi loại tươi nhất rồi id nhỏ. | Haind |
| 34 | 2026-11-21 22:05 | Nhiều đơn bị ảnh hưởng khi hàng ươn: nhả hết rồi mới giữ lại, hay từng đơn? | GIẢ ĐỊNH: từng đơn theo order_tick rồi id bàn — nhả phần giữ của đơn đó rồi thử giữ lại ngay; đơn sau thấy kho sau khi đơn trước đã giữ (`test_rereserve_fails_unfulfillable_by_order_tick_then_table`). | Haind |
| 35 | 2026-11-21 22:10 | Cá thể đúng fresh 30 có được giữ chỗ / dùng nấu không? | **Ticket-03:** ươn là fresh < 30 → đúng 30 vẫn dùng được. Fixture giữ hàng fresh 30 hợp lệ; sang bước sau mới ươn. | Ticket-03 |
| 36 | 2026-11-21 22:10 | Thứ tự trong bước 1 gather giữa hồi nút và hao tươi? | GIẢ ĐỊNH: theo câu Ticket-03 "đồng hồ, cooldown, hồi nút và độ tươi" → `node_regrown` trước `spoiled` trong cùng tick. | Haind |
| 37 | 2026-11-21 22:15 | `hold_count`/sức chứa có tính hàng ươn? | **Ticket-03:** hàng ươn vẫn chiếm ô → có tính. | Ticket-03 |
