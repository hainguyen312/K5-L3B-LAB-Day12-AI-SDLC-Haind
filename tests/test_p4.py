"""Test Phase 4 (Ticket-04 / Test Contract v1.3): manifest, soak, công thức benchmark, endpoint đo/chụp.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_p4 -v
Benchmark có render thật (Chrome headless) chỉ chạy khi có trình duyệt và CHONOI_BENCH_TEST=1.
"""

import json
import math
import os
import subprocess
import sys
import unittest
import urllib.error
import urllib.request

from chonoi.bench import find_browser, summarize
from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer
from chonoi.soak import run_soak

from helpers import Workdir

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _post(url, obj):
    req = urllib.request.Request(url, data=json.dumps(obj).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        e.close()
        return e.code


class Manifest(unittest.TestCase):
    def test_v13_commands(self):
        with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
            c = json.load(f)
        self.assertEqual(c["contract_version"], "1.3")
        self.assertEqual(c["bench_cmd"], "python3 -m chonoi.bench")
        self.assertEqual(c["soak_cmd"], "python3 -m chonoi.soak")
        self.assertIn("freshness", c["tuning"], "gameplay giữ nguyên v1.2")


class Soak(unittest.TestCase):
    def test_two_days_complete_deterministic_and_fields(self):
        tuning = load_contract()["tuning"]
        a, b = run_soak(7, 2, tuning), run_soak(7, 2, tuning)
        self.assertEqual((a["days"], a["days_completed"], a["crashes"]), (2, 2, 0))
        self.assertEqual([r["day"] for r in a["results"]], [1, 2])
        self.assertEqual(set(a["results"][0]), {"day", "earned", "reputation", "score"})
        for r in a["results"]:
            self.assertEqual(r["score"], r["earned"] + 100 * math.floor(r["reputation"]))
        a.pop("duration_s"), b.pop("duration_s")
        self.assertEqual(a, b, "bỏ thời gian thực thì soak lặp lại giống hệt")

    def test_plan_repeats_after_day5(self):
        from chonoi.ids import IdAllocator
        from chonoi.rng import Streams
        from chonoi.sim.day import DaySim
        tuning = load_contract()["tuning"]
        sim = DaySim(tuning, {}, Streams(1), IdAllocator(), days=10)
        sim.day = 6
        self.assertEqual(sim.plan_today()["dishes"], tuning["day_plan"][0]["dishes"])

    def test_cli_writes_json_and_bad_args_exit_2(self):
        with Workdir() as w:
            out = w.path("soak.json")
            p = subprocess.run([sys.executable, "-m", "chonoi.soak", "--seed", "7", "--days", "1", "--out", out],
                               cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            with open(out, encoding="utf-8") as f:
                d = json.load(f)
            self.assertEqual(set(d), {"days", "days_completed", "crashes", "results", "duration_s"})
            for bad in (["--days", "0"], ["--days", "x"], []):
                p = subprocess.run([sys.executable, "-m", "chonoi.soak", "--seed", "7", *bad, "--out", out],
                                   cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(p.returncode, 2, bad)


class BenchFormula(unittest.TestCase):
    def test_summary_fields_and_p1_low(self):
        deltas = [1000 / 60] * 99 + [50.0]
        r = summarize(deltas, 1234.4)
        self.assertEqual(set(r), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
        self.assertEqual((r["frames"], r["load_ms"]), (100, 1234))
        self.assertAlmostEqual(r["measured_s"], (99 * 1000 / 60 + 50) / 1000, places=3)
        self.assertAlmostEqual(r["avg_fps"], 100 / r["measured_s"], places=1)
        self.assertAlmostEqual(r["p1_low_fps"], 20.0, places=2, msg="max(1, ceil(1)) = 1 khung chậm nhất 50 ms")
        r = summarize([10.0] * 247 + [40.0, 30.0, 20.0], 0)  # 250 khung -> 3 khung chậm nhất
        self.assertAlmostEqual(r["p1_low_fps"], 1 / ((40 + 30 + 20) / 3 / 1000), places=2)
        with self.assertRaises(ValueError):
            summarize([], 0)

    def test_bench_and_shot_endpoints_validate(self):
        server = LiveServer(LiveGame("gather", load_contract()["tuning"], {}, 42), port=0)
        server.start()
        base = f"http://127.0.0.1:{server.port}"
        try:
            self.assertEqual(_post(base + "/bench", {"deltas_ms": [16.7] * 3000, "load_ms": 500}), 200)
            self.assertEqual(len(server.game.bench_result["deltas_ms"]), 3000)
            self.assertEqual(_post(base + "/bench", {"deltas_ms": [-1], "load_ms": 1}), 400)
            self.assertEqual(_post(base + "/shot", {"png": "data:image/png;base64,AAAA"}), 200)
            self.assertEqual(_post(base + "/shot", {"png": "nope"}), 400)
        finally:
            server.stop()

    @unittest.skipUnless(os.environ.get("CHONOI_BENCH_TEST") == "1" and find_browser(), "cần Chrome + CHONOI_BENCH_TEST=1")
    def test_render_bench_end_to_end(self):
        with Workdir() as w:
            out = w.path("bench.json")
            p = subprocess.run([sys.executable, "-m", "chonoi.bench", "--seed", "42", "--duration", "2", "--warmup", "0.5",
                                "--out", out], cwd=ROOT, capture_output=True, text=True, timeout=120)
            self.assertEqual(p.returncode, 0, p.stderr)
            with open(out, encoding="utf-8") as f:
                d = json.load(f)
            self.assertEqual(set(d), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
            self.assertGreater(d["frames"], 0)


if __name__ == "__main__":
    unittest.main()
