# TEAM

**Tên nhóm:** Haind  **Số người:** 1  (khớp `team_size` trong `game.contract.json`)

> Nhóm chỉ có **1 thành viên** (làm cá nhân, ít hơn mức 4–6 người của đề). `tools/check_team.py` vì vậy sẽ cảnh báo
> "số thành viên phải từ 4 đến 6" — đây là cảnh báo đã biết, CI không chặn. Một người kiêm mọi module và mọi vai.

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Nguyễn Đức Hải | hainguyen312 | `sim/gather`, `sim/quan`, `client/ui`, `qa` | PO · Integrator · QA lead · Scrum/Release | — (làm một mình) |

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Có thể kiêm.

## Thỏa thuận làm việc nhóm (điền trong 15 phút kickoff, ≤ 10 dòng)

- Kênh liên lạc: hỏi giảng viên/trợ giảng trực tiếp trên lab board (Anh Năm hàng xóm); ghi mọi câu trả lời vào `docs/clarify.md`.
- Khi bất đồng về thiết kế: (với chính agent AI) đọc lại PRD 2 phút; không rõ thì chọn cách đơn giản nhất, ghi "GIẢ ĐỊNH" + ADR nếu đổi hợp đồng.
- Khi vướng quá 10 phút: ghi vào `docs/standup.md`, hỏi trợ giảng, chuyển sang lát khác rồi quay lại.
- Giờ standup giữa phase: tự standup ở phút 20 của mỗi phase (một dòng trong `docs/standup.md`).
- Cách đọc code: mọi thay đổi do agent viết đều được tôi đọc lại diff trước khi commit; chạy skill `verify-phase` trước khi gắn tag.
- Cách làm việc với Git: push thẳng `main` (một người), commit nhỏ theo lát; tôi gắn tag `phase-N` sau khi `verify-phase` PASS.
