"""One objective for every search stage (L1, docs/loop.md 2.1): score a candidate build by the run's benchmarks.

Lexicographic key `(-deficit, goal)`:
  * deficit = sum of fractional shortfalls of every constraint (`1 - have/need`; clamped to [0, 1] except stat floors,
    which keep their gradient below zero, so units never mix): stat floors, survive every named hit of a boss benchmark (max hit taken / hit >= 1), and, only when
    `hard_ttk` is set, the boss time-to-kill gate. Zero = every constraint met.
  * goal = sum over benchmarks of ln(rate): -ln(boss TTK), -ln(pack clear s). A boss rate falls back to ln(metric) when
    the TTK cannot be computed (life/uptime unsourced), a pack rate likewise; availability depends on the benchmark, not
    on the candidate, so candidates stay comparable. Log keeps a difference a relative gain.
Unsourced named hits impose no survival constraint (never a guess). Scoring runs one engine evaluation per benchmark
under that benchmark's PoB options (`fights`), the same options `benchmarks.evaluate` uses, so the stage score and the
ranking agree. Ranking stays benchmark-only (report.py); this only changes what the searches pull toward.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from . import benchmarks as B
from . import data

FLOOR_NEED_MIN = 1e-9
LN_FLOOR = math.log(1e-9)     # goal term of a candidate with no damage / no clear


@dataclass(frozen=True)
class Fight:
    bid: str
    kind: str                       # boss | pack
    options: tuple[tuple[str, Any], ...]   # PoB config options, sorted

    def opts(self) -> dict[str, Any]:
        return dict(self.options)


@dataclass(frozen=True)
class Score:
    deficit: float                  # sum of fractional shortfalls; 0 = all constraints met
    goal: float                     # sum of ln(rate)
    parts: tuple[tuple[str, float], ...] = ()   # (constraint, shortfall) for the non-zero ones

    @property
    def key(self) -> tuple[float, float]:
        return (-self.deficit, self.goal)


def _shortfall(have: float, need: float, clamp: bool = True) -> float:
    """Fraction by which `have` misses `need`. Stat floors pass clamp=False: resists start deeply negative (-60%), and a
    clamped shortfall gives the search no gradient until the stat is positive."""
    if need <= FLOOR_NEED_MIN or have >= need:
        return 0.0
    f = 1.0 - have / need
    return min(1.0, f) if clamp else f


class Objective:
    def __init__(self, metric: str, bench_ids: Sequence[str], *, floors: Mapping[str, float | str] | None = None,
                 hard_ttk: bool = False, projectile: bool = False, conditions: Sequence[str] = ()):
        bms = B.benchmarks()
        unknown = [b for b in bench_ids if b not in bms]
        if unknown:
            raise ValueError(f"unknown benchmark(s) {unknown}; known: {', '.join(bms)}")
        self.metric, self.hard_ttk, self.projectile = metric, hard_ttk, projectile
        self.floors = dict(floors or {})
        self.fights = tuple(
            Fight(b, bms[b]["kind"], tuple(sorted({**data.conditions_not_in_fight(conditions, bms[b]["kind"])[0],
                                                   **B.pob_options(bms[b])}.items())))
            for b in bench_ids)
        floor_keys = [*self.floors, *(v for v in self.floors.values() if isinstance(v, str))]
        self.keys = tuple(dict.fromkeys([*B.BENCH_KEYS, metric, *floor_keys]))
        self.notes: list[str] = []

    def __bool__(self) -> bool:
        return bool(self.fights)

    def mutations(self, fight: Fight) -> tuple:
        return (("set_config", {"options": fight.opts()}),)

    # ---- pure scoring --------------------------------------------------------------------------------------
    def floors_deficit(self, stats: Mapping[str, Any]) -> float:
        d = 0.0
        for k, v in self.floors.items():
            need = float(stats.get(v) or 0.0) if isinstance(v, str) else float(v)
            d += _shortfall(float(stats.get(k) or 0.0), need, clamp=False)
        return d

    def score(self, stats_by_fight: Sequence[Mapping[str, Any]]) -> Score:
        """`stats_by_fight[i]` = PoB stats of the candidate under `fights[i]`'s options."""
        deficit, goal, parts = 0.0, 0.0, []

        def add(name: str, v: float) -> None:
            nonlocal deficit
            if v > 0:
                deficit += v
                parts.append((name, round(v, 6)))

        if stats_by_fight:
            add("floors", self.floors_deficit(stats_by_fight[0]))
        for f, st in zip(self.fights, stats_by_fight):
            if f.kind == "boss":
                r = B.boss_metrics(f.bid, st, self.metric)
                margins = [m for m in r.hit_margins.values() if m is not None]
                if r.survive_basis == "named" and margins and _gate(f.bid, "survive_all_hits"):
                    add(f"survive:{f.bid}", sum(_shortfall(m, 1.0) for m in margins) / len(margins))
                gmax = B._v(B.benchmarks()[f.bid]["gates"].get("ttk_s_max"))
                if self.hard_ttk and gmax and r.ttk_s:
                    add(f"ttk:{f.bid}", _shortfall(gmax, r.ttk_s))
                elif self.hard_ttk and gmax and not r.ttk_s:
                    add(f"ttk:{f.bid}", 1.0)
                goal += -math.log(r.ttk_s) if r.ttk_s else _ln(st.get(self.metric))
            else:
                r = B.pack_metrics(f.bid, st, self.projectile)
                goal += -math.log(r.clear_s) if r.clear_s else _ln(st.get(self.metric))
        return Score(deficit, goal, tuple(parts))


def _gate(bid: str, name: str) -> bool:
    return bool(B._v(B.benchmarks()[bid]["gates"].get(name)))


def _ln(x: Any) -> float:
    try:
        x = float(x or 0.0)
    except (TypeError, ValueError):
        return LN_FLOOR
    return math.log(x) if x > 1e-9 else LN_FLOOR


def from_names(metric: str, bench_ids: Sequence[str], **kw: Any) -> Objective | None:
    """None when the run names no benchmark (the searches then keep the plain metric)."""
    return Objective(metric, bench_ids, **kw) if bench_ids else None
