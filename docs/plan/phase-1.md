# Kế hoạch Phase 1 (≤ 1 trang)

- **Mục tiêu:** luật `gather` (oxy, ngạt, Máu, ngất, hái, bắt cá, giỏ) và `quan` (khách, giữ chỗ, bếp, bưng, trả tiền, boa, uy tín) đúng Test Contract v1.0; luồng gather → file kho → quan chạy được; tag `phase-1`.
- **Việc / người / phụ thuộc** (nhóm 1 người, chia theo lát; mỗi lát giao một agent AI, tôi đọc lại diff):

| Lát | Việc | Người | Phụ thuộc |
|---|---|---|---|
| 0 | Kickoff: TEAM.md, `team_size`, hợp đồng tích hợp (`docs/contracts/`) | Haind | — |
| 1 | gather: oxy + ngạt + Máu + ngất + dive/surface | Haind + Claude | lát 0 |
| 2 | gather: hái nút + bắt cá + hold_full | Haind + Claude | lát 1 |
| 3 | quan: lịch khách, chọn món, giữ chỗ, kiên nhẫn, no_dish | Haind + Claude | lát 0 (schema kho) |
| 4 | quan: bếp, bưng, phục vụ, trả tiền, boa, uy tín, kiểm scenario mức luật | Haind + Claude | lát 3 |
| 5 | QA: `tests/test_rules_p1.py`, skill `verify-phase`, bằng chứng `docs/proof/phase-1/` | Haind | lát 1–4 |

- **Rủi ro:**
  - Agent không đọc được PRD trên lab board → phải dán nguyên văn; chỗ PRD chưa nói → `docs/clarify.md` (#13–#17), khóa bằng test.
  - Một người làm mọi vai → không có review chéo; bù bằng đọc diff + `verify-phase` trước tag.
  - Nhóm < 4 người → không đạt điều kiện số thành viên của đề (đã ghi trong TEAM.md).
