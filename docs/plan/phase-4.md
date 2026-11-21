# Kế hoạch Phase 4 — Ticket-04 Phát hành v1.0.0 (≤ 1 trang)

| Vai (Ticket-04 mục 4) | Việc | Người |
|---|---|---|
| Đóng gói | thử clone sạch, README ≤ 3 lệnh, zip bản phát hành (`git archive`) | hainguyen312 |
| Bench/QA | `chonoi/bench.py`, `chonoi/soak.py`, `tests/test_p4.py`, `verify-phase 4`, ma trận `docs/verification/phase-4.md` | hainguyen312 + Claude |
| Release/Integrator | release notes, CHANGELOG, tag `phase-4`, GitHub Release v1.0.0 cùng commit | hainguyen312 |
| Điều phối retro | rà hành động retro P2/P3 (chơi thử trên trình duyệt), retro cuối, phản tư | hainguyen312 |

- **AC:** AC-P4-01 manifest v1.3 · 02 bench_cmd + bench.json · 03 soak_cmd · 04 ba cảnh báo · 05 tương phản cao · 06 clone sạch ≤ 3 lệnh · 07 README/CREDITS/LICENSE · 08 CHANGELOG + release notes + bản đóng gói · 09 regression P1–P3 · 10 retro + phản tư · 11 tag + Release cùng commit.
- **Rủi ro:** không có `gh` để tạo Release từ terminal → chuẩn bị zip + release notes, tạo Release bằng web (hoặc `gh` sau khi người dùng đăng nhập).
