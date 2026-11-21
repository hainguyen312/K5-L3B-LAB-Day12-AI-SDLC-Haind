"""Test luật Phase 1 của nhóm Haind theo PRD-0 (mục D, E, F, G) — hộp đen qua headless như test_smoke_p1.py.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_rules_p1 -v
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


G, Q, MENU = tuning()["gather"], tuning()["quan"], tuning()["menu"]
PMAX = int(Q["patience_s"] * 60)
EAT = int(Q["eat_s"] * 60)
STOVE, TABLE = Q["stoves"][0]["pos"], Q["tables"][0]["pos"]


def run(mode, block, inputs=None, ticks=10, seed=1, every=1, inv_out=False):
    """Chạy headless; trả (rows, code, stderr, inventory|None)."""
    with Workdir() as w:
        args = ["--mode", mode, "--seed", str(seed), "--ticks", str(ticks), "--snapshot-every", str(every),
                "--out", w.path("o.jsonl")]
        if block is not None:
            args += ["--scenario", write_json(w.path("sc.json"), {mode: block})]
        if inputs is not None:
            args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
        if inv_out:
            args += ["--inventory-out", w.path("inv.json")]
        code, err = run_headless(*args)
        rows = read_jsonl(w.path("o.jsonl")) if code == 0 else []
        inv = None
        if inv_out:
            try:
                with open(w.path("inv.json"), encoding="utf-8") as f:
                    inv = json.load(f)
            except OSError:
                pass
        return rows, code, err, inv


def names(rows):
    return [r["name"] for r in events(rows)]


def last(rows):
    return snapshots(rows)[-1]


# ----------------------------------------------------------------------------------------------- gather
class GatherOxygen(unittest.TestCase):
    def test_drain_refill_clamp(self):
        omax = G["oxygen_max_s"] * 60
        rows, code, err, _ = run("gather", {"player": {"pos": [50, 10]}}, ticks=5)
        self.assertEqual(code, 0, err)
        self.assertEqual(last(rows)["player"]["oxygen_ticks"], omax - 5)
        rows, *_ = run("gather", {"player": {"pos": [50, 0.5], "oxygen_ticks": 100}}, ticks=2)
        self.assertEqual(last(rows)["player"]["oxygen_ticks"], 100 + 2 * G["oxygen_refill_per_tick"],
                         "d = surface_depth vẫn là mặt nước")
        rows, *_ = run("gather", {"player": {"pos": [50, 0], "oxygen_ticks": omax - 1}}, ticks=1)
        self.assertEqual(last(rows)["player"]["oxygen_ticks"], omax)

    def test_oxygen_empty_then_first_choke_at_t_plus_59(self):
        iv = G["choke_interval_ticks"]
        rows, code, err, _ = run("gather", {"player": {"pos": [50, 10], "oxygen_ticks": 1}}, ticks=iv + 5)
        self.assertEqual(code, 0, err)
        ev = events(rows)
        self.assertEqual([e["name"] for e in ev], ["oxygen_empty", "choke"])
        self.assertEqual(ev[0]["data"], {"oxygen_ticks": 0})
        t = ev[0]["tick"]
        self.assertEqual(ev[1]["tick"], t + iv - 1)
        self.assertEqual(ev[1]["data"], {"hp": G["hp_max"] - 1})

    def test_surface_on_choke_step_refills_no_choke(self):
        sc = {"player": {"pos": [50, 0.505], "oxygen_ticks": 0, "zero_oxy_ticks": 59}}
        rows, code, err, _ = run("gather", sc, [{"tick": 0, "move": [0, -1]}], ticks=1)
        self.assertEqual(code, 0, err)
        self.assertEqual(names(rows), ["surface"])
        p = last(rows)["player"]
        self.assertEqual((p["oxygen_ticks"], p["zero_oxy_ticks"], p["hp"]), (G["oxygen_refill_per_tick"], 0, G["hp_max"]))

    def test_faint_drops_hold_lifo_and_empty_inventory(self):
        sc = {"hold": ["ca_loc", "bong_sung"], "player": {"pos": [50, 10], "oxygen_ticks": 0, "hp": 1,
                                                          "zero_oxy_ticks": 59}}
        rows, code, err, inv = run("gather", sc, ticks=10, inv_out=True)
        self.assertEqual(code, 0, err)
        self.assertEqual(names(rows), ["choke", "faint", "gather_end"])
        self.assertEqual(events(rows, "faint")[0]["data"], {"cause": "choke", "lost": ["bong_sung", "ca_loc"], "hp": 0})
        self.assertEqual(events(rows, "gather_end")[0]["data"], {"reason": "fainted", "inventory": {"items": {}}})
        self.assertEqual(rows[-1]["reason"], "fainted")
        self.assertEqual(rows[-1]["ticks"], 1, "dừng sớm")
        self.assertEqual(inv, {"items": {}})

    def test_dive_and_surface_once_per_crossing(self):
        rows, code, err, _ = run("gather", {"player": {"pos": [50, 0]}},
                                 [{"tick": 0, "move": [0, 1]}, {"tick": 30, "move": [0, -1]}], ticks=80)
        self.assertEqual(code, 0, err)
        self.assertEqual(names(rows), ["dive", "surface"])
        self.assertGreater(events(rows, "dive")[0]["data"]["pos"][1], G["surface_depth"])


class GatherHarvest(unittest.TestCase):
    def test_prd_example_node_on_radius_edge(self):
        sc = {"player": {"pos": [20, 0], "heading_deg": 0}, "hold": ["ca_loc", "bong_sung"],
              "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [22, 0]}], "fish": [],
              "random_fish": False, "time_left_ticks": 120}
        rows, code, err, _ = run("gather", sc, [{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual(code, 0, err)
        ev = events(rows, "gather")[0]
        self.assertEqual((ev["tick"], ev["data"]), (1, {"node_id": "N1", "kind": "bong_dien_dien", "amount": 1}))
        s = last(rows)
        self.assertEqual(s["hold"], ["ca_loc", "bong_sung", "bong_dien_dien"])
        self.assertEqual(s["nodes"][0]["regrow_ticks"], int(G["regrow_s"] * 60))
        self.assertFalse(s["nodes"][0]["ready"])

    def test_regrow_event_and_harvest_again(self):
        regrow = int(G["regrow_s"] * 60)
        inp = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False}, {"tick": regrow, "interact": True}]
        rows, code, err, _ = run("gather", {"player": {"pos": [12, 0]}}, inp, ticks=regrow + 1, every=10000)
        self.assertEqual(code, 0, err)
        ev = events(rows)
        self.assertEqual([e["name"] for e in ev], ["gather", "node_regrown", "gather"])
        self.assertEqual(ev[1]["tick"], 1 + regrow)
        self.assertEqual(ev[1]["data"], {"node_id": "N1"})
        self.assertEqual(ev[2]["tick"], 1 + regrow, "nút về 0 có thể hái ngay trong cùng bước")

    def test_no_harvest_underwater_or_far(self):
        for pos in ([12, 1], [15, 0]):
            rows, code, err, _ = run("gather", {"player": {"pos": pos}}, [{"tick": 0, "interact": True}], ticks=1)
            self.assertEqual(code, 0, err)
            self.assertEqual(names(rows), [], pos)

    def test_tie_breaks_by_id(self):
        nodes = [{"id": "N10", "kind": "bong_dien_dien", "pos": [13, 0]}, {"id": "N2", "kind": "bong_sung", "pos": [11, 0]}]
        rows, *_ = run("gather", {"player": {"pos": [12, 0]}, "nodes": nodes}, [{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual(events(rows, "gather")[0]["data"]["node_id"], "N2")

    def test_hold_full_on_gather(self):
        cap = G["hold_capacity"]
        rows, code, err, _ = run("gather", {"player": {"pos": [12, 0]}, "hold": ["ca_loc"] * cap},
                                 [{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual(code, 0, err)
        self.assertEqual(events(rows)[0]["data"], {"action": "gather", "node_id": "N1", "required": 1, "free": 0})
        self.assertTrue(last(rows)["nodes"][0]["ready"])

    def test_dock_has_priority_and_writes_inventory(self):
        rows, code, err, inv = run("gather", {"hold": ["ca_linh"], "time_left_ticks": 1},
                                   [{"tick": 0, "interact": True}], ticks=5, inv_out=True)
        self.assertEqual(code, 0, err)
        self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked", "docked ưu tiên ở bước cuối")
        self.assertEqual(inv, {"items": {"ca_linh": 1}})

    def test_harvest_on_last_step_counts(self):
        rows, code, err, inv = run("gather", {"player": {"pos": [12, 0]}, "time_left_ticks": 1},
                                   [{"tick": 0, "interact": True}], ticks=5, inv_out=True)
        self.assertEqual(code, 0, err)
        self.assertEqual(names(rows), ["gather", "gather_end"])
        self.assertEqual(events(rows, "gather_end")[0]["data"],
                         {"reason": "time", "inventory": {"items": {"bong_dien_dien": 1}}})
        self.assertEqual(inv, {"items": {"bong_dien_dien": 1}})


class GatherCatch(unittest.TestCase):
    FISH = [{"id": "F1", "kind": "ca_linh", "pos": [20, 5]}, {"id": "F2", "kind": "ca_loc", "pos": [21, 5]}]

    def test_catch_yield_removes_school(self):
        rows, code, err, _ = run("gather", {"player": {"pos": [20, 5]}, "fish": self.FISH},
                                 [{"tick": 0, "catch": True}], ticks=1)
        self.assertEqual(code, 0, err)
        self.assertEqual(events(rows)[0]["data"], {"fish_id": "F1", "kind": "ca_linh", "yield": G["fish_yield"]["ca_linh"]})
        s = last(rows)
        self.assertEqual(s["hold"], ["ca_linh"] * G["fish_yield"]["ca_linh"])
        self.assertEqual([f["id"] for f in s["fish"]], ["F2"])
        self.assertEqual(s["player"]["catch_cd_ticks"], int(G["catch_cooldown_s"] * 60))

    def test_cooldown_reuse_from_t_plus_L(self):
        cd = int(G["catch_cooldown_s"] * 60)
        for second, want in ((cd - 1, ["F1"]), (cd, ["F1", "F2"])):
            inp = [{"tick": 0, "catch": True}, {"tick": 1, "catch": False}, {"tick": second, "catch": True}]
            rows, *_ = run("gather", {"player": {"pos": [20, 5]}, "fish": self.FISH}, inp, ticks=second + 1)
            ev = events(rows, "fish_caught")
            self.assertEqual([e["data"]["fish_id"] for e in ev], want, second)
            if len(ev) == 2:
                self.assertEqual(ev[1]["tick"] - ev[0]["tick"], cd)

    def test_miss_has_no_event_and_no_cooldown(self):
        rows, code, err, _ = run("gather", {"player": {"pos": [50, 5]}, "fish": self.FISH},
                                 [{"tick": 0, "catch": True}], ticks=1)
        self.assertEqual(code, 0, err)
        self.assertEqual(names(rows), [])
        self.assertEqual(last(rows)["player"]["catch_cd_ticks"], 0)

    def test_hold_full_on_catch_keeps_school_and_cooldown(self):
        cap = G["hold_capacity"]
        rows, code, err, _ = run("gather", {"player": {"pos": [20, 5]}, "fish": self.FISH, "hold": ["ca_loc"] * (cap - 1)},
                                 [{"tick": 0, "catch": True}], ticks=1)
        self.assertEqual(code, 0, err)
        self.assertEqual(events(rows)[0]["data"], {"action": "catch", "fish_id": "F1", "required": 3, "free": 1})
        s = last(rows)
        self.assertEqual(len(s["fish"]), 2, "không thử đàn khác")
        self.assertEqual(s["player"]["catch_cd_ticks"], 0)

    def test_no_catch_at_surface(self):
        rows, *_ = run("gather", {"player": {"pos": [20, 0.5]}, "fish": [{"id": "F1", "kind": "ca_loc", "pos": [20, 1]}]},
                       [{"tick": 0, "catch": True}], ticks=1)
        self.assertEqual(names(rows), [])

    def test_deterministic_full_run(self):
        inp = [{"tick": 0, "move": [1, 0.3]}, {"tick": 200, "catch": True}, {"tick": 400, "move": [-1, -1]}]
        a, *_ = run("gather", None, inp, ticks=900, seed=5, every=10)
        b, *_ = run("gather", None, inp, ticks=900, seed=5, every=10)
        self.assertEqual(a, b)


# ----------------------------------------------------------------------------------------------- quan
def walk_inputs(start, frm, to, speed=Q["walk_speed"]):
    """Frames đi thẳng từ `frm` tới `to` bắt đầu ở tick `start`; trả (frames, tick dừng)."""
    dx, dz = to[0] - frm[0], to[1] - frm[1]
    n = (dx * dx + dz * dz) ** 0.5
    walk = int(n / speed * 60) + 1
    return [{"tick": start, "move": [dx / n, dz / n]}, {"tick": start + walk, "move": [0, 0]}], start + walk


class QuanCustomers(unittest.TestCase):
    def test_first_customer_reserves_recipe(self):
        rows, code, err, _ = run("quan", {"stock": {"ca_loc": 1}}, ticks=Q["first_customer_tick"])
        self.assertEqual(code, 0, err)
        ev = events(rows, "customer_arrived")
        self.assertEqual((ev[0]["tick"], ev[0]["data"]),
                         (Q["first_customer_tick"], {"order_id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}))
        c = last(rows)["customers"][0]
        self.assertEqual((c["order_tick"], c["patience_ticks_left"], c["order_status"], c["reserved"], c["state"]),
                         (Q["first_customer_tick"], PMAX, "reserved", {"ca_loc": 1}, "waiting"))
        self.assertEqual(last(rows)["tables"][0]["customer_id"], "C1")
        self.assertEqual(last(rows)["stock"], {"ca_loc": 1}, "stock gồm cả phần giữ chỗ")

    def test_schedule_by_phase_tick_even_when_shift_shortened(self):
        rows, code, err, _ = run("quan", {"stock": {"ca_loc": 1}, "time_left_ticks": 200}, ticks=Q["first_customer_tick"])
        self.assertEqual(code, 0, err)
        self.assertEqual(events(rows, "customer_arrived")[0]["tick"], Q["first_customer_tick"])

    def test_no_dish_when_no_available_stock(self):
        rows, code, err, _ = run("quan", {"stock": {"bong_sung": 1}}, ticks=Q["first_customer_tick"])
        self.assertEqual(code, 0, err)
        ev = events(rows)
        self.assertEqual([(e["name"], e["data"]) for e in ev], [("no_dish", {})])

    def test_no_table_skips_silently(self):
        cust = [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]
        rows, code, err, _ = run("quan", {"stock": {"ca_loc": 5}, "customers": cust}, ticks=Q["first_customer_tick"])
        self.assertEqual(code, 0, err)
        self.assertEqual(names(rows), [])

    def test_patience_leave_releases_reservation(self):
        cust = [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "patience_ticks_left": 3}]
        rows, code, err, _ = run("quan", {"stock": {"bong_sung": 2}, "customers": cust, "random_customers": False}, ticks=4)
        self.assertEqual(code, 0, err)
        ev = events(rows, "customer_left")[0]
        self.assertEqual(ev["tick"], 3)
        rep = Q["reputation_initial"] + Q["left_reputation_delta"]
        self.assertEqual(ev["data"], {"order_id": "C1", "table_id": "T1", "reason": "patience", "reputation": rep})
        s = last(rows)
        self.assertEqual((s["customers"], s["stock"], s["tables"][0]["customer_id"]), ([], {"bong_sung": 2}, None))

    def test_new_customer_patience_starts_next_step(self):
        t0 = Q["first_customer_tick"]
        rows, *_ = run("quan", {"stock": {"ca_loc": 1}}, ticks=t0 + 2)
        s = {r["tick"]: r for r in snapshots(rows)}
        self.assertEqual(s[t0]["customers"][0]["patience_ticks_left"], PMAX)
        self.assertEqual(s[t0 + 2]["customers"][0]["patience_ticks_left"], PMAX - 2)


class QuanService(unittest.TestCase):
    def test_full_loop_cook_pick_serve_pay(self):
        dish = "goi_bong_sung"
        cook = int(MENU[dish]["cook_s"] * 60)
        price = MENU[dish]["price"]
        sc = {"stock": {"bong_sung": 2}, "customers": [{"id": "C1", "table_id": "T1", "dish_id": dish}],
              "random_customers": False, "player": {"pos": STOVE}}
        walk, t_stop = walk_inputs(cook + 2, STOVE, TABLE)
        inp = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False}, {"tick": cook, "interact": True},
               {"tick": cook + 1, "interact": False}] + walk + [{"tick": t_stop + 5, "interact": True}]
        rows, code, err, _ = run("quan", sc, inp, ticks=t_stop + 6 + EAT, every=100000)
        self.assertEqual(code, 0, err)
        ev = {e["name"]: e for e in events(rows)}
        self.assertEqual(names(rows), ["cook_started", "dish_ready", "dish_picked", "served", "paid"])
        self.assertEqual(ev["cook_started"]["data"], {"stove_id": "B1", "order_id": "C1", "dish_id": dish,
                                                      "items": ["bong_sung", "bong_sung"], "base_price": price})
        self.assertEqual(ev["dish_ready"]["tick"], 1 + cook)
        self.assertEqual(ev["dish_ready"]["data"], {"stove_id": "B1", "order_id": "C1", "dish_id": dish})
        self.assertEqual(ev["dish_picked"]["tick"], 1 + cook, "món chín đầu bước được lấy ngay trong bước")
        tip = (price * 2) // 10  # floor(price × 0.2)
        sv = ev["served"]["data"]
        self.assertEqual((sv["order_id"], sv["table_id"], sv["base_price"], sv["tip"]), ("C1", "T1", price, tip))
        self.assertEqual(ev["paid"]["tick"], ev["served"]["tick"] + EAT)
        self.assertEqual(ev["paid"]["data"], {"order_id": "C1", "table_id": "T1", "base_price": price, "tip": tip,
                                              "amount": price + tip, "reason": "finished_eating"})
        end = rows[-1]
        rep = Q["reputation_initial"] + Q["tip_reputation"]
        self.assertEqual((end["money"], end["earned"]), (price + tip, price + tip))
        self.assertAlmostEqual(end["reputation"], rep, places=2)
        self.assertEqual(end["score"], price + tip + 100 * int(rep))
        s = last(rows)
        self.assertEqual((s["stock"], s["customers"], s["hand"]), ({}, [], None))

    def _serve_with_patience(self, patience):
        cust = [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned",
                 "patience_ticks_left": patience, "reserved": {}}]
        hand = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        rows, code, err, _ = run("quan", {"customers": cust, "hand": hand, "random_customers": False,
                                          "player": {"pos": TABLE}}, [{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual(code, 0, err)
        return rows

    def test_tip_threshold_uses_patience_after_step_1(self):
        half = int(PMAX * Q["tip_min_patience_ratio"])
        self.assertEqual(events(self._serve_with_patience(half + 1), "served")[0]["data"]["tip"], 12)
        self.assertEqual(events(self._serve_with_patience(half), "served")[0]["data"]["tip"], 0)

    def test_serve_on_patience_zero_tick_is_valid(self):
        rows = self._serve_with_patience(1)
        self.assertEqual(names(rows), ["served"])
        self.assertEqual(events(rows)[0]["data"]["patience_ticks_left"], 0)
        self.assertEqual(last(rows)["customers"][0]["state"], "eating")

    def test_wrong_order_in_hand_not_served(self):
        cust = [{"id": "C2", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "unfulfillable",
                 "reserved": {}}]
        rows, code, err, _ = run("quan", {"customers": cust, "random_customers": False, "player": {"pos": TABLE}},
                                 [{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual(code, 0, err)
        self.assertEqual(names(rows), [])

    def test_ready_ticks_increase_while_on_stove(self):
        cust = [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned", "reserved": {}}]
        stove = [{"id": "B1", "state": "ready", "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}}]
        rows, code, err, _ = run("quan", {"customers": cust, "stoves": stove, "random_customers": False}, ticks=5)
        self.assertEqual(code, 0, err)
        self.assertEqual(last(rows)["stoves"][0]["ready_ticks"], 5)

    def test_customer_leaving_discards_dish_no_refund(self):
        cust = [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned",
                 "reserved": {}, "patience_ticks_left": 1}]
        stove = [{"id": "B1", "state": "cooking", "cook_ticks_left": 100,
                  "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}}]
        rows, code, err, _ = run("quan", {"customers": cust, "stoves": stove, "random_customers": False}, ticks=2)
        self.assertEqual(code, 0, err)
        self.assertEqual(names(rows), ["customer_left"])
        st = last(rows)["stoves"][0]
        self.assertEqual((st["state"], st["dish"], st["cook_ticks_left"]), ("idle", None, 0))
        self.assertEqual(last(rows)["stock"], {})


class QuanClosing(unittest.TestCase):
    def test_closing_pays_eating_customer_prd_end_example(self):
        cust = [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating",
                 "order_status": "served", "eat_ticks_left": 300, "base_price": 60, "tip": 12}]
        rows, code, err, _ = run("quan", {"customers": cust, "time_left_ticks": 1, "random_customers": False}, ticks=5)
        self.assertEqual(code, 0, err)
        self.assertEqual(names(rows), ["paid", "quan_end"])
        self.assertEqual(events(rows, "paid")[0]["data"]["reason"], "closing")
        self.assertEqual(events(rows, "quan_end")[0]["data"],
                         {"reason": "time", "money": 72, "earned": 72, "shift_earned": 72, "reputation": 3.2})
        end = rows[-1]
        self.assertEqual((end["money"], end["earned"], end["score"], end["reason"]), (72, 72, 372, "time"))

    def test_closing_waiting_customer_leaves_without_penalty(self):
        cust = [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}]
        rows, code, err, _ = run("quan", {"stock": {"bong_sung": 2}, "customers": cust, "time_left_ticks": 1}, ticks=5)
        self.assertEqual(code, 0, err)
        self.assertEqual(names(rows), ["customer_left", "quan_end"])
        self.assertEqual(events(rows, "customer_left")[0]["data"]["reason"], "closing")
        self.assertEqual(rows[-1]["reputation"], Q["reputation_initial"])

    def test_full_shift_deterministic(self):
        a, *_ = run("quan", {"stock": {"ca_loc": 3, "bong_sung": 4}}, ticks=10800, seed=9, every=600)
        b, *_ = run("quan", {"stock": {"ca_loc": 3, "bong_sung": 4}}, ticks=10800, seed=9, every=600)
        self.assertEqual(a, b)
        self.assertEqual(a[-1]["reason"], "time")


class QuanFixtures(unittest.TestCase):
    PAY = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
    ASSIGNED = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned", "reserved": {}}

    def test_valid_fixtures(self):
        ok = [
            {"customers": [self.ASSIGNED], "hand": self.PAY},
            {"customers": [self.ASSIGNED], "stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 5, "dish": self.PAY}]},
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "eating",
                            "order_status": "served", "eat_ticks_left": 10, "base_price": 40, "tip": 0}]},
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_status": "unfulfillable",
                            "reserved": {}}]},
            {"stock": {"bong_sung": 2}, "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
                                                       "reserved": {"bong_sung": 2}, "order_tick": 5}]},
        ]
        for block in ok:
            _, code, err, _ = run("quan", block, ticks=0)
            self.assertEqual(code, 0, (block, err))

    def test_rule_conflicts_exit_2(self):
        bad = [
            {"stock": {}, "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}]},  # quá tồn
            {"stock": {"bong_sung": 5}, "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
                                                       "reserved": {"bong_sung": 1}}]},  # khác công thức
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "pho"}]},
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "eating",
                            "order_status": "served", "eat_ticks_left": 10}]},  # thiếu base_price/tip
            {"customers": [self.ASSIGNED]},  # assigned không có món
            {"customers": [self.ASSIGNED], "hand": self.PAY,
             "stoves": [{"id": "B1", "state": "ready", "dish": self.PAY}]},  # bếp và tay cùng đơn
            {"hand": self.PAY},  # liên kết thiếu
            {"customers": [self.ASSIGNED], "hand": dict(self.PAY, dish_id="goi_bong_sung")},  # món không khớp đơn
            {"customers": [self.ASSIGNED], "stoves": [{"id": "B1", "state": "cooking", "dish": self.PAY}]},  # timer 0
            {"hand": "ca_loc_nuong_trui"},
            {"reputation": 9},
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "mood": 1}]},
            {"stoves": [{"id": "B2"}]},
        ]
        for block in bad:
            _, code, _, _ = run("quan", block, ticks=0)
            self.assertEqual(code, 2, block)


class PrdSmokeG(unittest.TestCase):
    def test_two_process_smoke(self):
        with Workdir() as w:
            dock = write_json(w.path("dock.json"), {"gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"]}})
            di = write_json(w.path("dock-inputs.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "42", "--scenario", dock, "--inputs", di, "--ticks", "1",
                                     "--out", w.path("gather.jsonl"), "--inventory-out", w.path("catch.json"))
            self.assertEqual(code, 0, err)
            code, err = run_headless("--mode", "quan", "--seed", "42", "--inventory", w.path("catch.json"), "--ticks", "0",
                                     "--out", w.path("quan.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("quan.jsonl")))[0]["stock"], {"bong_sung": 2, "ca_loc": 1})


if __name__ == "__main__":
    unittest.main()
