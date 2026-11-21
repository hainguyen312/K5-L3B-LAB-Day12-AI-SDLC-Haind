"""Cửa sổ chơi chế độ day (Phase 2): menu chính -> DayIntro -> gameplay, pause, Shop. Chỉ cho starter Python."""

import json
import time
import unittest
import urllib.request

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return json.loads(r.read())


def _post(url, obj=None):
    req = urllib.request.Request(url, data=json.dumps(obj or {}).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status


class LiveDayTest(unittest.TestCase):
    def test_menu_intro_play_pause(self):
        tuning = load_contract()["tuning"]
        server = LiveServer(LiveGame("day", tuning, {}, 1, days=1), port=0)
        server.start()
        base = f"http://127.0.0.1:{server.port}"
        try:
            st = _get(base + "/state")
            self.assertEqual((st["ui"]["screen"], st["phase"], st["day"]), ("menu", "gather", 1))
            time.sleep(0.2)
            self.assertEqual(_get(base + "/state")["tick"], 0, "ở menu chính mô phỏng không bước")
            _post(base + "/continue")
            self.assertEqual(_get(base + "/state")["ui"]["screen"], "day_intro")
            _post(base + "/continue")
            deadline = time.time() + 3
            while time.time() < deadline and _get(base + "/state")["tick"] < 5:
                time.sleep(0.05)
            self.assertGreaterEqual(_get(base + "/state")["tick"], 5)
            _post(base + "/input", {"pause": True})
            time.sleep(0.15)
            st1 = _get(base + "/state")
            self.assertEqual(st1["state"], "paused")
            time.sleep(0.2)
            st2 = _get(base + "/state")
            self.assertEqual(st2["sim_tick"], st1["sim_tick"], "pause dừng timer gameplay")
            self.assertEqual(_post(base + "/input", {"buy": "oxygen"}), 200)
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
