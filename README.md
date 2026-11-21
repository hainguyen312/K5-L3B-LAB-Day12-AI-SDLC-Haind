# K5-L3B-LAB-Day12-AI-SDLC-Haind

> **Nhóm Haind** (1 thành viên: [@hainguyen312](https://github.com/hainguyen312)) — xem [`TEAM.md`](TEAM.md).
> **v1.0.0** (Phase 4, Ticket-04, Test Contract v1.3) — vòng ngày 5 Ngày: lặn & hái (cá bơi/sinh, Cá Sấu Năm Chèo, oxy/Máu),
> mở quán (2 bếp, 4 bàn, 6 món), Shop nâng cấp, pause, kho cá thể có độ tươi, cảnh báo dễ nhận biết + chế độ tương phản cao,
> benchmark có render và soak 10 Ngày. 125 test xanh. Ghi chú phát hành: [`docs/release-notes-v1.0.0.md`](docs/release-notes-v1.0.0.md).
> Bằng chứng: [phase-1](docs/verification/phase-1.md) · [phase-2](docs/verification/phase-2.md) · [phase-3](docs/verification/phase-3.md) · [phase-4](docs/verification/phase-4.md).

### Yêu cầu môi trường
- macOS hoặc Linux, **Python ≥ 3.9** (chỉ thư viện chuẩn, không cần `pip install`), trình duyệt hiện đại (Chrome, Firefox, Safari) để chơi.
- Benchmark cần thêm **Google Chrome / Chromium** (chạy headless; đặt `CHONOI_BROWSER=/đường/dẫn` nếu ở chỗ khác).

### Chạy từ clone sạch (≤ 3 lệnh)

```bash
git clone https://github.com/hainguyen312/K5-L3B-LAB-Day12-AI-SDLC-Haind
cd K5-L3B-LAB-Day12-AI-SDLC-Haind
python3 -m chonoi.live                     # mở địa chỉ in ra (mặc định http://127.0.0.1:8000/): menu -> 5 Ngày -> tổng kết
```

Bản đóng gói ở GitHub Release v1.0.0: giải nén `quan-an-cho-noi-v1.0.0.zip`, `cd quan-an-cho-noi-v1.0.0`, `python3 -m chonoi.live`.

### Điều khiển
| Phím | Việc |
|---|---|
| WASD / mũi tên | bơi (sáng) · đi (tối) |
| **E** | cập bến, hái (sáng) · nấu, lấy món, phục vụ (tối) |
| **Space** | bắt cá (dưới nước) |
| **Esc / P** | tạm dừng (Tiếp tục / Về menu) |
| **H** | bật/tắt **tương phản cao** (nhớ giữa các lần mở; hoặc mở `/?contrast=1`) |
| Shop: **1 / 2 / Enter** | mua Bình oxy / Áo phao / đóng Shop |

### Cách chơi và cảnh báo
- **Vòng ngày:** DayIntro (Má Tư đọc món + nguyên liệu cần) → lặn & hái → EveningIntro → mở quán → DayResult → Shop → Ngày kế; sau Ngày 5 là Tổng kết.
- **Cảnh báo (chữ + biểu tượng):** ⚠ *Thủy quái gần!* + viền tím khi Cá Sấu đuổi / ở gần dưới d ≥ 10 m · ⚠ *Oxy sắp hết!* khi oxy < 25% (⚠ *Hết hơi!* khi cạn) · 😠 *Khách sắp giận!* khi kiên nhẫn của khách < 25%. Ảnh ở chế độ thường và tương phản cao: [`docs/proof/phase-4/`](docs/proof/phase-4/).
- **Độ tươi:** hàng trong giỏ hao 0.5/s, trong kho quán 0.25/s; dưới 30 là ươn (✗), không nấu được. Giá món = giá niêm yết × độ tươi trung bình.
- **Điểm:** `earned + 100 × floor(reputation)` (tiền đơn vị nghìn đồng; uy tín 0–5, bắt đầu 3.0). Mua nâng cấp trừ tiền nhưng không trừ điểm.

### Lệnh cho kiểm thử / chấm
| Việc | Lệnh |
|---|---|
| Test (1 lệnh) | `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` |
| Headless | `python3 -m chonoi.headless --mode gather\|quan\|day --seed 1 --ticks 22200 --out out.jsonl [--days 1..5]` |
| Benchmark có render | `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json` |
| Soak headless | `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json` |
| Kiểm chứng + bằng chứng | `bash .agents/skills/verify-phase/verify.sh 4` |
| Chơi riêng từng buổi | `python3 -m chonoi.live --mode gather --inventory-out kho.json` rồi `python3 -m chonoi.live --mode quan --inventory kho.json` |

## Sáng tạo của nhóm

Phase 1–4 ưu tiên **làm lõi đúng trước**: không làm mục mở rộng nào của Ticket-02/03/04 (nhóm 1 người, không bắt buộc), nên `extensions` không khai.
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
