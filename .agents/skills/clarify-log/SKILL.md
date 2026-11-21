---
name: clarify-log
description: Quy trình khi gặp yêu cầu mơ hồ trong PRD/ticket — không bịa luật, ghi câu hỏi + giả định vào docs/clarify.md, gắn giả định vào code và test. Dùng mỗi khi agent phải chọn giữa nhiều cách hiểu.
---

# clarify-log

## Khi nào dùng
Bất cứ khi nào PRD/ticket không nói rõ: thứ tự xử lý trong một tick, tick nào được tính, làm tròn, hòa thì chọn gì, dữ liệu event gồm trường nào...

## Các bước
1. **Dừng, không đoán ngầm.** Viết câu hỏi một dòng, nêu 2 cách hiểu.
2. Thêm một dòng vào bảng `docs/clarify.md`:
   `| #n | YYYY-MM-DD HH:MM | <câu hỏi> | <trả lời của PO> hoặc "GIẢ ĐỊNH: <cách chọn> (lý do)" | <ai quyết> |`
3. Code theo lựa chọn đó và ghi `# giả định: clarify #n` ngay tại chỗ trong code.
4. Viết một test khóa hành vi đó (tên test nhắc tới hành vi, ví dụ `test_oxygen_empty_then_choke_every_interval`).
5. Khi PO trả lời khác giả định: sửa luật + test trong cùng một commit, cập nhật dòng clarify (ghi "ĐÃ ĐỔI").

## Không được
- Không sửa test của giảng viên (`tests/test_smoke_p1.py`) cho xanh.
- Không thêm số liệu vào luật; số liệu chỉ nằm trong `game.contract.json`.
