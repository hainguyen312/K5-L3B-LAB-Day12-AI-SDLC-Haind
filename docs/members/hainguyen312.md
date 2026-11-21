# hainguyen312 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm:** toàn bộ Phase 1 (nhóm 1 người): luật `chonoi/sim/gather.py`, `chonoi/sim/quan.py`, test `tests/test_rules_p1.py` (36 test theo PRD), skill `.agents/skills/verify-phase` và `clarify-log`, hợp đồng `docs/contracts/README.md`, bằng chứng `docs/proof/phase-1/`. (Link commit: bổ sung sau khi commit/push lên repo nhóm.)
- **Tôi đã review:** đọc lại từng diff agent AI viết trước khi nhận; so hành vi với smoke test công khai và docstring khung.
- **AI sai ở đâu và tôi phát hiện thế nào:** agent không đọc được PRD trên lab board nên tự đoán 11 luật; khi tôi dán PRD vào, đặt từng giả định cạnh câu PRD thì 6 cái sai (boa `round` thay `floor`, khách rời trước interact, bắt trượt tốn hồi chiêu, tự thêm sự kiện `no_table`…). Nhờ đã ghi giả định vào `docs/clarify.md` và khóa bằng test nên sửa nhanh, biết chính xác chỗ cần đổi.
- **Điều tôi học được:** với AI, phần tốn công nhất không phải viết code mà là chốt chỗ mơ hồ; ghi giả định + khóa bằng test giúp đổi luật nhanh khi PO trả lời khác.
