# Credits

## Tài sản (asset)
- **Không dùng asset ngoài.** Toàn bộ hình là khối 2D vẽ bằng Canvas trong `chonoi/web/index.html`; chữ dùng font hệ thống
  (`system-ui`), biểu tượng ⚠ 😠 ✗ ♥ là ký tự Unicode/emoji của hệ điều hành. Không có âm thanh, nhạc, ảnh hay font tải về.
- Nhân vật, bối cảnh, món ăn và cơ chế là bản gốc của lab Day 12 (Quán Ăn Chợ Nổi, VinUni-AI20k).

## Mã nguồn
- Khung starter `chonoi/` (CLI headless, inputs, scenario, runner, cửa sổ chơi thử) do giảng viên lab cung cấp
  (`VinUni-AI20k/K5-L3B-LAB-Day12-AI-SDLC`); nhóm Haind mở rộng theo PRD-0 và Ticket-02/03/04.
- Chỉ dùng thư viện chuẩn Python; benchmark gọi Google Chrome/Chromium có sẵn trên máy (không đóng gói kèm).

## Công cụ AI
- Claude Code (model Claude Opus 5.5, Anthropic) hỗ trợ viết mã, test và tài liệu; chi tiết theo phase ở `docs/ai-usage-log.md`.
  Mọi thay đổi do AI viết đều được hainguyen312 đọc lại và kiểm bằng test / bằng chứng trong `docs/proof/`.
