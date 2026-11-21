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
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
