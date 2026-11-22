"""Tree stage (G6, docs/tree.md): passive allocation for a seed build via the engine's `optimize_passives`.

A thin wrapper: the greedy (what-if calc per candidate per pick) runs inside one engine process, so a call
is long and is not routed through `EnginePool` (its per-job watchdog is 60 s). Seeds run in parallel, one
dedicated engine per seed. The result carries the new build XML so later stages (gear) start from it.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from pos_engine.engine import PobEngine

STAT_KEYS = ("TotalDPS", "FullDPS", "TotalEHP", "Life", "EnergyShield", "Mana")


@dataclass
class TreeSearch:
    metric: str
    start: float | None
    final: float | None
    points_used: int
    points_remaining: int
    allocated: list[dict[str, Any]]
    xml: str
    stats: dict[str, Any]
    seconds: float                      # wall time of the optimize_passives call only
    reset: bool
    notes: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    @property
    def gain(self) -> float:
        return ((self.final or 0.0) - self.start) / self.start if self.start else 0.0


def _values(res: dict[str, Any], metric: str, goals: dict[str, float] | None) -> tuple[float | None, float | None]:
    m = (res.get("metrics") or {})
    if goals:  # weighted: report the first goal's values; the full dict is in notes
        return None, None
    cur = m.get(metric) or {}
    return cur.get("start"), cur.get("final")


def search_tree(
    engine: PobEngine,
    xml: str,
    metric: str = "TotalDPS",
    *,
    points: int = 0,
    require: Sequence[str | int] = (),
    reset: bool = True,
    candidates: int = 200,
    goals: dict[str, float] | None = None,
    node_type: str = "Notable",
) -> TreeSearch:
    """Re-plan the regular passive tree of `xml` for `metric` (or weighted `goals`).

    `reset=True` (default) clears regular nodes first so `require`d nodes are planned in and the tree cannot
    end over budget (the engine skips `require` on a non-empty tree unless reset). `points=0` fills the whole
    budget. `candidates` caps what-if calcs per pick (cost lever: seconds ~ picks x candidates).
    """
    t0 = time.perf_counter()
    try:
        engine.load_build_xml(xml)
        t1 = time.perf_counter()
        res = engine.optimize_passives(
            metric=metric, points=points, node_type=node_type, candidates=candidates,
            goals=goals, require=list(require) or None, reset=reset,
        )
        t2 = time.perf_counter()
        stats = engine.get_stats(list(STAT_KEYS)).get("stats", {})
        out_xml = engine.get_xml()
    except Exception as ex:  # engine error / crash: caller decides whether to retry on a fresh engine
        return TreeSearch(metric, None, None, 0, 0, [], xml, {}, time.perf_counter() - t0, reset,
                          error=f"{type(ex).__name__}: {ex}")
    start, final = _values(res, metric, goals)
    notes = [res[k] for k in ("note", "requireNote") if res.get(k)]
    if goals:
        notes.append(f"weighted goals {goals}: {res.get('metrics')}")
    return TreeSearch(
        metric=metric, start=start, final=final,
        points_used=int(res.get("pointsUsed", 0)), points_remaining=int(res.get("pointsRemaining", 0)),
        allocated=list(res.get("allocated") or []), xml=out_xml, stats=stats,
        seconds=t2 - t1, reset=reset, notes=notes,
    )


DEFAULT_CAPS = (100, 200, 400)


def search_tree_caps(
    engine: PobEngine,
    xml: str,
    metric: str = "TotalDPS",
    *,
    caps: Sequence[int] = DEFAULT_CAPS,
    **kw: Any,
) -> TreeSearch:
    """`search_tree` once per candidate cap on the same engine; keep the best final `metric`.

    The greedy is non-monotonic in `candidates` (docs/tree.md), so one cap can be far from best. Each run reloads
    `xml`, so runs are independent. Weighted `goals` have no scalar value to compare: the first cap is kept.
    The winner's notes list every cap's result; if all runs fail the last error is returned."""
    runs = [(c, search_tree(engine, xml, metric, candidates=c, **kw)) for c in dict.fromkeys(caps)]
    ok = [(c, r) for c, r in runs if r.ok]
    if not ok:
        return runs[-1][1]
    if kw.get("goals"):
        c, best = ok[0]
    else:
        c, best = max(ok, key=lambda t: float("-inf") if t[1].final is None else t[1].final)
    best.seconds = sum(r.seconds for _, r in runs)
    best.notes = [*best.notes, "candidate caps: " + ", ".join(
        f"{k}={'FAILED' if not r.ok else r.final}" for k, r in runs) + f"; kept {c}"]
    return best


def search_trees(
    xmls: Sequence[str],
    metric: str = "TotalDPS",
    *,
    workers: int | None = None,
    engine_factory: Callable[[], PobEngine] = PobEngine,
    caps: Sequence[int] | None = None,
    **kw: Any,
) -> list[TreeSearch]:
    """One tree search per seed XML (with `caps`: best of several candidate caps, `search_tree_caps`), `workers` at a time, each on its own engine (recycled after the call
    because `load_build_xml` leaks engine memory, docs/engine-pool.md). A failed seed is retried once on a
    fresh engine; a second failure is returned with `error` set."""
    def one(x: str) -> TreeSearch:
        r = None
        for _ in (1, 2):
            with engine_factory() as eng:
                r = search_tree_caps(eng, x, metric, caps=caps, **kw) if caps else search_tree(eng, x, metric, **kw)
            if r.ok:
                break
        return r  # type: ignore[return-value]

    n = max(1, min(workers or 1, len(xmls)))
    with ThreadPoolExecutor(n) as ex:
        return list(ex.map(one, xmls))
