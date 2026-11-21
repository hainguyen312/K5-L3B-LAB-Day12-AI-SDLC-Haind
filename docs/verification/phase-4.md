# Ma trận truy vết Phase 4 (Ticket-04 Phát hành v1.0.0, Test Contract v1.3)

Chạy lại: `bash .agents/skills/verify-phase/verify.sh 4` → [`docs/proof/phase-4/verify.txt`](../proof/phase-4/verify.txt) (125 test, tất định byte, smoke P2/P3, benchmark render, soak 10 Ngày ×2, regression P1–P3, `RESULT: PASS` ở commit `3c77cef`).

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P4-01 `contract_version 1.3`, `bench_cmd`, `soak_cmd` ở gốc manifest; gameplay/kho/JSONL giữ v1.2 | `tests/test_p4.py::Manifest`, `chonoi/contract.py` kiểm đủ 5 lệnh | verify.txt | đạt |
| AC-P4-02 `bench_cmd --seed 42 --duration 30 --out bench.json`: cảnh sáng chuẩn, đứng yên ở bến, 1280×720, làm nóng 3 s, đúng 5 trường | `python3 -m chonoi.bench …` (Chrome headless); công thức `p1_low_fps`/`avg_fps` ở `BenchFormula.test_summary_fields_and_p1_low`; render thật `test_render_bench_end_to_end` (`CHONOI_BENCH_TEST=1`) | [bench.json](../proof/phase-4/bench.json): avg 60.0, 1% low 59.52, 1801 khung / 30.015 s, load 717 ms (chạy lại trên clone sạch: 716 ms) | đạt (mốc ≥ 60 / ≥ 30 / ≤ 10 s đều đạt; FPS bị trần vsync 60 — xem clarify #39) |
| AC-P4-03 `soak_cmd --seed 7 --days 10 --out soak.json`: 10 Ngày gather → quan → shop, D1–D5 lặp, trạng thái xuyên suốt; `days_completed = days`, `crashes = 0`, lặp lại giống nhau | `Soak.*` + script chạy 2 lần so (bỏ `duration_s`) | [soak.json](../proof/phase-4/soak.json) (10/10, 0 crash, earned 476, uy tín 5 ở Ngày 10) | đạt |
| AC-P4-04 ba cảnh báo có chữ + biểu tượng: thủy quái gần, oxy sắp hết, khách sắp giận | ảnh chụp tự động từ scenario dựng sẵn (`tools/screenshot.py`) | [warn-gather-normal.png](../proof/phase-4/warn-gather-normal.png), [warn-quan-normal.png](../proof/phase-4/warn-quan-normal.png), scenario `warn-*.scenario.json` | đạt |
| AC-P4-05 chế độ tương phản cao (H / `?contrast=1`, nhớ giữa lần mở) và cả ba cảnh báo ở chế độ đó | ảnh chụp ở `?contrast=1` | [warn-gather-contrast.png](../proof/phase-4/warn-gather-contrast.png), [warn-quan-contrast.png](../proof/phase-4/warn-quan-contrast.png) | đạt (kiểm bằng ảnh chụp tự động, chưa có người chơi thử dài) |
| AC-P4-06 clone sạch chạy bản có giao diện ≤ 3 lệnh (clone, cd, `python3 -m chonoi.live`) | `git clone` thật từ GitHub (commit `3c77cef`) rồi chạy đúng lệnh README: server lên menu + trả index.html, 125 test, headless day, soak, bench | [clean-clone.txt](../proof/phase-4/clean-clone.txt) | đạt |
| AC-P4-07 README: yêu cầu môi trường, điều khiển, lệnh test/headless/benchmark/soak; CREDITS + LICENSE rà tài sản | đọc README/CREDITS/LICENSE | `README.md`, `CREDITS.md` (không có asset ngoài), `LICENSE` | đạt |
| AC-P4-08 CHANGELOG theo từng phase, release notes (điểm mới, cách chạy, giới hạn), bản đóng gói chạy được | `CHANGELOG.md`, `docs/release-notes-v1.0.0.md`, `quan-an-cho-noi-v1.0.0.zip` (`git archive` của tag) | release notes + zip đính kèm Release | đạt khi Release được công bố |
| AC-P4-09 regression P1–P3 còn hiệu lực | `tests.test_smoke_p1`, `test_rules_p1/p2/p3` trong script | [regression-p1.txt](../proof/phase-4/regression-p1.txt), [regression-p2.txt](../proof/phase-4/regression-p2.txt), [regression-p3.txt](../proof/phase-4/regression-p3.txt) | đạt — 2 test đổi `contract_version` 1.2 → 1.3 (gameplay không đổi) |
| AC-P4-10 retro rà hành động P2, chốt việc tiếp theo; phản tư cá nhân đủ người | `docs/retro.md` (Phase 4), `docs/members/hainguyen312.md` | — | đạt (nhóm 1 người) |
| AC-P4-11 tag `phase-4` và GitHub Release v1.0.0 cùng trỏ một commit trên main | `git ls-remote origin` (phase-4^{} = v1.0.0^{}), trang Release | commit chứa file này; Release: https://github.com/hainguyen312/K5-L3B-LAB-Day12-AI-SDLC-Haind/releases/tag/v1.0.0 | đạt khi Release công bố (tag muộn so với mốc 3:00 của lab) |

## Ảnh giao diện khác (kiểm bằng mắt lần đầu ở P4)
[ui-menu.png](../proof/phase-4/ui-menu.png) · [ui-day-intro.png](../proof/phase-4/ui-day-intro.png). Xem ảnh phát hiện và đã sửa: nhãn "Oxy Ns" khó đọc, hộp cảnh báo che người chơi, tương phản cao tô vàng cả dòng bình thường.

## Đánh giá ngắn
- **Đạt:** toàn bộ lõi Ticket-04 chạy được trên máy phát triển; số đo vượt mốc báo cáo.
- **Giới hạn:** nhóm 1 người; không làm mở rộng (leaderboard, phụ đề SFX…); FPS đo bị trần 60 Hz; chưa có người chơi trọn 5 Ngày bằng tay (hành động tiếp theo trong retro).
