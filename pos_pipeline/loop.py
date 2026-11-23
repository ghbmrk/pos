"""Inner improvement loop v1 (L3, docs/loop.md 2.3): round-robin coordinate descent on the benchmark objective.

Pure control flow with injected moves, so it is testable without an engine. A *move* re-searches one stage (supports,
tree, gear) from the current build and returns a new build XML. After every move the build is scored by `key_of`
(the L1 objective key `(-deficit, goal)`, lexicographic); a move is **kept only if it strictly improves the key**, so the
objective never regresses and a stage that cannot improve the build is a recorded no-op, not a loss.

A round runs every move once. L4 (docs/loop.md 6.1) directs the rounds:
  * a move that found nothing on build X is *dead* on X (searches are deterministic): it is skipped until another move
    changes the build, and a round in which every move is dead stops the loop at once ("fixed point");
  * an optional `advisor(xml)` (a diagnosis in the orchestrator) returns, per stage, an upper bound on the fractional
    gain the stage can still deliver (None = unknown); a stage whose bound is below `skip_below` is skipped;
  * from round 2 on, moves run in order of the gain per second they last delivered (a stage not yet timed goes first).
The loop stops when
  * a full round gains less than `min_gain` (default 1%: `(-deficit)` and `ln(rate)` are both relative, so their summed
    difference is a fractional gain), or
  * `max_rounds` rounds ran, or
  * `budget_s` wall seconds are spent (checked between moves; a running move is never interrupted).
Every move is appended to a JSONL trace (move, key before/after, seconds, accepted) and each round summarised, so the
convergence curve and the reason for stopping are on record.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Sequence

Key = tuple[float, float]
DEFAULT_MIN_GAIN = 0.01
KEY_EPS = 1e-6
DEFAULT_SKIP_BELOW = 0.002   # a stage the advisor bounds under 0.2% of the objective is not worth its seconds


@dataclass
class Move:
    name: str
    fn: Callable[[str], str]                       # build xml -> improved build xml (may raise: recorded, skipped)
    on_accept: Callable[[str], None] | None = None  # called with the new xml when the loop keeps the move's result
    stage: str = ""                                # key into the advisor's bounds; "" = never advised away


@dataclass
class MoveRecord:
    round: int
    move: str
    before: Key
    after: Key | None            # None = the move failed or the result could not be scored
    seconds: float
    accepted: bool
    note: str = ""
    skipped: bool = False        # not run: dead on this build, or advised away (seconds = 0)


@dataclass
class Round:
    n: int
    start: Key
    best: Key
    gain: float
    accepted: list[str]
    seconds: float


@dataclass
class LoopResult:
    xml: str                     # best build found (the input xml if nothing improved)
    start: Key
    best: Key
    rounds: list[Round] = field(default_factory=list)
    moves: list[MoveRecord] = field(default_factory=list)
    stop: str = ""               # converged | fixed_point | max_rounds | budget
    advice: list[dict] = field(default_factory=list)   # one entry per advisor call (round, bounds, notes)
    seconds: float = 0.0

    @property
    def gain(self) -> float:
        return gain(self.start, self.best)

    def summary(self) -> dict:
        """JSON-safe digest for run.json / the report (no xml)."""
        d = asdict(self)
        d.pop("xml")
        d["gain"] = self.gain
        return d


def gain(a: Key, b: Key) -> float:
    """Fractional improvement from key `a` to `b`: deficit shortfall removed plus ln-rate gained (both relative)."""
    return (b[0] - a[0]) + (b[1] - a[1])


def better(b: Key, a: Key, eps: float = KEY_EPS) -> bool:
    """`b` strictly beats `a` lexicographically: a smaller constraint deficit, or an equal one and a larger goal."""
    if b[0] > a[0] + eps:
        return True
    return b[0] >= a[0] - eps and b[1] > a[1] + eps


def improve(xml: str, moves: Sequence[Move], key_of: Callable[[str], Key], *, max_rounds: int = 4,
            min_gain: float = DEFAULT_MIN_GAIN, budget_s: float | None = None, trace: str | Path | None = None,
            clock: Callable[[], float] = time.perf_counter, log: Callable[[str], None] = lambda s: None,
            label: str = "", after_move: Callable[[], None] | None = None,
            advisor: Callable[[str], dict] | None = None, skip_below: float = DEFAULT_SKIP_BELOW,
            dead_skip: bool = True) -> LoopResult:
    t_start = clock()
    cur, cur_key = xml, key_of(xml)
    res = LoopResult(xml, cur_key, cur_key)
    out = open(trace, "a", encoding="utf-8") if trace else None

    def emit(rec: dict) -> None:
        if out:
            out.write(json.dumps({"label": label, **rec}) + "\n")
            out.flush()

    def spent() -> bool:
        return budget_s is not None and clock() - t_start >= budget_s

    try:
        emit({"event": "start", "key": cur_key})
        dead: dict[str, str] = {}          # move name -> build xml it found nothing on
        rate: dict[str, float] = {}        # move name -> last gain per second (ordering from round 2)
        for n in range(1, max_rounds + 1):
            r_start, r_t0, acc = cur_key, clock(), []
            bounds: dict = {}
            if advisor is not None and not spent():
                try:
                    adv = advisor(cur)
                    bounds = adv.get("bounds") or {}
                    res.advice.append({"round": n, **{k: v for k, v in adv.items()}})
                    emit({"event": "advice", "round": n, **adv})
                except Exception as ex:   # no diagnosis = no direction: the round runs undirected
                    res.advice.append({"round": n, "error": f"{type(ex).__name__}: {ex}"})
                    emit({"event": "advice", "round": n, "error": f"{type(ex).__name__}: {ex}"})
            order = list(moves)
            if n > 1:
                order.sort(key=lambda m: -rate.get(m.name, float("inf")))   # sort is stable: untimed first, in given order
            ran = 0
            for mv in order:
                if spent():
                    res.stop = "budget"
                    break
                t0, before = clock(), cur_key
                rec = MoveRecord(n, mv.name, before, None, 0.0, False)
                skip = ""
                if dead_skip and dead.get(mv.name) == cur:
                    skip = "dead: found nothing on this exact build"
                elif mv.stage and bounds.get(mv.stage) is not None and bounds[mv.stage] < skip_below:
                    skip = f"advised away: bound {bounds[mv.stage]:.4f} < {skip_below}"
                if skip:
                    rec.skipped, rec.after, rec.note = True, before, skip
                    res.moves.append(rec)
                    emit({"event": "move", **asdict(rec)})
                    log(f"{label} round {n} {mv.name}: skipped ({skip})")
                    continue
                ran += 1
                try:
                    new = mv.fn(cur)
                    if new == cur:
                        rec.note = "unchanged"
                        rec.after = before
                        dead[mv.name] = cur
                    else:
                        rec.after = key_of(new)
                        if better(rec.after, before):
                            rec.accepted = True
                            cur, cur_key = new, rec.after
                            acc.append(mv.name)
                            if mv.on_accept:
                                mv.on_accept(new)
                        else:
                            rec.note = "no gain; discarded"
                            dead[mv.name] = cur
                except Exception as ex:   # a failed search or scoring leaves the build as it was
                    rec.note = f"{type(ex).__name__}: {ex}"
                rec.seconds = clock() - t0
                rate[mv.name] = (gain(before, rec.after) / max(rec.seconds, 1e-9)) if rec.accepted and rec.after else 0.0
                if after_move:
                    after_move()   # e.g. recycle a leaking engine between moves (every build load leaks memory)
                res.moves.append(rec)
                emit({"event": "move", **asdict(rec)})
                log(f"{label} round {n} {mv.name}: {before[1]:.4f} -> "
                    f"{(rec.after or before)[1]:.4f} {'kept' if rec.accepted else rec.note}")
            g = gain(r_start, cur_key)
            res.rounds.append(Round(n, r_start, cur_key, g, acc, clock() - r_t0))
            emit({"event": "round", **asdict(res.rounds[-1])})
            if res.stop == "budget":
                break
            if ran == 0:
                res.stop = "fixed_point"
                break
            if g < min_gain:
                res.stop = "converged"
                break
        else:
            res.stop = "max_rounds"
        res.xml, res.best, res.seconds = cur, cur_key, clock() - t_start
        emit({"event": "stop", "reason": res.stop, "best": cur_key, "gain": res.gain, "seconds": res.seconds})
    finally:
        if out:
            out.close()
    return res
