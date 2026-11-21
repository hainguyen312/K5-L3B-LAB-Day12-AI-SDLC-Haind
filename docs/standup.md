# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| 1 (phút 20) | hainguyen312 | TEAM.md, hợp đồng tích hợp, gather lát 1–2 (oxy, ngạt, hái, bắt cá) | quan lát 3–4, test luật | Không đọc được PRD đầy đủ từ lab board qua agent → dựa vào docstring khung + smoke test, ghi giả định |
| 1 (phút 45) | hainguyen312 | quan lát 3–4, test luật, skill verify-phase | đối chiếu PRD-0 vừa lấy được | 11 giả định chưa được xác nhận |
| 1 (trước tag) | hainguyen312 | Sửa theo PRD-0: 6 giả định sai đã đổi; 68 test xanh; bằng chứng mới | commit + gắn tag `phase-1` | chưa có repo fork trên GitHub |
| 2 (phút 20) | hainguyen312 | contract v1.1, cá bơi/sinh, Cá Sấu, 2 bếp/4 bàn/6 món; smoke tích hợp gather → kho → quan đạt | `day`, Shop, pause, cửa sổ chơi | thứ tự phát hiện của Cá Sấu chưa rõ → giả định clarify #21 |
| 2 (phút 40) | hainguyen312 | `day` + Shop + pause, 98 test xanh, verify-phase 2 PASS | tài liệu, retro, tag `phase-2` | chưa kiểm được giao diện bằng trình duyệt |
| 3 (phút 7) | hainguyen312 | Phân tích tác động + ADR-0002, chốt thứ tự tích hợp | items/inventory → gather → quan → day | — |
| 3 (phút 20) | hainguyen312 | v1.2 chạy; smoke bàn giao file khớp chính xác sau khi bỏ làm tròn `fresh` | migrate 36 test cũ, test P3, HUD | 36 test đỏ do breaking change (dự kiến) |
