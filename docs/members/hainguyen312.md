# hainguyen312 — phản tư cá nhân (≤ 200 từ)

- **Phần tôi làm (nhóm 1 người, mọi lát):** P1 luật gather/quan (`2df311f`…`35632df`); P2 contract v1.1, cá/Cá Sấu, `day`, Shop, pause, cửa sổ chơi (`b5391ed`…`3a11e2e`); P3 kho cá thể có độ tươi, ADR-0002 (`806501d`…`e20a0c1`); P4 bench, soak, cảnh báo + tương phản cao, phát hành v1.0.0. Bằng chứng: `docs/proof/phase-1..4/`.
- **Đã giúp ai / review:** không có thành viên khác; tôi review mọi diff do Claude Code viết trước khi commit, đối chiếu với câu PRD/ticket.
- **AI sai ở đâu và tôi phát hiện thế nào:** P1 đoán sai 6/11 luật khi chưa có PRD (đối chiếu clarify ↔ PRD); P2 Shop không hiện cấp vừa mua (test bắt); P3 làm tròn fresh làm smoke "so chính xác" hỏng (chạy đúng ví dụ ticket); P4 giao diện có lỗi đọc/che chữ mà test không thấy (xem ảnh chụp).
- **Bài học:** với AI, phần đắt nhất là chốt yêu cầu và kiểm chứng, không phải viết code; mỗi loại rủi ro cần một loại bằng chứng riêng — test cho luật, ảnh chụp cho giao diện, số đo cho hiệu năng.
