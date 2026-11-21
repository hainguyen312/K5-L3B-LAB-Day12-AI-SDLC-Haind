"""Test luật Phase 2 của nhóm Haind theo Ticket-02 / Test Contract v1.1 — hộp đen qua headless.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_rules_p2 -v

v1.2 (Ticket-03): fixture giỏ/kho đổi sang cá thể {id, kind, fresh}; `lost` là mảng cá thể; giá món chốt theo độ tươi.
"""

import json
import math
import time
import unittest

from helpers import Workdir, events, frames, items, kind_counts, kinds, read_jsonl, run_headless, snapshots, stock, write_json


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


T = tuning()
G, Q, SHOP = T["gather"], T["quan"], T["shop"]
GATHER_T = int(G["duration_s"] * 60)
QUAN_T = int(Q["duration_s"] * 60)
SHOP_T = SHOP["max_ticks"]


def run(mode, scenario=None, inputs=None, ticks=10, seed=1, every=1, extra=()):
    """`scenario` là object gốc ({"gather": ...} / {"day": ..., "gather": ...}); trả (rows, code, stderr)."""
    with Workdir() as w:
        args = ["--mode", mode, "--seed", str(seed), "--ticks", str(ticks), "--snapshot-every", str(every),
                "--out", w.path("o.jsonl"), *extra]
        if scenario is not None:
            args += ["--scenario", write_json(w.path("sc.json"), scenario)]
        if inputs is not None:
            args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
        code, err = run_headless(*args)
        return (read_jsonl(w.path("o.jsonl")) if code == 0 else []), code, err


def names(rows):
    return [r["name"] for r in events(rows)]


def snap_at(rows, tick):
    return {r["tick"]: r for r in snapshots(rows)}[tick]


def spawn_points():
    return {(kind, x, d) for kind, ds in G["fish_spawn_depths"].items() for x in G["fish_spawn_x"] for d in ds}


# ----------------------------------------------------------------------------------------------- dữ liệu chuẩn
class StandardData(unittest.TestCase):
    def test_contract_v11_standard_numbers(self):
        with open("game.contract.json", encoding="utf-8") as f:
            c = json.load(f)
        self.assertEqual(c["contract_version"], "1.2")  # v1.2 (Ticket-03) giữ nguyên số chuẩn v1.1
        self.assertEqual([n["id"] for n in G["nodes"]], ["N1", "N2", "N3", "N4", "N5", "N6"])
        self.assertEqual(G["fish_yield"], {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2})
        self.assertEqual(len(T["menu"]), 6)
        self.assertEqual([s["id"] for s in Q["stoves"]], ["B1", "B2"])
        self.assertEqual([t["id"] for t in Q["tables"]], ["T1", "T2", "T3", "T4"])
        self.assertEqual(len(spawn_points()), 36)
        self.assertEqual(len({(x, d) for _, x, d in spawn_points()}), 30)
        need = {1: 9, 2: 10, 3: 12, 4: 9, 5: 10}
        for p in T["day_plan"]:
            self.assertEqual(sum(p["ingredients"].values()), need[p["day"]], p)


