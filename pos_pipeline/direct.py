"""L4: turn a `Diagnosis` (L2 shadow prices) into direction for the improvement loop (docs/loop.md 6.1).

Pure functions over a `Diagnosis`; no engine. Two uses:
  * `stage_bounds`: per stage, a signal of what the stage can still gain, so the loop can skip a stage that has nothing to
    buy. Only gear has enumerable levers (probes with a gear-affix cost); supports and the tree get `None` (unknown: they
    always run). Heuristic, not a proof: one probe is one affix step, a search can combine several.
  * `tree_goals`: weights for the tree optimiser's weighted goals (relative gain per output), from the measured relief per
    relative change of DPS vs EHP on the binding constraint, so the tree pulls toward whichever output relieves it.
"""
from __future__ import annotations

from statistics import median

from .diagnose import Diagnosis

MIN_SIGNAL = 1e-6      # a probe moving an output less than this (relative) says nothing about it
GOAL_CLAMP = (0.1, 10.0)


def _relief(d: Diagnosis, p) -> float | None:
    key = d.binding if d.binding != "objective" else "dps"
    return p.gains.get(key)


def stage_bounds(d: Diagnosis) -> dict[str, float | None]:
    gear = [r for p in d.probes if p.status == "ok" and p.cost_points is not None and (r := _relief(d, p)) is not None]
    # no gear-buyable lever measured at all (all inert/excluded) is "unknown", not zero: never skip on missing data
    return {"gear": max(0.0, max(gear)) if gear else None, "tree": None, "supports": None}


def tree_goals(d: Diagnosis, metric: str) -> dict[str, float] | None:
    """{metric: 1, TotalEHP: w}; w = (relief per relative EHP) / (relief per relative DPS), clamped. None when either is not
    measurable on this build (then the tree keeps optimising the plain metric)."""
    if d.binding == "objective":
        return None
    per_dps, per_ehp = [], []
    for p in d.probes:
        if p.status != "ok":
            continue
        r, dps, ehp = _relief(d, p), p.gains.get("dps"), p.gains.get("ehp")
        if r is None or dps is None or ehp is None:
            continue
        if dps > MIN_SIGNAL and abs(ehp) < MIN_SIGNAL:
            per_dps.append(r / dps)
        elif ehp > MIN_SIGNAL and abs(dps) < MIN_SIGNAL:
            per_ehp.append(r / ehp)
    if not per_dps or not per_ehp:
        return None
    rd, re = median(per_dps), median(per_ehp)
    if rd <= 0 and re <= 0:
        return None
    if rd <= 0:
        w = GOAL_CLAMP[1]
    else:
        w = min(max(re / rd, GOAL_CLAMP[0]), GOAL_CLAMP[1])
    return {metric: 1.0, "TotalEHP": round(w, 3)}


def advice(d: Diagnosis, metric: str) -> dict:
    """What the loop records and acts on: bounds per stage, tree goals, the binding constraint, the top levers."""
    return {"bounds": stage_bounds(d), "tree_goals": tree_goals(d, metric), "binding": d.binding,
            "top": [{"id": p.id, "price": p.price} for p in d.top(3)], "diagnose_s": d.seconds}
