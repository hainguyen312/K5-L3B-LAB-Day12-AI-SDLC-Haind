# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: dán nguyên văn Ticket-02 ngay từ đầu nên không phải làm lại luật như Phase 1; tách mỗi pha thành một sim nhỏ + `DaySim` điều phối giúp thêm Shop/pause mà không đụng luật gather/quan; skill `verify-phase` mở rộng cho P2 sinh đủ bằng chứng (`integration.*`, day smoke, nhiều Ngày, regression P1) bằng một lệnh.
- Điều tệ: test của chính agent viết sai 3 lần (đọc snapshot ở tick không được ghi, chạy quá thời gian bất tử) → mất thời gian phân biệt lỗi test với lỗi luật; một bug thật (cấp vừa mua không hiện ngay trong Shop) chỉ lộ ra nhờ test — chưa có ai xem giao diện bằng mắt, chưa đo FPS.
- 1 hành động cho Phase 3: trước khi gắn tag, mở `python3 -m chonoi.live` chơi trọn 1 Ngày trên trình duyệt 1280×720 và chụp màn hình vào `docs/proof/phase-3/` — người nhận: hainguyen312.

## Phase 3 (nhanh) — rút ra từ lần đổi kho
- Điều tốt: viết ADR-0002 (bảng tác động + thứ tự tích hợp) TRƯỚC khi code giúp đổi schema theo đúng thứ tự adapter → Lặn → Quán → day → test → HUD; helper `items()/stock()` trong test làm migration 40 test cũ nhanh và đồng nhất; dùng phân số cho độ tươi nên các ca ngưỡng 30 / floor giá đúng ngay lần chạy đầu.
- Điều tệ: breaking change làm đỏ 36 test cùng lúc — với nhóm đông người thì main sẽ hỏng nếu không có adapter v1.1/v1.2; JSONL làm tròn 3 chữ số suýt làm smoke bàn giao "so chính xác" không đạt (phát hiện nhờ chạy đúng ví dụ của ticket). Hành động retro P2 (chơi thử trên trình duyệt) vẫn chưa làm.
- 1 hành động cho Phase 4: hainguyen312 chơi thử 1 Ngày trên trình duyệt + chụp màn hình HUD (độ tươi, Thủy quái, Shop) vào `docs/proof/phase-4/` trước khi phát hành v1.0.0.

## Phase 4 (cuối)
- **Rà lại hành động Phase 2** ("hainguyen312 chơi thử 1 Ngày trên trình duyệt 1280×720 + chụp màn hình"): **làm được một phần, muộn 2 phase.** Lý do treo: mỗi phase hết giờ vào phần luật/test bắt buộc, hành động này không có test nào ép. Ở P4 đã làm bằng cách tự động: `tools/screenshot.py` chụp HUD bằng Chrome headless (cảnh báo sáng/tối ở chế độ thường + tương phản cao, menu, DayIntro) và benchmark render thật 30 s. Chính việc xem ảnh phát hiện 2 lỗi hiển thị mà 118 test không bắt được (nhãn oxy khó đọc, hộp cảnh báo che người chơi; ở tương phản cao dòng bình thường cũng bị tô vàng). **Còn vướng:** chưa có người chơi trọn 5 Ngày bằng tay — chuyển thành hành động tiếp theo.
- **Điều tốt:** dán nguyên văn ticket từ P2 trở đi → không làm lại luật; mỗi phase có skill `verify-phase N` sinh bằng chứng bằng 1 lệnh; ADR-0002 trước breaking change kho; phân số cho độ tươi; tìm ra Chrome headless chờ 60 s là do dò proxy (WPAD) chứ không phải game (load_ms 64 s → 0.5 s).
- **Điều tệ:** nhóm 1 người nên không có review chéo thật, mọi "review" là người đọc diff của AI; giao diện bị bỏ quên tới P4; tag các phase đều muộn so với mốc giờ của lab.
- **Số liệu:** commit theo người — hainguyen312: toàn bộ (20 commit P1–P3 + các commit P4, xem `git shortlog -sn`), không có người khác. Cách đọc code: người đọc lại diff của agent trước mỗi commit + test hộp đen + ảnh chụp HUD. Token ước tính (theo `docs/ai-usage-log.md`): P1 ~180k, P2 ~135k, P3 ~80k, P4 ~70k, tổng ~465k token cho hainguyen312.
- **Một lần AI sai và cách nhóm phát hiện:** P1 — khi chưa có PRD, agent tự đoán 11 luật thì 6 luật sai (boa `round` thay `floor`, khách rời trước interact, bắt trượt tốn hồi chiêu, tự thêm `no_table`…). Phát hiện bằng cách đặt từng dòng `docs/clarify.md` cạnh câu PRD tương ứng khi PRD được dán vào; sửa luật + test trong cùng lượt.
- **Nếu làm lại, đổi gì:** lấy nguyên văn đề trước khi viết dòng code đầu tiên; thêm một bước "chụp ảnh HUD" vào `verify-phase` ngay từ P2 để giao diện có bằng chứng như luật; gắn tag đúng mốc giờ dù chưa xong hết.
- **Hành động tiếp theo:** hainguyen312 chơi trọn 5 Ngày bằng tay trước buổi demo và quay video < 5 phút theo checklist demo.