# ----------------------------------------------------------------------------------------------- cá
class Fish(unittest.TestCase):
    def test_initial_8_schools_at_distinct_spawn_points(self):
        for seed in (1, 2, 3):
            rows, code, err = run("gather", ticks=0, seed=seed)
            self.assertEqual(code, 0, err)
            fish = snapshots(rows)[0]["fish"]
            self.assertEqual([f["id"] for f in fish], [f"F{i}" for i in range(1, 9)])
            pos = [tuple(f["pos"]) for f in fish]
            self.assertEqual(len(set(pos)), 8)
            for f in fish:
                self.assertIn((f["kind"], f["pos"][0], f["pos"][1]), spawn_points())
                self.assertEqual(f["age_ticks"], 0)

    def test_swim_speed_and_age(self):
        sc = {"gather": {"fish": [{"id": "F1", "kind": "ca_linh", "pos": [50, 5], "heading_deg": 0}]}}
        rows, code, err = run("gather", sc, ticks=60)
        self.assertEqual(code, 0, err)
        f = snapshots(rows)[-1]["fish"][0]
        self.assertAlmostEqual(f["pos"][0], 50 + G["fish_speed"], places=2)
        self.assertEqual(f["age_ticks"], 60)

    def test_reflect_x_edge_and_depth_band(self):
        sc = {"gather": {"fish": [{"id": "F1", "kind": "ca_linh", "pos": [95.5, 5], "heading_deg": 0},
                                  {"id": "F2", "kind": "ca_linh", "pos": [50, 11.5], "heading_deg": 90},
                                  {"id": "F3", "kind": "ca_keo", "pos": [5, 22.5], "heading_deg": 225}]}}
        rows, code, err = run("gather", sc, ticks=60)
        self.assertEqual(code, 0, err)
        f1, f2, f3 = snapshots(rows)[-1]["fish"]
        self.assertAlmostEqual(f1["pos"][0], 95.0, places=2)   # 95.5 + 1.5 = 97 -> 96 - 1
        self.assertAlmostEqual(f1["heading_deg"], 180, places=2)
        self.assertAlmostEqual(f2["pos"][1], 11.0, places=2)   # 11.5 + 1.5 = 13 -> 12 - 1
        self.assertAlmostEqual(f2["heading_deg"], 270, places=2)
        self.assertAlmostEqual(f3["heading_deg"], 45, places=2, msg="chạm góc đảo cả hai thành phần")

    def test_turn_by_seed_at_swim_step_120(self):
        fish = [{"id": "F1", "kind": "ca_loc", "pos": [50, 14], "heading_deg": 0, "age_ticks": 119},
                {"id": "F2", "kind": "ca_loc", "pos": [30, 14], "heading_deg": 0, "age_ticks": 0}]
        a, *_ = run("gather", {"gather": {"fish": fish}}, ticks=1, seed=4)
        b, *_ = run("gather", {"gather": {"fish": fish}}, ticks=1, seed=4)
        f1, f2 = snapshots(a)[-1]["fish"]
        self.assertNotEqual(f1["heading_deg"], 0)
        self.assertEqual(f2["heading_deg"], 0)
        self.assertEqual(a, b, "đổi hướng theo seed, tất định")

    def test_spawn_every_360_after_swim_cap_and_clearance(self):
        rows, code, err = run("gather", {"gather": {"fish": []}}, ticks=720, every=1000)
        self.assertEqual(code, 0, err)
        ev = events(rows, "fish_spawned")
        self.assertEqual([e["tick"] for e in ev], [360, 720])
        self.assertEqual(ev[0]["data"]["id"], "F1")
        self.assertIn((ev[0]["data"]["kind"], *ev[0]["data"]["pos"]), spawn_points())
        full = [{"id": f"F{i}", "kind": "ca_keo", "pos": [5 + 7 * i, 25]} for i in range(1, G["fish_max"] + 1)]
        rows, *_ = run("gather", {"gather": {"fish": full}}, ticks=360, every=1000)
        self.assertEqual(events(rows, "fish_spawned"), [], "đủ trần 12 đàn thì không sinh")
        fish = snapshots(run("gather", ticks=GATHER_T - 1, every=GATHER_T)[0])[-1]["fish"]
        self.assertLessEqual(len(fish), G["fish_max"])

    def test_random_fish_false_static_no_spawn(self):
        sc = {"gather": {"random_fish": False, "fish": [{"id": "F1", "kind": "ca_keo", "pos": [50, 25], "heading_deg": 0}]}}
        rows, code, err = run("gather", sc, ticks=400, every=1000)
        self.assertEqual(code, 0, err)
        self.assertEqual(snapshots(rows)[-1]["fish"][0]["pos"], [50, 25])
        self.assertEqual(events(rows, "fish_spawned"), [])

    def test_catch_uses_position_before_swim(self):
        sc = {"gather": {"player": {"pos": [20, 5]}, "fish": [{"id": "F1", "kind": "ca_linh", "pos": [22, 5], "heading_deg": 0}]}}
        rows, code, err = run("gather", sc, [{"tick": 0, "catch": True}], ticks=1)
        self.assertEqual(code, 0, err)
        self.assertEqual(names(rows), ["fish_caught"], "đàn đúng mép 2.0 m trước khi bơi vẫn bắt được")

    def test_ca_keo_yield_and_keo_neo_node(self):
        sc = {"gather": {"player": {"pos": [76, 0]}, "random_fish": False}}
        rows, *_ = run("gather", sc, [{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual(events(rows, "gather")[0]["data"], {"node_id": "N5", "kind": "keo_neo", "amount": 1})
        sc = {"gather": {"player": {"pos": [40, 25]}, "random_fish": False,
                         "fish": [{"id": "F1", "kind": "ca_keo", "pos": [40, 25]}]}}
        rows, *_ = run("gather", sc, [{"tick": 0, "catch": True}], ticks=1)
        self.assertEqual(events(rows, "fish_caught")[0]["data"], {"fish_id": "F1", "kind": "ca_keo", "yield": 2})


# ----------------------------------------------------------------------------------------------- Cá Sấu
def croc(**kw):
    m = {"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]}
    m.update(kw)
    return m


class Crocodile(unittest.TestCase):
    QUIET = {"random_fish": False, "fish": []}

    def test_default_layout_day1_and_patrol(self):
        rows, code, err = run("gather", {"gather": dict(self.QUIET)}, ticks=241)
        self.assertEqual(code, 0, err)
        s0 = snapshots(rows)[0]["monsters"]
        self.assertEqual([m["id"] for m in s0], ["M1"], "gather độc lập dùng bố trí Ngày 1")
        self.assertEqual((s0[0]["target_idx"], s0[0]["state"]), (1, "patrol"))
        m60 = snap_at(rows, 60)["monsters"][0]
        self.assertAlmostEqual(m60["pos"][0], 61.0, places=2)
        m240 = snap_at(rows, 240)["monsters"][0]
        self.assertEqual((m240["pos"], m240["target_idx"]), ([64, 24], 0), "tới waypoint thì đổi mục tiêu cho bước sau")
        self.assertLess(snap_at(rows, 241)["monsters"][0]["pos"][0], 64)

    def test_chase_when_deep_and_close_then_exit_when_shallow(self):
        sc = {"gather": dict(self.QUIET, player={"pos": [60, 15]})}
        rows, code, err = run("gather", sc, [{"tick": 0}, {"tick": 5, "move": [0, -1]}], ticks=150)
        self.assertEqual(code, 0, err)
        m1 = snap_at(rows, 1)["monsters"][0]
        self.assertEqual(m1["state"], "chase")
        self.assertAlmostEqual(m1["pos"][1], 24 - G["monsters"]["species"]["ca_sau"]["chase_speed"] / 60, places=3)
        self.assertEqual(snapshots(rows)[-1]["monsters"][0]["state"], "patrol", "người chơi lên d < 10 -> patrol")

    def test_hit_loses_hp_drops_half_lifo_invuln_recoil(self):
        hold = items("ca_loc", "bong_sung", "ca_linh", "ca_linh", "ca_keo")
        sc = {"gather": dict(self.QUIET, hold=hold, player={"pos": [60, 24]},
                             monsters=[croc(state="patrol")])}
        rows, code, err = run("gather", sc, ticks=90)  # bất tử đặt ở tick 1 -> hết ở tick 91
        self.assertEqual(code, 0, err)
        hit = events(rows, "monster_hit")
        self.assertEqual(len(hit), 1, "trong 90 tick bất tử không có hit thứ hai")
        self.assertEqual(hit[0]["tick"], 1)
        self.assertEqual(hit[0]["data"]["monster_id"], "M1")
        self.assertEqual(hit[0]["data"]["hp"], G["hp_max"] - 1)
        self.assertEqual([(i["id"], i["kind"]) for i in hit[0]["data"]["lost"]], [("I5", "ca_keo"), ("I4", "ca_linh")])
        s1 = snap_at(rows, 1)
        self.assertEqual([i["id"] for i in s1["hold"]], ["I1", "I2", "I3"])
        self.assertEqual(s1["player"]["invuln_ticks"], G["monsters"]["invuln_ticks"])
        m = s1["monsters"][0]
        self.assertEqual((m["state"], m["state_ticks_left"]), ("recoil", 60))
        self.assertEqual(len(m["recoil_dir"]), 2)
        m61 = snap_at(rows, 61)["monsters"][0]
        self.assertEqual(m61["state"], "patrol")
        d = math.dist(m61["pos"], s1["monsters"][0]["pos"])
        self.assertAlmostEqual(d, G["monsters"]["species"]["ca_sau"]["recoil_dist"], places=2)

    def test_same_center_recoils_plus_x(self):
        sc = {"gather": dict(self.QUIET, player={"pos": [50, 20]}, monsters=[croc(pos=[50, 20])])}
        rows, *_ = run("gather", sc, ticks=1)
        self.assertEqual(snapshots(rows)[-1]["monsters"][0]["recoil_dir"], [1, 0])

    def test_no_hit_when_shallow_or_invulnerable(self):
        sc = {"gather": dict(self.QUIET, player={"pos": [60, 9.9]}, monsters=[croc(pos=[60, 10])])}
        self.assertEqual(events(run("gather", sc, ticks=1)[0], "monster_hit"), [])
        sc = {"gather": dict(self.QUIET, player={"pos": [60, 24], "invuln_ticks": 5}, monsters=[croc()])}
        self.assertEqual(events(run("gather", sc, ticks=1)[0], "monster_hit"), [])

    def test_monster_faint_lists_remaining_hold(self):
        sc = {"gather": dict(self.QUIET, hold=items("ca_loc", "bong_sung", "ca_linh"), player={"pos": [60, 24], "hp": 1},
                             monsters=[croc()])}
        rows, code, err = run("gather", sc, ticks=5)
        self.assertEqual(code, 0, err)
        self.assertEqual(names(rows), ["monster_hit", "faint", "gather_end"])
        self.assertEqual([i["id"] for i in events(rows, "monster_hit")[0]["data"]["lost"]], ["I3"])
        faint = events(rows, "faint")[0]["data"]
        self.assertEqual((faint["cause"], [i["id"] for i in faint["lost"]], faint["hp"]), ("monster", ["I2", "I1"], 0))
        self.assertEqual(events(rows, "gather_end")[0]["data"]["inventory"], {"items": []})

    def test_bad_monster_fixture_exit_2(self):
        for m in (croc(pos=[60, 5]), croc(state="recoil"), croc(waypoints=[[60, 24]]), croc(kind="ran"),
                  croc(target_idx=2), croc(state_ticks_left=3)):
            _, code, _ = run("gather", {"gather": {"monsters": [m]}}, ticks=0)
            self.assertEqual(code, 2, m)


# ----------------------------------------------------------------------------------------------- quán v1.1
class QuanV11(unittest.TestCase):
    def test_next_free_table_and_schedule(self):
        cust = [{"id": "C1", "table_id": "T1", "dish_id": "ca_keo_nuong"}]
        sc = {"quan": {"stock": stock(ca_keo=6), "customers": cust}}
        rows, code, err = run("quan", sc, ticks=1020, every=10000)
        self.assertEqual(code, 0, err)
        ev = events(rows, "customer_arrived")
        self.assertEqual([(e["tick"], e["data"]["table_id"]) for e in ev], [(120, "T2"), (1020, "T3")])
        self.assertEqual({e["data"]["dish_id"] for e in ev}, {"ca_keo_nuong"}, "quán riêng dùng cả 6 món")

    def test_second_stove_b2(self):
        cust = [{"id": "C1", "table_id": "T1", "dish_id": "lau_mam"}]
        stk = stock(ca_linh=2, ca_keo=1, keo_neo=1, bong_dien_dien=1)
        sc = {"quan": {"stock": stk, "customers": cust, "random_customers": False,
                       "player": {"pos": Q["stoves"][1]["pos"]}}}
        rows, code, err = run("quan", sc, [{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual(code, 0, err)
        ev = events(rows, "cook_started")[0]["data"]
        self.assertEqual((ev["stove_id"], ev["base_price"]), ("B2", 199))  # floor(200 × (100 − 1/240) / 100)
        self.assertEqual(kinds(ev["items"]), ["bong_dien_dien", "ca_keo", "ca_linh", "ca_linh", "keo_neo"])


# ----------------------------------------------------------------------------------------------- pause
class Pause(unittest.TestCase):
    def test_pause_freezes_gameplay_and_resume_runs_same_step(self):
        inp = [{"tick": 5, "pause": True}, {"tick": 6, "pause": False, "interact": True},
               {"tick": 10, "pause": True, "interact": False}]
        rows, code, err = run("gather", {"gather": {"random_fish": False}}, inp, ticks=12)
        self.assertEqual(code, 0, err)
        self.assertEqual([(e["tick"], e["name"]) for e in events(rows)], [(6, "paused"), (11, "resumed")])
        s = {r["tick"]: r for r in snapshots(rows)}
        self.assertEqual((s[6]["state"], s[6]["sim_tick"]), ("paused", 5))
        self.assertEqual((s[10]["sim_tick"], s[10]["time_left_ticks"]), (5, s[6]["time_left_ticks"]))
        self.assertEqual((s[11]["state"], s[11]["sim_tick"]), ("playing", 6))
        self.assertEqual(rows[-1]["sim_tick"], 7)
        self.assertNotIn("gather_end", names(rows), "cạnh interact trong lúc pause bị bỏ qua")

    def test_pause_in_quan(self):
        rows, code, err = run("quan", {"quan": {"stock": []}}, [{"tick": 0, "pause": True}], ticks=200, every=1000)
        self.assertEqual(code, 0, err)
        self.assertEqual(names(rows), ["paused"], "lịch khách đứng yên khi pause")
        self.assertEqual(rows[-1]["sim_tick"], 0)


# ----------------------------------------------------------------------------------------------- day
def dock_day(extra=None, gather=None):
    sc = {"gather": dict({"hold": items("ca_loc", "bong_sung", "bong_sung"), "random_fish": False}, **(gather or {}))}
    if extra:
        sc["day"] = extra
    return sc


class Day(unittest.TestCase):
    def test_one_day_phase_sequence(self):
        t0 = time.time()
        rows, code, err = run("day", ticks=30000, every=600)
        self.assertEqual(code, 0, err)
        self.assertLess(time.time() - t0, 20, "headless một Ngày ≤ 20 s")
        ev = [(e["tick"], e["phase"], e["day"], e["name"]) for e in events(rows)
              if e["name"] not in ("fish_spawned", "no_dish", "customer_arrived", "customer_left")]
        self.assertEqual(ev[:3], [(0, "gather", 1, "day_start"), (0, "gather", 1, "day_plan"), (0, "gather", 1, "phase_start")])
        self.assertEqual(ev[3:], [(GATHER_T, "gather", 1, "gather_end"), (GATHER_T, "quan", 1, "phase_start"),
                                  (GATHER_T + QUAN_T, "quan", 1, "quan_end"), (GATHER_T + QUAN_T, "shop", 1, "phase_start"),
                                  (22200, "shop", 1, "shop_end")])
        self.assertEqual(events(rows, "day_plan")[0]["data"], {k: T["day_plan"][0][k] for k in ("dishes", "ingredients")})
        end = rows[-1]
        self.assertEqual((end["ticks"], end["reason"], end["days_completed"], end["state"]), (22200, "days_complete", 1, "finished"))
        s = snap_at(rows, GATHER_T)
        self.assertEqual((s["phase"], s["phase_tick"]), ("quan", 0), "snapshot đổi pha ghi pha mới, phase_tick 0")
        s = snap_at(rows, 0)
        for k in ("day", "day_plan", "upgrades", "active_upgrades"):
            self.assertIn(k, s)

    def test_dock_handover_plan_filter_and_shop_buy_applies_next_day(self):
        q_open = 1
        shop_open = q_open + QUAN_T
        inp = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
               {"tick": shop_open, "buy": "oxygen"}, {"tick": shop_open + 1, "buy": "hp"},
               {"tick": shop_open + 2, "shop_done": True}]
        sc = dock_day({"money": 200, "earned": 200}, {"hold": items("ca_keo", "ca_keo", "ca_loc")})
        rows, code, err = run("day", sc, inp, ticks=shop_open + 4, every=1, extra=("--days", "2"))
        self.assertEqual(code, 0, err)
        self.assertEqual(kind_counts(snap_at(rows, q_open)["stock"]), {"ca_keo": 2, "ca_loc": 1})
        arrived = events(rows, "customer_arrived")
        self.assertEqual(arrived[0]["data"]["dish_id"], "ca_loc_nuong_trui", "Ngày 1 chỉ bán món trong kế hoạch")
        self.assertEqual(events(rows, "bought")[0]["data"], {"upgrade": "oxygen", "level": 1, "price": 200, "money": 0})
        self.assertEqual(events(rows, "buy_failed")[0]["data"], {"action": "hp", "reason": "funds"})
        self.assertEqual(events(rows, "shop_end")[0]["data"], {"reason": "done"})
        s = snap_at(rows, shop_open + 3)
        self.assertEqual((s["day"], s["phase"], s["upgrades"], s["active_upgrades"]), (2, "gather", {"oxygen": 1}, {"oxygen": 1}))
        self.assertEqual(s["player"]["oxygen_max_ticks"], 2700)
        self.assertEqual(s["player"]["oxygen_ticks"], 2700)
        self.assertEqual(kinds(s["hold"]), ["ca_keo", "ca_keo", "ca_loc"], "gather.hold là mẫu khởi tạo mỗi Ngày")
        self.assertEqual([i["id"] for i in s["hold"]], ["I4", "I5", "I6"], "v1.2: Ngày kế cấp id mới theo thứ tự mảng")
        self.assertEqual([i["fresh"] for i in s["hold"]], [100, 100, 100])
        s_shop = snap_at(rows, shop_open + 1)
        self.assertEqual((s_shop["upgrades"], s_shop["active_upgrades"]), ({"oxygen": 1}, {}))
        self.assertEqual(s_shop["earned"], 200, "mua trừ money, giữ earned")

    def test_buy_max_level_unknown_and_exact_price(self):
        inp = [{"tick": 0, "interact": True}, {"tick": 1 + QUAN_T, "buy": "hp"},
               {"tick": 2 + QUAN_T, "buy": "weapon"}, {"tick": 3 + QUAN_T, "buy": "oxygen"}]
        sc = dock_day({"money": 400, "earned": 400, "upgrades": {"hp": 2, "oxygen": 1}})
        rows, code, err = run("day", sc, inp, ticks=QUAN_T + 5, every=100000)
        self.assertEqual(code, 0, err)
        self.assertEqual([e["data"] for e in events(rows, "buy_failed")],
                         [{"action": "hp", "reason": "max_level"}, {"action": "weapon", "reason": "unknown"}])
        self.assertEqual(events(rows, "bought")[0]["data"], {"upgrade": "oxygen", "level": 2, "price": 400, "money": 0})
        self.assertEqual(snapshots(rows)[0]["player"]["hp_max"], 5, "cấp có sẵn trong scenario áp dụng từ Ngày 1")

    def test_faint_still_opens_quan_with_empty_stock(self):
        sc = dock_day(gather={"player": {"pos": [50, 10], "oxygen_ticks": 0, "hp": 1, "zero_oxy_ticks": 59}})
        rows, code, err = run("day", sc, ticks=3, every=1)
        self.assertEqual(code, 0, err)
        self.assertEqual(names(rows)[3:], ["choke", "faint", "gather_end", "phase_start"])
        self.assertEqual(snap_at(rows, 1)["stock"], [])

    def test_three_days_m2_from_day3_and_hp_refill(self):
        day3_start = 1 + QUAN_T + SHOP_T + 22200  # Ngày 1 cập bến ở tick 1; Ngày 2 chạy đủ 22.200 tick
        rows, code, err = run("day", dock_day(), [{"tick": 0, "interact": True}], ticks=day3_start, every=100000,
                              extra=("--days", "3"))
        self.assertEqual(code, 0, err)
        self.assertEqual(rows[-1]["days_completed"], 2)
        starts = [e["tick"] for e in events(rows, "day_start")]
        self.assertEqual(starts[2], day3_start)
        self.assertEqual(starts[1], 1 + QUAN_T + SHOP_T)  # Ngày 1 cập bến ở tick 1, Shop tự đóng sau 600 tick
        day3 = snap_at(rows, starts[2])
        self.assertEqual([m["id"] for m in day3["monsters"]], ["M1", "M2"])
        self.assertEqual(day3["player"]["hp"], G["hp_max"])

    def test_day_scenario_conflicts_exit_2(self):
        bad = [
            {"quan": {"stock": stock(ca_loc=1)}},
            {"quan": {"reputation": 4}},
            {"day": {"money": 300, "earned": 100}},
            {"day": {"money": 100}},
            {"day": {"upgrades": {"hp": 3}}},
            {"day": {"upgrades": {"weapon": 1}}},
            {"day": {"day_plan": [{"day": 1, "dishes": {"goi_bong_sung": 1}, "ingredients": {"bong_sung": 3}}]}},
            {"day": {"day_plan": [{"day": 1, "dishes": {"pho": 1}}]}},
            {"day": {"nope": 1}},
        ]
        for sc in bad:
            self.assertEqual(run("day", sc, ticks=0)[1], 2, sc)
        ok = {"day": {"money": 200, "earned": 200, "day_plan": [{"day": 1, "dishes": {"goi_bong_sung": 1}}]}}
        rows, code, err = run("day", ok, ticks=0)
        self.assertEqual(code, 0, err)
        self.assertEqual(events(rows, "day_plan")[0]["data"], {"dishes": {"goi_bong_sung": 1}, "ingredients": {"bong_sung": 2}})

    def test_runtime_conflict_at_quan_open_exit_2(self):
        sc = dock_day(extra=None)
        sc["quan"] = {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "lau_mam"}]}  # không thuộc kế hoạch D1
        self.assertEqual(run("day", sc, [{"tick": 0, "interact": True}], ticks=5)[1], 2)

    def test_cli_days_rules(self):
        for args in (("--mode", "day", "--days", "6"), ("--mode", "day", "--days", "0"), ("--mode", "gather", "--days", "1")):
            with Workdir() as w:
                code, _ = run_headless(*args, "--seed", "1", "--ticks", "0", "--out", w.path("o.jsonl"))
                self.assertEqual(code, 2, args)
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": []})
            self.assertEqual(run_headless("--mode", "day", "--seed", "1", "--ticks", "0", "--inventory", inv,
                                          "--out", w.path("o.jsonl"))[0], 2)

    def test_day_deterministic(self):
        a, *_ = run("day", ticks=22200, seed=11, every=500)
        b, *_ = run("day", ticks=22200, seed=11, every=500)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
