# Kế hoạch Phase 3 — Ticket-03 Change Request "Mùa Nước Nổi" (≤ 1 trang)

- **Mục tiêu:** Test Contract v1.2 — kho cá thể có độ tươi qua file và trong `day`; kho đếm → mã 2; giữ chỗ theo id, giữ lại khi hàng vừa ươn, giá theo tươi; HUD hiện độ tươi; tag `phase-3`.
- **Phân tích tác động, quyết định schema, thứ tự tích hợp:** [ADR-0002](../adr/0002-kho-ca-the-do-tuoi-v12.md).
- **AC:** AC-P3-01 contract/schema · 02 hao + spoiled (giỏ) · 03 id cá thể · 04 file kho + round-trip ngưỡng · 05 kho đếm → 2 · 06 hao kho quán · 07 giữ theo id tươi nhất · 08 giữ lại khi ươn / unfulfillable · 09 giá theo tươi + boa · 10 bàn giao trong day + Shop không hao · 11 HUD · 12 regression P1–P2 · 13 DoD tag.
- **Mở rộng (dòng lũ, khách đặt trước):** không làm — nhóm 1 người, ticket không bắt buộc với nhóm ≤ 4.
- **Rủi ro:** phép làm tròn ở ngưỡng (giải bằng phân số + lưới 1/240); thứ tự id trong `reserved` không được ticket nói rõ (clarify #33).
