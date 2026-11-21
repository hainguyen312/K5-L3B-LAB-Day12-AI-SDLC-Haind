"""Chụp màn hình cửa sổ chơi bằng Chrome headless (bằng chứng HUD/cảnh báo, Ticket-04), nhóm Haind.

    python3 tools/screenshot.py --mode gather --scenario sc.json --out a.png [--query contrast=1] [--delay 1500]

Dựng server chơi thử trong tiến trình (cùng sim), mở Chrome headless 1280×720 ở `/?shot=1`; trang tự chụp canvas
(`toDataURL`) sau `delay` ms và POST về `/shot`; script lưu PNG. Không cần thư viện ngoài.
"""

import argparse
import base64
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chonoi.bench import find_browser  # noqa: E402
from chonoi.contract import load_contract  # noqa: E402
from chonoi.live import LiveGame, LiveServer  # noqa: E402
from chonoi.scenario import load_scenario  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", default="gather", choices=["gather", "quan", "day"])
    p.add_argument("--scenario")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--out", required=True)
    p.add_argument("--query", default="")
    p.add_argument("--delay", type=int, default=1500)
    p.add_argument("--screen", help="day: màn hình mở sẵn (menu/day_intro/…); 'play' = vào chơi luôn")
    a = p.parse_args()
    tuning = load_contract()["tuning"]
    game = LiveGame(a.mode, tuning, load_scenario(a.scenario, a.mode, tuning), a.seed, days=5)
    if a.screen:
        game._screen(None if a.screen == "play" else a.screen)
    server = LiveServer(game, port=0)
    server.start()
    profile = tempfile.mkdtemp(prefix="chonoi-shot-")
    q = f"?shot=1&delay={a.delay}" + (f"&{a.query}" if a.query else "")
    proc = subprocess.Popen([find_browser(), "--headless=new", f"--user-data-dir={profile}", "--window-size=1280,720",
                             "--no-first-run", "--no-proxy-server", "--proxy-bypass-list=*", "--use-mock-keychain",
                             "--password-store=basic", "--disable-background-networking", "--disable-extensions",
                             server.url + q], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.time() + 60
        while game.shot_png is None and time.time() < deadline:
            time.sleep(0.1)
        if game.shot_png is None:
            sys.stderr.write("không nhận được ảnh\n")
            return 1
        with open(a.out, "wb") as f:
            f.write(base64.b64decode(game.shot_png.split(",", 1)[1]))
        print(a.out)
        return 0
    finally:
        proc.terminate()
        proc.wait(timeout=5)
        server.stop()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
