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
| 4 (phút 15) | hainguyen312 | contract v1.3, soak 10 Ngày (10/10, 0 crash), bench chạy được | cảnh báo + tương phản cao, ảnh chụp, tài liệu phát hành | Chrome headless chờ 60 s mỗi lần mở → đã tìm ra do dò proxy |
| 4 (phút 20) | hainguyen312 | ảnh chụp 3 cảnh báo ở 2 chế độ, sửa 2 lỗi hiển thị, verify-phase 4 PASS | retro, phản tư, clone sạch, tag + Release | chưa có `gh` để tạo Release từ terminal |
