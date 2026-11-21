# K5-L3B-LAB-Day12-AI-SDLC-Haind

> **Nhóm Haind** (1 thành viên: [@hainguyen312](https://github.com/hainguyen312)) — xem [`TEAM.md`](TEAM.md).
> Trạng thái: **Phase 3 (Ticket-03 "Mùa Nước Nổi") xong** — Test Contract v1.2: kho cá thể có độ tươi (hao, ươn, giữ chỗ theo id, giá theo tươi) trên nền vòng ngày 5 Ngày, cá bơi/sinh, Cá Sấu, Shop, pause; 118 test xanh. Bằng chứng: [`phase-1`](docs/verification/phase-1.md) · [`phase-2`](docs/verification/phase-2.md) · [`phase-3`](docs/verification/phase-3.md). Breaking change kho: xem [`CHANGELOG.md`](CHANGELOG.md).

**Chạy từ clone sạch** (macOS/Linux, chỉ cần Python ≥ 3.9, không cài thêm gì):

```bash
git clone https://github.com/hainguyen312/K5-L3B-LAB-Day12-AI-SDLC-Haind && cd K5-L3B-LAB-Day12-AI-SDLC-Haind
python3 -m chonoi.live                     # mở địa chỉ in ra trên trình duyệt: menu -> 5 Ngày -> tổng kết
```

- **Vòng ngày:** DayIntro (Má Tư đọc món + nguyên liệu cần) → lặn & hái → EveningIntro → mở quán → DayResult → Shop → Ngày kế; sau Ngày 5 là Tổng kết.
- **Điều khiển:** WASD / mũi tên bơi hoặc đi · **E** tương tác (cập bến, hái; ở quán: nấu, lấy món, phục vụ) · **Space** bắt cá · **Esc/P** tạm dừng (Tiếp tục / Về menu) · Shop: **1** Bình oxy, **2** Áo phao, **Enter** đóng Shop.
- **Cẩn thận:** Cá Sấu Năm Chèo tuần tra ở d ≥ 10 m; bị chạm mất 1 Máu và nửa giỏ. Oxy cạn thì ngạt mất Máu. Máu về 0 là ngất, tối mở quán với kho rỗng.
- **Độ tươi (Mùa Nước Nổi):** hàng trong giỏ hao 0.5/s, trong kho quán 0.25/s; dưới 30 là ươn (✗ trên HUD), không nấu được. Giá món = giá niêm yết × độ tươi trung bình — về bến sớm thì bán được giá hơn.
- **Điểm:** `earned + 100 × floor(reputation)` (tiền đơn vị nghìn đồng; uy tín 0–5, bắt đầu 3.0). Mua nâng cấp trừ tiền nhưng không trừ điểm.
- **Chơi riêng từng buổi:** `python3 -m chonoi.live --mode gather --inventory-out kho.json` rồi `python3 -m chonoi.live --mode quan --inventory kho.json`.
- **Test (1 lệnh):** `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- **Kiểm chứng + bằng chứng:** `bash .agents/skills/verify-phase/verify.sh 3`
- **Headless:** `python3 -m chonoi.headless --mode gather|quan|day --seed 1 --ticks 22200 --out out.jsonl [--days 1..5]` (cờ theo Test Contract v1.2).

## Sáng tạo của nhóm

Phase 1–3 ưu tiên **làm lõi đúng trước**: chưa làm mục mở rộng nào của Ticket-02/03 (nhóm 1 người, không bắt buộc).
Phần trình bày riêng của nhóm trong cửa sổ chơi (không ảnh hưởng headless): bảng màu nước phù sa / ánh hồng buổi sớm / đèn dây vàng ở quán, lời Má Tư giọng Nam Bộ ở DayIntro. Các giả định luật (không phải sáng tạo) ghi ở
[`docs/clarify.md`](docs/clarify.md). Mở rộng ở phase sau sẽ được liệt kê tại đây và tắt ở headless.

---

## Đề bài gốc

### Day 12 — AI SDLC: Quán Ăn Chợ Nổi

> **Làm theo nhóm 4–6 người** · Dùng AI để xây game 2D qua **4 phase** trong **3 giờ**: Út Sen lặn bắt cá, hái rau trên mặt nước rồi tối mở quán phục vụ khách.
> **Yêu cầu từng phase mở đúng mốc giờ tại lab board:** **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** (cần đăng nhập claude.ai; có trợ giảng AI cho từng phase).

## Bắt buộc (chỉ có thế)

Cách làm việc kỹ thuật là **tự do** (push thẳng, nhánh + PR, pair, có hay không CI…). Cái bắt buộc:

1. **Một repo chung:** trưởng nhóm **fork** repo này, đặt tên `K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`, thêm mọi thành viên làm collaborator (*Settings → Collaborators*, quyền Write) và để repo **public** (giảng viên xem được, không cần mời).
2. **Cả nhóm cùng commit** bằng tài khoản GitHub của mình, mỗi người **≥ 3 commit có nội dung** (làm cặp thì ghi `Co-authored-by:`).
3. **Điền [`TEAM.md`](TEAM.md):** danh sách thành viên + thỏa thuận làm việc nhóm; sửa `team_size` trong [`game.contract.json`](game.contract.json). Commit của người không có trong `TEAM.md` không được tính.
4. **Gắn tag** `phase-1` … `phase-4` đúng hạn; chạy được tại từng tag.
5. **Ghi chép tối thiểu:** `docs/verification/phase-n.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/<handle>.md`.

## Bắt đầu nhanh

```bash
git clone <fork-của-nhóm> && cd <fork-của-nhóm>
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v        # smoke test
python3 -m chonoi.live --mode gather                                # chơi thử trên trình duyệt (tùy chọn)
```

Game cần chế độ **headless** theo Test Contract (`python3 -m chonoi.headless --mode gather|quan …`) để được chạy và chấm tự động. **Công nghệ không ràng buộc**: khung Python trong `chonoi/` chỉ là gợi ý, chi tiết ở [`docs/STARTER.md`](docs/STARTER.md).

## Tự do sáng tạo

Ngoài phần đề yêu cầu, nhóm được **thêm** nhân vật, loài cá/cây, sinh vật, món, bản đồ, cơ chế, câu chuyện, đồ họa, âm nhạc… với ba điều kiện: **không phá phần cố định** (tắt ở headless), ghi mục **"Sáng tạo của nhóm"** trong README của nhóm, và **làm lõi đúng trước**.

## Lịch 3 giờ

| Mốc | Phase | Hạn tag |
|---|---|---|
| 0:00 | Phase 1 (PRD-0) | `phase-1` trước 1:00 |
| 1:00 | Phase 2 | `phase-2` trước 1:55 |
| 1:55 | Phase 3 | `phase-3` trước 2:30 |
| 2:30 | Phase 4 | `phase-4` + Release `v1.0.0` trước 3:00 |

Hết giờ mỗi phase thì gắn tag rồi đi tiếp; chỗ chưa xong ghi trung thực trong bằng chứng.

## Đánh giá (100 điểm)

| Hạng mục | Điểm |
|---|---|
| Test tự động ẩn (headless, gồm kiểm tra lại phase trước) | 25 |
| Làm việc nhóm (một repo chung, chia việc, tích hợp, đổi yêu cầu) | 25 |
| Kiểm chứng & bằng chứng | 15 |
| Harness AI (AGENTS.md, skill, nhật ký dùng AI) | 10 |
| Đánh giá & retro | 10 |
| Chất lượng sản phẩm (đúng yêu cầu, mở rộng/sáng tạo) | 10 |
| Demo | 5 |

## Quy định

- Dùng AI thoải mái; **không sao chép repo của nhóm khác**; bằng chứng phải thật.
- Nhân vật, bối cảnh là bản gốc của lab; asset ngoài chỉ dùng CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn trong `CREDITS.md`. Không commit API key, token, `.env`.
