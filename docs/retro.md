# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: dán nguyên văn Ticket-02 ngay từ đầu nên không phải làm lại luật như Phase 1; tách mỗi pha thành một sim nhỏ + `DaySim` điều phối giúp thêm Shop/pause mà không đụng luật gather/quan; skill `verify-phase` mở rộng cho P2 sinh đủ bằng chứng (`integration.*`, day smoke, nhiều Ngày, regression P1) bằng một lệnh.
- Điều tệ: test của chính agent viết sai 3 lần (đọc snapshot ở tick không được ghi, chạy quá thời gian bất tử) → mất thời gian phân biệt lỗi test với lỗi luật; một bug thật (cấp vừa mua không hiện ngay trong Shop) chỉ lộ ra nhờ test — chưa có ai xem giao diện bằng mắt, chưa đo FPS.
- 1 hành động cho Phase 3: trước khi gắn tag, mở `python3 -m chonoi.live` chơi trọn 1 Ngày trên trình duyệt 1280×720 và chụp màn hình vào `docs/proof/phase-3/` — người nhận: hainguyen312.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
