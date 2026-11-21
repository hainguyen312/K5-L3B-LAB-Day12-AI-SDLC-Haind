"""Vòng tick (Contract B/E, Test Contract v1.1).

Thứ tự ghi: [event tick 0 của day] -> snapshot tick 0 -> với mỗi bước: event (theo thứ tự xử lý) rồi snapshot (nếu tới
lượt hoặc lượt kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

Ba bộ đếm (Ticket-02 mục 4.2, 4.4): `tick` = số bước ngoài (tăng cả khi pause), `sim_tick` = số bước gameplay toàn
lượt, `phase_tick` = số bước gameplay trong pha hiện tại (về 0 khi đổi pha).
Pause: xét cạnh `pause` trước. Vào pause chỉ tăng tick ngoài và phát `paused`; còn pause thì bỏ qua mọi cạnh hành động
và `buy`, timer đứng yên; cạnh kế tiếp phát `resumed` rồi chạy gameplay ngay trong bước đó.

`Session` là API bước tick dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`).
"""

import math

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.day import DaySim
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory, days=1):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    if mode == "day":
        return DaySim(tuning, scenario, streams, ids, days=days)
    return QuanSim(tuning, scenario, streams, ids, inventory=inventory)


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days)
        self.tick = 0
        self.sim_tick = 0
        self.paused = False

    @property
    def done(self) -> bool:
        return self.sim.done

    def _score(self):
        return self.sim.earned + self.tuning["score"]["reputation_multiplier"] * math.floor(self.sim.reputation)

    def _event(self, name, data, phase=None, day=None, tick=None):
        row = {"type": "event", "tick": self.tick if tick is None else tick, "phase": phase or self.sim.phase}
        if self.mode == "day":
            row["day"] = day if day is not None else self.sim.day
        row.update(name=name, data=data)
        return row

    def initial_rows(self) -> list:
        """Event ở tick 0 (chế độ day: day_start, day_plan, phase_start) — ghi trước snapshot tick 0."""
        return [self._event(n, d, ph, dy) for n, d, ph, dy in getattr(self.sim, "initial_events", [])]

    def snapshot(self) -> dict:
        sim = self.sim
        state = "finished" if sim.done else ("paused" if self.paused else "playing")
        s = {"type": "snapshot", "tick": self.tick, "sim_tick": self.sim_tick, "mode": self.mode,
             "phase": sim.phase, "phase_tick": sim.phase_tick, "state": state, "time_left_ticks": sim.time_left_ticks,
             "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": self._score()}
        s.update(sim.snapshot())
        return s

    def step(self, inp) -> list:
        """Chạy một bước ngoài với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        rows = []
        if inp.pressed("pause"):
            self.paused = not self.paused
            if self.paused:
                self.tick += 1
                return [self._event("paused", {})]
            rows.append(self._event("resumed", {}, tick=self.tick + 1))  # gameplay chạy ngay trong bước này
        elif self.paused:
            self.tick += 1
            return rows
        evs = self.sim.step(inp)
        self.tick += 1
        self.sim_tick += 1
        for ev in evs:
            rows.append(self._event(*ev) if len(ev) > 2 else self._event(ev[0], ev[1]))
        return rows

    def end_row(self) -> dict:
        sim = self.sim
        row = {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": self.mode,
               "state": "finished" if sim.done else ("paused" if self.paused else "playing"),
               "reason": sim.reason if sim.done else "tick_limit",
               "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": self._score()}
        if self.mode == "day":
            row["days_completed"] = sim.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None,
        days=1):
    sess = Session(mode, tuning, scenario, seed, inventory, days)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        for row in sess.initial_rows():
            w.write(row)
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            for row in sess.step(inp):
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
