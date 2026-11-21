# Kế hoạch Phase 2 — Ticket-02 (≤ 1 trang)

- **Mục tiêu:** Test Contract v1.1 với số chuẩn; cá bơi/sinh, Cá Sấu, Máu/ngất, 2 bếp/4 bàn/6 món; `--mode day` (kế hoạch D1–D5, Shop, nâng cấp oxygen/hp), pause; cửa sổ chơi trọn vòng ngày có menu, pause, HUD; tag `phase-2`.
- **So số chuẩn với giả định cũ (phút 0–5):** tuning P1 đã dùng đúng preset nên chỉ thêm khóa mới; 4 test P1 phải đổi vì luật mới (ghi lý do trong test + `docs/verification/phase-2.md`).

| Lát (Ticket-02 mục 5) | AC | Việc | Người | Phụ thuộc |
|---|---|---|---|---|
| 1 | AC-P2-01..04 | contract v1.1, N5/N6, cá bơi/phản xạ/đổi hướng, sinh theo lịch | Haind + Claude | — |
| 2 | AC-P2-05..08 | Cá Sấu patrol/chase/recoil, hit (LIFO, bất tử), faint cause monster | Haind + Claude | lát 1 (thứ tự bước gather) |
| 3 | AC-P2-09..10 | B2, T2–T4, 6 món, lọc món theo kế hoạch | Haind + Claude | — |
| 4 | AC-P2-11..17 | runner (tick/sim_tick/phase_tick, pause), `day`, Shop, CLI `--days`, scenario `day`, cửa sổ chơi + HUD | Haind + Claude | lát 1–3 |
| QA | AC-P2-18..20 | `tests/test_rules_p2.py`, `test_live_day.py`, verify-phase 2 (integration.*, day smoke, nhiều Ngày, regression P1) | Haind | tất cả |

- **Giao diện chuyển pha (chốt trước khi code):** `DaySim` giữ trạng thái xuyên Ngày; mỗi pha là một sim con có `step/snapshot/done/phase_tick`; sự kiện con trả về `(name, data, phase, day)` để runner gắn đúng pha cũ/mới.
- **Rủi ro:** nhiều chỗ ticket chưa nói rõ (thứ tự phát hiện/di chuyển Cá Sấu, chọn loài theo trọng số…) → `docs/clarify.md` #18–#30; không kiểm được FPS/hiển thị bằng trình duyệt thật trong phiên agent.
