# Quán Ăn Chợ Nổi v1.0.0 — nhóm Haind

Bản phát hành cuối của Lab Day 12 (AI SDLC). Út Sen lặn bắt cá, hái rau trên sông Chín Khúc vào buổi sáng, tối nấu và
phục vụ khách trên nhà bè của Má Tư, cuối ngày mua nâng cấp cho lần lặn sau — 5 Ngày.

## Điểm mới (so với từng phase)
- **Phase 1 (PRD-0):** lặn & hái (oxy, ngạt, Máu, ngất, hái nút, bắt cá, giỏ), mở quán (khách, giữ chỗ, bếp, bưng, boa, uy tín), bàn giao qua file kho.
- **Phase 2 (Ticket-02, v1.1):** số chuẩn, cá bơi/sinh theo seed, Cá Sấu Năm Chèo, 2 bếp / 4 bàn / 6 món, chế độ `day` với kế hoạch D1–D5, Shop nâng cấp oxy/Máu, pause, menu + màn hình ngày + HUD.
- **Phase 3 (Ticket-03, v1.2, breaking):** kho cá thể có độ tươi (hao, ươn, giữ chỗ theo id, giá theo tươi), HUD độ tươi.
- **Phase 4 (Ticket-04, v1.3):** cảnh báo dễ nhận biết (⚠ Thủy quái gần, ⚠ Oxy sắp hết, 😠 Khách sắp giận) + chế độ tương phản cao (phím H), `bench_cmd` (benchmark có render qua Chrome headless), `soak_cmd` (10 Ngày bằng bot tất định), README chạy từ clone sạch, CREDITS/LICENSE.

## Cách chạy
Cần Python ≥ 3.9 (không cài thêm gì) và một trình duyệt.

```bash
unzip quan-an-cho-noi-v1.0.0.zip && cd quan-an-cho-noi-v1.0.0
python3 -m chonoi.live            # mở http://127.0.0.1:8000/
```
Điều khiển: WASD/mũi tên · E tương tác · Space bắt cá · Esc/P tạm dừng · H tương phản cao · Shop 1/2/Enter.
Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` · Benchmark: `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json` · Soak: `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json`.

## Số đo (máy phát triển, macOS, Chrome headless)
- Benchmark seed 42, 30 s: avg 60 FPS, 1% low 59.5 FPS, load 0.5–0.65 s (`docs/proof/phase-4/bench.json`). FPS bị trần vsync 60 Hz của Chrome.
- Soak 10 Ngày seed 7: 10/10 Ngày, 0 crash, ~5 s; lặp lại cho kết quả gameplay giống hệt (`docs/proof/phase-4/soak.json`).
- 125 test tự động xanh (1 test benchmark render bật bằng `CHONOI_BENCH_TEST=1`).

## Giới hạn đã biết
- Nhóm chỉ 1 thành viên (đề yêu cầu 4–6); không làm mục mở rộng nào (dòng lũ, khách đặt trước, bảng xếp hạng, phụ đề SFX, Lao, vợt…).
- Không có âm thanh; đồ họa là khối 2D đơn giản.
- Benchmark: Chrome headless báo viewport 1280×633 (khung trình duyệt chiếm phần còn lại) nhưng canvas vẫn vẽ đủ 1280×720; FPS bị trần 60. Không có Chrome/Chromium thì lệnh mở trình duyệt mặc định.
- Nhiều chỗ đề chưa nói rõ được nhóm tự giả định (`docs/clarify.md`, 43 mục) — test ẩn có thể chấm khác.
- Chế độ tương phản cao và ba cảnh báo được kiểm bằng ảnh chụp tự động (`tools/screenshot.py`), chưa có người chơi thử dài trên trình duyệt thật.
