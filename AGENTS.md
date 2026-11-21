# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Headless: `python3 -m chonoi.headless --mode gather|quan --seed 1 --ticks 600 --out out.jsonl`
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode gather|quan` (mở địa chỉ in ra; WASD, E, Space, R)
- Test luật của nhóm: `PYTHONPATH=tests:. python3 -m unittest tests.test_rules_p1 -v`
- Kiểm chứng + bằng chứng trước khi gắn tag: `bash .agents/skills/verify-phase/verify.sh <N>`

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do.
- Luật chơi của nhóm: `chonoi/sim/gather.py`, `chonoi/sim/quan.py` — docstring đầu file ghi THỨ TỰ một bước; giữ đúng thứ tự đó khi sửa.
- Hành vi theo giả định có comment `giả định: clarify #n` → đọc `docs/clarify.md` trước khi đổi.
- Test luật: `tests/test_rules_p1.py` (hộp đen qua headless, dùng `run(mode, block, inputs, ticks)`).
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm
- `verify-phase` (`.agents/skills/verify-phase/`): chạy unittest + so byte tất định 2 mode + luồng gather→kho→quan, ghi `docs/proof/phase-N/`. Dùng sau mỗi lần sửa luật và BẮT BUỘC trước khi gắn tag.
- `clarify-log` (`.agents/skills/clarify-log/`): gặp chỗ PRD mơ hồ → ghi câu hỏi + GIẢ ĐỊNH vào `docs/clarify.md`, comment `giả định: clarify #n` trong code, viết test khóa hành vi. Không đoán ngầm.

## Bài học từ Phase 1 (cập nhật theo phase)
- Agent không đọc được PRD trên lab board → luôn dán nguyên văn phase vào prompt. Phase 1: agent tự đoán 11 luật, 6 luật sai, phải làm lại.
- Agent hay tự thêm sự kiện/trường ngoài PRD → mọi sự kiện mới phải có trong `docs/contracts/README.md`.
