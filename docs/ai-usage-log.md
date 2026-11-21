# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | hainguyen312 | Claude Code (Claude Opus 5.5) | Đọc khung `chonoi/`, smoke test; tóm tắt yêu cầu Phase 1 | ~60k token vào | Agent không đọc được nội dung PRD trên lab board (dữ liệu tải động, artifact ngoài tổ chức) → phải suy từ docstring + test; tôi xác nhận lại bằng cách đọc smoke test |
| 1 | hainguyen312 | Claude Code (Claude Opus 5.5) | Viết luật `sim/gather.py` (oxy, ngạt, faint, hái, bắt cá) | ~15k token ra | Bản đầu cần quyết: tick oxy chạm 0 có tính ngạt không → ghi clarify #1 thay vì để AI tự đoán ngầm |
| 1 | hainguyen312 | Claude Code (Claude Opus 5.5) | Viết luật `sim/quan.py` + kiểm scenario mức luật | ~20k token ra | AI tự thêm sự kiện `no_table` không có trong PRD → giữ lại nhưng ghi vào hợp đồng sự kiện + clarify #7 để PO duyệt |
| 1 | hainguyen312 | Claude Code (Claude Opus 5.5) | Viết `tests/test_rules_p1.py` (20 test), skill `verify-phase`, `clarify-log`, tài liệu | ~25k token ra | Test vòng phục vụ phải tính số tick đi bộ từ bếp tới bàn; kiểm bằng cách chạy test, không tin con số AI nhẩm |
| 1 | hainguyen312 | Claude Code (Claude Opus 5.5) | Đối chiếu code với PRD-0 (dán nguyên văn), sửa gather (payload event, hồi chiêu khi trượt/hold_full) và viết lại `sim/quan.py` (payload món, order_status, đóng ca, lịch theo phase_tick, kiểm fixture mục D) | ~40k token ra | **AI sai rõ nhất:** khi chưa có PRD, agent tự đoán 11 luật thì 6 luật sai (boa dùng `round` thay `floor`, khách rời trước interact, bắt trượt vẫn tốn hồi chiêu, tự thêm `no_table`…). Phát hiện bằng cách đặt từng dòng `docs/clarify.md` cạnh câu PRD tương ứng |
| 1 | hainguyen312 | Claude Code (Claude Opus 5.5) | Viết lại `tests/test_rules_p1.py` (36 test, mỗi test trỏ một câu PRD) | ~20k token ra | Test vòng phục vụ đầu tiên tự sinh 2 frame cùng tick → headless trả mã 2; lỗi ở test chứ không ở luật, sửa test |
