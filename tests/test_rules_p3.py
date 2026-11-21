"""Test luật Phase 3 của nhóm Haind theo Ticket-03 "Mùa Nước Nổi" / Test Contract v1.2 (độ tươi, kho cá thể).

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_rules_p3 -v
"""

import json
import math
import unittest

from helpers import Workdir, events, frames, items, read_jsonl, run_headless, snapshots, stock, write_json


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


T = tuning()
Q, MENU, FR = T["quan"], T["menu"], T["freshness"]
STOVE, TABLE = Q["stoves"][0]["pos"], Q["tables"][0]["pos"]
G_TICK = FR["gather_decay_per_s"] / 60   # 1/120
Q_TICK = FR["quan_decay_per_s"] / 60     # 1/240
QUIET = {"random_fish": False, "monsters": []}


def run(mode, scenario=None, inputs=None, ticks=1, seed=1, every=1, extra=()):
    with Workdir() as w:
        args = ["--mode", mode, "--seed", str(seed), "--ticks", str(ticks), "--snapshot-every", str(every),
                "--out", w.path("o.jsonl"), *extra]
        if scenario is not None:
            args += ["--scenario", write_json(w.path("sc.json"), scenario)]
        if inputs is not None:
            args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
        code, err = run_headless(*args)
        return (read_jsonl(w.path("o.jsonl")) if code == 0 else []), code, err


def last(rows):
    return snapshots(rows)[-1]


def names(rows, name=None):
    return [e["name"] for e in events(rows)] if name is None else events(rows, name)


class Contract12(unittest.TestCase):
    def test_version_and_freshness_block(self):
        with open("game.contract.json", encoding="utf-8") as f:
            c = json.load(f)
        self.assertEqual(c["contract_version"], "1.2")
        self.assertEqual(FR, {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30})


class GatherFreshness(unittest.TestCase):
    def test_prd_threshold_example_spoils_on_first_step(self):
        sc = {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}], "random_fish": False, "monsters": []}}
        rows, code, err = run("gather", sc, ticks=1)
        self.assertEqual(code, 0, err)
        self.assertEqual(events(rows), [{"type": "event", "tick": 1, "phase": "gather", "name": "spoiled",
                                         "data": {"item_id": "I1", "kind": "ca_linh", "location": "hold"}}])

    def test_decay_half_per_second_clamped_and_spoiled_once_by_id(self):
        hold = [{"id": "I10", "kind": "ca_loc", "fresh": 30}, {"id": "I2", "kind": "ca_linh", "fresh": 30},
                {"id": "I3", "kind": "bong_sung", "fresh": 0.004}, {"id": "I4", "kind": "keo_neo", "fresh": 100}]
        rows, code, err = run("gather", {"gather": dict(QUIET, hold=hold)}, ticks=120)
        self.assertEqual(code, 0, err)
        sp = names(rows, "spoiled")
        self.assertEqual([e["data"]["item_id"] for e in sp], ["I2", "I10"], "cùng tick phát theo id, đúng một lần")
        h = {i["id"]: i["fresh"] for i in last(rows)["hold"]}
        self.assertAlmostEqual(h["I4"], 99.0, places=6)
        self.assertEqual(h["I3"], 0, "kẹp đáy 0")
        self.assertEqual([i["id"] for i in last(rows)["hold"]], ["I10", "I2", "I3", "I4"], "giữ thứ tự vào giỏ")

    def test_new_items_fresh_100_ids_continue_after_fixture(self):
        sc = {"gather": dict(QUIET, player={"pos": [12, 0]}, hold=[{"id": "I7", "kind": "ca_loc", "fresh": 80}])}
        rows, code, err = run("gather", sc, [{"tick": 0, "interact": True}], ticks=2)
        self.assertEqual(code, 0, err)
        h1 = snapshots(rows)[1]["hold"]
        self.assertEqual((h1[1]["id"], h1[1]["kind"], h1[1]["fresh"]), ("I8", "bong_dien_dien", 100))
        self.assertAlmostEqual(last(rows)["hold"][1]["fresh"], 100 - G_TICK, places=9, msg="hao từ bước sau")
        fish = [{"id": "F1", "kind": "ca_linh", "pos": [20, 5]}]
        rows, *_ = run("gather", {"gather": dict(QUIET, player={"pos": [20, 5]}, fish=fish)}, [{"tick": 0, "catch": True}])
        self.assertEqual([i["id"] for i in last(rows)["hold"]], ["I1", "I2", "I3"], "một đàn cá linh = 3 cá thể")

    def test_spoiled_still_occupies_slot(self):
        sc = {"gather": dict(QUIET, player={"pos": [12, 0]}, hold=items(*["ca_loc"] * 12, fresh=5))}
        rows, *_ = run("gather", sc, [{"tick": 0, "interact": True}])
        self.assertEqual(names(rows, "hold_full")[0]["data"]["free"], 0)

    def test_pause_stops_decay(self):
        sc = {"gather": dict(QUIET, hold=items("ca_loc"))}
        rows, *_ = run("gather", sc, [{"tick": 0, "pause": True}], ticks=50)
        self.assertEqual(last(rows)["hold"][0]["fresh"], 100)


