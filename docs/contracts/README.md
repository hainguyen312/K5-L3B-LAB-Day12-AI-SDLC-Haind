# Hợp đồng tích hợp — nhóm Haind (chốt ở kickoff Phase 1)

## 1. Schema file kho (PRD-0 mục G)
- Ghi **đúng một lần** khi có `gather_end` (docked / time / fainted); hết `--ticks` trước thì **không** ghi.
- Dạng: `{"items": {<id nguyên liệu>: <số nguyên ≥ 0>}}`, khóa sắp tăng dần, bỏ mục 0, chỉ khóa gốc `items`.
- Id hợp lệ v1.0: `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`. Mẫu: [`inventory.sample.json`](inventory.sample.json).
- Ngất → `{"items": {}}`. Quán đọc bằng `--inventory` (không được kèm `quan.stock` trong scenario → mã 2).

## 2. Giao diện `sim/*` ↔ `client/ui`
- UI (`chonoi/live.py` + `chonoi/web/index.html`) **chỉ đọc snapshot** (GET `/state`) và gửi `move`, `interact`, `catch` (POST `/input`). Không gọi hàm luật.
- Gather snapshot (PRD E): `player{pos, vel, heading_deg, oxygen_ticks, oxygen_max_ticks, hp, hp_max, zero_oxy_ticks, catch_cd_ticks, at_surface}`, `hold[]` (thứ tự nhặt, cuối = mới nhất), `hold_count`, `hold_capacity`, `nodes[{id,pos,kind,ready,regrow_ticks}]`, `fish[{id,pos,kind,heading_deg}]`.
- Quan snapshot (PRD D/E): `player{pos, vel}`, `stock{}` (gồm cả phần giữ), `hand` (payload `{order_id, dish_id, base_price}` hoặc null), `stoves[{id,pos,state: idle|cooking|ready,dish: payload|null,cook_ticks_left,ready_ticks}]`, `tables[{id,pos,customer_id}]`, `customers[{id,table_id,dish_id,order_tick,state: waiting|eating,order_status: reserved|assigned|unfulfillable|served,patience_ticks_left,eat_ticks_left,reserved,base_price,tip}]`.
- Chung (runner): `tick, sim_tick, mode, phase, phase_tick, state, time_left_ticks, money, earned, reputation, score = earned + 100 × floor(reputation)`.
- UI tự tính "kho khả dụng" = `stock − Σ customers[].reserved` để hiện HUD.

## 3. Danh sách sự kiện (PRD-0 mục E)

| Mode | Sự kiện | `data` | Ai phát |
|---|---|---|---|
| gather | `node_regrown` | `node_id` | sim/gather |
| gather | `dive` / `surface` | `pos` (sau di chuyển) | sim/gather |
| gather | `oxygen_empty` | `oxygen_ticks: 0` | sim/gather |
| gather | `choke` | `hp` (sau trừ) | sim/gather |
| gather | `faint` | `cause: "choke"`, `lost` (mảng kind, LIFO), `hp: 0` | sim/gather |
| gather | `gather` | `node_id, kind, amount` | sim/gather |
| gather | `fish_caught` | `fish_id, kind, yield` | sim/gather |
| gather | `hold_full` | `action: gather|catch`, `node_id` hoặc `fish_id`, `required`, `free` | sim/gather |
| gather | `gather_end` | `reason: time|docked|fainted`, `inventory{items}` | sim/gather (runner ghi kho) |
| quan | `customer_arrived` | `order_id, table_id, dish_id` | sim/quan |
| quan | `no_dish` | `{}` | sim/quan |
| quan | `cook_started` | `stove_id, order_id, dish_id, items` (mảng kind sắp theo kind), `base_price` | sim/quan |
| quan | `dish_ready` / `dish_picked` | `stove_id, order_id, dish_id` | sim/quan |
| quan | `served` | `order_id, table_id, dish_id, patience_ticks_left, base_price, tip` | sim/quan |
| quan | `paid` | `order_id, table_id, base_price, tip, amount, reason: finished_eating|closing` | sim/quan |
| quan | `customer_left` | `order_id, table_id, reason: patience|closing, reputation` | sim/quan |
| quan | `quan_end` | `reason: "time", money, earned, shift_earned, reputation` | sim/quan |

Người nghe: UI (nhật ký sự kiện, HUD) và test (`tests/test_rules_p1.py`). Đổi hợp đồng: ghi ADR trong `docs/adr/`.

## 4. Thay đổi v1.1 (Ticket-02, chốt đầu Phase 2)
- **Kho:** thêm `ca_keo`, `keo_neo` (6 nguyên liệu). Schema `{"items": {...}}` giữ nguyên; `day` bàn giao trong bộ nhớ theo đúng schema này.
- **CLI:** `--mode day`, `--days 1..5` (chỉ với day). `--inventory`/`--inventory-out` vẫn chỉ cho quan/gather độc lập.
- **Inputs:** nút `pause`, `shop_done`, `attack`, `photo` (2 nút cuối bị bỏ qua vì nhóm chưa bật mở rộng); `buy` là chuỗi, chỉ ở đúng frame.
- **Snapshot:** `state` thêm `paused`; gather thêm `monsters[]`, `fish[].age_ticks`; chế độ day thêm `day`, `day_plan`, `upgrades`, `active_upgrades`, pha `shop` có `stock` dư + `time_left_ticks`. `tick` (bước ngoài) ≠ `sim_tick` (gameplay) khi có pause; `phase_tick` về 0 khi đổi pha.
- **Giao diện sim nội bộ:** mỗi pha là một sim (`GatherSim`, `QuanSim`, `ShopSim`) có `step(inp) -> [(name, data)]`, `snapshot()`, `done`, `reason`, `phase_tick`, `time_left_ticks`, `money`, `earned`, `reputation`. `DaySim` (`chonoi/sim/day.py`) điều phối và trả sự kiện dạng `(name, data, phase, day)`.
- **UI ↔ sim:** cửa sổ chơi đọc thêm `ui {screen, elapsed, stats}` (chỉ có ở `chonoi.live`, không có trong JSONL) và gửi `/continue`, `/quit`, `buy`.

| Mode | Sự kiện mới v1.1 | `data` |
|---|---|---|
| gather | `monster_hit` | `monster_id, hp, lost` (mảng kind LIFO), `pos` (người chơi) |
| gather | `fish_spawned` | `id, kind, pos` |
| gather | `faint` | thêm `cause: "monster"` |
| day | `day_start`, `phase_start` | `{}` |
| day | `day_plan` | `dishes, ingredients` |
| mọi mode | `paused`, `resumed` | `{}` |
| shop | `bought` | `upgrade, level, price, money` |
| shop | `buy_failed` | `action, reason: funds|max_level|unknown` |
| shop | `shop_end` | `reason: done|time` |