class FileHandover(unittest.TestCase):
    def _dock(self, hold, w):
        sc = write_json(w.path("sc.json"), {"gather": dict(QUIET, hold=hold)})
        inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
        code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5", "--scenario", sc, "--inputs", inp,
                                 "--inventory-out", w.path("kho.json"), "--out", w.path("g.jsonl"))
        self.assertEqual(code, 0, err)
        with open(w.path("kho.json"), encoding="utf-8") as f:
            return json.load(f), read_jsonl(w.path("g.jsonl"))

    def test_prd_handover_smoke_exact_match(self):
        with Workdir() as w:
            kho, g = self._dock([{"id": "I1", "kind": "ca_linh", "fresh": 100}], w)
            self.assertEqual([(i["id"], i["kind"]) for i in kho["items"]], [("I1", "ca_linh")])
            self.assertAlmostEqual(kho["items"][0]["fresh"], 100 - G_TICK, places=9)
            self.assertEqual(events(g, "gather_end")[0]["data"]["inventory"], kho)
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", w.path("kho.json"),
                                     "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"], kho["items"], "so chính xác id/kind/fresh")

    def test_file_sorted_by_id_and_threshold_survives_round_trip(self):
        with Workdir() as w:
            hold = [{"id": "I2", "kind": "ca_loc", "fresh": 30 + 1 / 120}, {"id": "I1", "kind": "bong_sung", "fresh": 31}]
            kho, g = self._dock(hold, w)
            self.assertEqual([i["id"] for i in kho["items"]], ["I1", "I2"])
            self.assertEqual(kho["items"][1]["fresh"], 30, "30 + 1/120 − 1/120 = đúng 30, chưa ươn")
            self.assertEqual(events(g, "spoiled"), [])
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "1", "--inventory", w.path("kho.json"),
                                     "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            sp = events(read_jsonl(w.path("q.jsonl")), "spoiled")
            self.assertEqual([(e["tick"], e["data"]) for e in sp], [(1, {"item_id": "I2", "kind": "ca_loc", "location": "stock"})])

    def test_faint_writes_empty_item_list(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": dict(QUIET, hold=items("ca_loc"), player={
                "pos": [50, 10], "oxygen_ticks": 0, "hp": 1, "zero_oxy_ticks": 59})})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "3", "--scenario", sc,
                                     "--inventory-out", w.path("kho.json"), "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            with open(w.path("kho.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})

    def test_count_inventory_and_bad_items_exit_2(self):
        bad = [{"items": {"ca_loc": 1}}, {"items": [{"id": "I1", "kind": "ca_loc"}]},
               {"items": [{"id": "I1", "kind": "ca_loc", "fresh": -1}]}, {"items": [{"id": 1, "kind": "ca_loc", "fresh": 5}]}]
        for b in bad:
            with Workdir() as w:
                p = write_json(w.path("inv.json"), b)
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", p, "--out", w.path("q.jsonl"))
                self.assertEqual(code, 2, b)
        for sc in ({"quan": {"stock": {"ca_loc": 1}}}, {"gather": {"hold": ["ca_loc"]}},
                   {"gather": {"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 101}]}}):
            mode = next(iter(sc))
            self.assertEqual(run(mode, sc, ticks=0)[1], 2, sc)


class QuanFreshness(unittest.TestCase):
    def test_stock_decays_quarter_per_second_including_reserved(self):
        cust = [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}]
        sc = {"quan": {"stock": stock(bong_sung=2), "customers": cust, "random_customers": False}}
        rows, code, err = run("quan", sc, ticks=240)
        self.assertEqual(code, 0, err)
        s = last(rows)
        self.assertEqual([i["fresh"] for i in s["stock"]], [99, 99])
        self.assertEqual(s["customers"][0]["reserved"], ["I1", "I2"])

    def test_reserve_freshest_tie_by_id_and_skip_spoiled(self):
        stk = [{"id": "I1", "kind": "bong_sung", "fresh": 50}, {"id": "I2", "kind": "bong_sung", "fresh": 90},
               {"id": "I3", "kind": "bong_sung", "fresh": 70}, {"id": "I4", "kind": "bong_sung", "fresh": 90},
               {"id": "I5", "kind": "bong_sung", "fresh": 29}]
        rows, code, err = run("quan", {"quan": {"stock": stk}}, ticks=Q["first_customer_tick"], every=1000)
        self.assertEqual(code, 0, err)
        c = last(rows)["customers"][0]
        self.assertEqual((c["dish_id"], c["reserved"]), ("goi_bong_sung", ["I2", "I4"]))

    def test_spoiled_not_cookable_no_dish(self):
        rows, *_ = run("quan", {"quan": {"stock": stock(ca_loc=3, fresh=29)}}, ticks=Q["first_customer_tick"], every=1000)
        self.assertEqual(names(rows), ["no_dish"])

    def test_rereserve_once_when_reserved_item_spoils(self):
        stk = [{"id": "I1", "kind": "bong_sung", "fresh": 30}, {"id": "I2", "kind": "bong_sung", "fresh": 60},
               {"id": "I3", "kind": "bong_sung", "fresh": 80}]
        cust = [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "reserved": ["I1", "I2"]}]
        rows, code, err = run("quan", {"quan": {"stock": stk, "customers": cust, "random_customers": False}}, ticks=1)
        self.assertEqual(code, 0, err)
        self.assertEqual([(e["tick"], e["data"]["item_id"]) for e in names(rows, "spoiled")], [(1, "I1")])
        c = last(rows)["customers"][0]
        self.assertEqual((c["order_status"], c["reserved"]), ("reserved", ["I2", "I3"]))

    def test_rereserve_fails_unfulfillable_by_order_tick_then_table(self):
        stk = [{"id": "I1", "kind": "ca_loc", "fresh": 30}, {"id": "I2", "kind": "ca_loc", "fresh": 30},
               {"id": "I3", "kind": "ca_loc", "fresh": 90}]
        cust = [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"], "order_tick": 5},
                {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "reserved": ["I2"], "order_tick": 3}]
        rows, code, err = run("quan", {"quan": {"stock": stk, "customers": cust, "random_customers": False}}, ticks=2)
        self.assertEqual(code, 0, err)
        self.assertEqual([e["data"]["item_id"] for e in names(rows, "spoiled")], ["I1", "I2"])
        c1, c2 = last(rows)["customers"]
        self.assertEqual((c2["order_status"], c2["reserved"]), ("reserved", ["I3"]), "order_tick nhỏ hơn được giữ lại trước")
        self.assertEqual((c1["order_status"], c1["reserved"], c1["state"]), ("unfulfillable", [], "waiting"))

    def test_price_by_freshness_exact_floor_and_tip(self):
        stk = [{"id": "I1", "kind": "ca_loc", "fresh": 50 + 1 / 240}]  # sau 1 lần hao đúng 50
        cust = [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]
        sc = {"quan": {"stock": stk, "customers": cust, "random_customers": False, "player": {"pos": STOVE}}}
        rows, code, err = run("quan", sc, [{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual(code, 0, err)
        cs = names(rows, "cook_started")[0]["data"]
        self.assertEqual(cs["base_price"], 30, "floor(60 × 50 / 100) = 30 chính xác, không 29")
        self.assertEqual(cs["items"], [{"id": "I1", "kind": "ca_loc", "fresh": 50}])
        self.assertEqual(last(rows)["stoves"][0]["dish"]["base_price"], 30)
        self.assertEqual(last(rows)["stock"], [], "tiêu đúng id đang giữ")

    def test_cook_items_sorted_kind_then_id_mean_price(self):
        stk = [{"id": "I9", "kind": "ca_loc", "fresh": 80}, {"id": "I3", "kind": "bong_dien_dien", "fresh": 60},
               {"id": "I12", "kind": "bong_dien_dien", "fresh": 60}]
        cust = [{"id": "C1", "table_id": "T1", "dish_id": "canh_chua_ca_loc"}]
        sc = {"quan": {"stock": stk, "customers": cust, "random_customers": False, "player": {"pos": STOVE}}}
        rows, *_ = run("quan", sc, [{"tick": 0, "interact": True}])
        cs = names(rows, "cook_started")[0]["data"]
        self.assertEqual([i["id"] for i in cs["items"]], ["I3", "I9"])
        self.assertEqual(cs["base_price"], math.floor(90 * (70 - Q_TICK) / 100))
        self.assertEqual([i["id"] for i in last(rows)["stock"]], ["I12"])

    def test_tip_on_fresh_price(self):
        cust = [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned", "reserved": []}]
        hand = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 33}
        rows, *_ = run("quan", {"quan": {"customers": cust, "hand": hand, "random_customers": False,
                                         "player": {"pos": TABLE}}}, [{"tick": 0, "interact": True}])
        self.assertEqual(names(rows, "served")[0]["data"]["tip"], 6, "floor(33 × 0.2) trên giá đã chốt")


class DayFreshness(unittest.TestCase):
    def test_day_handover_no_extra_decay_and_shop_no_decay(self):
        sc = {"gather": dict(QUIET, hold=items("ca_keo", "ca_keo"))}
        q_open = 1
        shop_open = q_open + int(Q["duration_s"] * 60)
        rows, code, err = run("day", sc, [{"tick": 0, "interact": True}], ticks=shop_open + 30, every=1)
        self.assertEqual(code, 0, err)
        s = {r["tick"]: r for r in snapshots(rows)}
        self.assertEqual(s[q_open]["phase"], "quan")
        self.assertAlmostEqual(s[q_open]["stock"][0]["fresh"], 100 - G_TICK, places=9, msg="bàn giao cùng tick, không hao thêm")
        self.assertAlmostEqual(s[q_open + 1]["stock"][0]["fresh"], 100 - G_TICK - Q_TICK, places=9)
        self.assertEqual(s[shop_open]["phase"], "shop")
        self.assertEqual(s[shop_open]["stock"], s[shop_open + 30]["stock"], "Shop không hao tươi")
        self.assertEqual([i["id"] for i in s[shop_open]["stock"]], ["I1", "I2"])

    def test_ids_continue_across_days(self):
        fish = [{"id": "F1", "kind": "ca_loc", "pos": [5, 10]}]
        sc = {"gather": dict(QUIET, fish=fish, player={"pos": [5, 10]})}
        end1 = int(T["gather"]["duration_s"] * 60) + int(Q["duration_s"] * 60) + T["shop"]["max_ticks"]
        # bắt xong thì nổi lên để không ngạt; Ngày 2 bắt lại đàn fixture ở bước đầu
        inp = [{"tick": 0, "catch": True}, {"tick": 1, "catch": False, "move": [0, -1]}, {"tick": end1, "catch": True}]
        rows, code, err = run("day", sc, inp, ticks=end1 + 1, every=100000, extra=("--days", "2"))
        self.assertEqual(code, 0, err)
        self.assertEqual([i["id"] for i in last(rows)["hold"]], ["I2"], "Ngày 2 tiếp tục I2 sau I1 của Ngày 1")


if __name__ == "__main__":
    unittest.main()
