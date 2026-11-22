"""Interaction sweeps and key-piece ablation on a probe seed (I4, docs/ideation.md, docs/sweep.md).

`sweep(kind)`: one-change-at-a-time marginal of every catalogue entry of a kind on a metric, with the
artefact flags carried from G5 (a single change above 3x baseline is flagged for audit; a zero delta on an
entry with effect text is `possibly_unmodelled`, never `useless`).
`ablate(key_pieces)`: remove each key piece from the build and re-measure; verdicts `confirmed`,
`not_load_bearing`, `possibly_unmodelled`.

Kinds: `keystone`, `ascendancy` (notables of the seed's own ascendancy), `unique:<slot>`, `support`.
Metric = a PoB stat key under optional `options` (a `set_config` mutation, e.g. benchmark pob_options). Numbers
come from the engine only.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from pos_catalogue import Catalogue
from pos_engine.engine import PobEngine
from pos_pool.pool import EnginePool, Job

from .gear import BASE_TYPE_KIND, SLOTS, kind_of
from .supports import OUTLIER_FACTOR, compatible, eligible, _job as _support_job

CONFIRM_THRESHOLD = 0.10      # removal costing at least this share of the metric = confirmed (data/ideation.yaml, I3)
ZERO = 1e-9                   # relative tolerance for "no change"


@dataclass
class SweepEntry:
    kind: str
    id: str
    name: str
    value: float | None = None      # metric with the entry applied; None = not evaluated
    delta: float | None = None      # value - baseline
    rel: float | None = None        # delta / baseline
    points: int | None = None       # passive points the change spends (keystone / ascendancy notable path)
    flags: list[str] = field(default_factory=list)   # audit_outlier | possibly_unmodelled | no_effect | unreachable | over_budget | unparsed | failed


@dataclass
class Sweep:
    kind: str
    metric: str
    baseline: float
    entries: list[SweepEntry]       # best delta first; entries that could not be evaluated last
    evals: int = 0
    seconds: float = 0.0
    notes: list[str] = field(default_factory=list)

    def flagged(self, flag: str) -> list[SweepEntry]:
        return [e for e in self.entries if flag in e.flags]


@dataclass
class Ablation:
    piece: dict
    baseline: float
    without: float | None
    delta_rel: float | None         # (baseline - without) / baseline: share of the metric the piece is worth
    verdict: str                    # confirmed | not_load_bearing | possibly_unmodelled | not_testable
    replacement: str | None = None  # what stood in (support / unique)
    note: str = ""


def _has_text(e: dict) -> bool:
    return bool(e.get("stats") or e.get("text") or e.get("lines"))


def _keys(metric: str, extra: Sequence[str] = ()) -> tuple[str, ...]:
    return tuple(dict.fromkeys([metric, *extra]))


def _config(options: Mapping[str, Any] | None) -> tuple:
    return (("set_config", {"options": dict(options)}),) if options else ()


def _score(pool: EnginePool, jobs: list[Job], metric: str) -> list[float | None]:
    return [float(r.stats[metric]) if r.ok and r.stats and r.stats.get(metric) is not None else None for r in pool.map(jobs)]


def _finish(e: SweepEntry, base: float, value: float | None, has_text: bool) -> None:
    if value is None:
        e.flags.append("failed")
        return
    e.value, e.delta = value, value - base
    e.rel = e.delta / base if base else None
    if abs(e.delta) <= ZERO * max(abs(base), 1.0):
        e.flags.append("possibly_unmodelled" if has_text else "no_effect")
    elif base > 0 and e.delta > OUTLIER_FACTOR * base:
        e.flags.append("audit_outlier")


def _sort(entries: list[SweepEntry]) -> list[SweepEntry]:
    return sorted(entries, key=lambda e: (e.delta is None, -(e.delta or 0.0), e.name))


def _seed_build(xml: str, engine: PobEngine | None) -> dict:
    if engine is not None:
        engine.load_build_xml(xml)
        return engine.get_build()
    with PobEngine() as eng:
        eng.load_build_xml(xml)
        return eng.get_build()


def _tree_alloc(cat: Catalogue, pool: EnginePool, xml: str, entries: list[dict], metric: str, options, engine: PobEngine | None,
                kind: str, base: float) -> list[SweepEntry]:
    """Marginal of allocating each node (with its path). Path cost and reachability come from a direct engine
    call per node (one XML load each); only reachable nodes are scored by the pool."""
    own = engine is None
    eng = engine or PobEngine()
    out: list[SweepEntry] = []
    todo: list[tuple[SweepEntry, dict]] = []
    try:
        for e in entries:
            row = SweepEntry(kind, str(e["node"]), e["name"])
            out.append(row)
            eng.load_build_xml(xml)
            r = eng.alloc_passive(e["node"])
            if not r.get("ok"):
                row.flags.append("unreachable")
                continue
            if r.get("already"):
                row.points = 0
                row.flags.append("no_effect")
                continue
            row.points = r.get("pointsSpent")
            if r.get("warning"):
                row.flags.append("over_budget")
            todo.append((row, e))
    finally:
        if own:
            eng.close()
    jobs = [Job(xml, mutations=(*_config(options), ("alloc_passive", {"node": e["node"]})), stat_keys=_keys(metric)) for _, e in todo]
    for (row, e), v in zip(todo, _score(pool, jobs, metric)):
        _finish(row, base, v, _has_text(e))
    return out


def _unique_slot_kind(cat: Catalogue, u: dict) -> str | None:
    try:
        b = cat.resolve("base", u["base"]).entry
    except Exception:
        return None
    if not b:
        return None
    if b["type"] in BASE_TYPE_KIND:
        return BASE_TYPE_KIND[b["type"]]
    return "weapon" if b.get("weapon") else None


def sweep(cat: Catalogue, pool: EnginePool, xml: str, kind: str, metric: str = "TotalDPS", *,
          options: Mapping[str, Any] | None = None, engine: PobEngine | None = None,
          skill_id: str | None = None, supports: Sequence[str] | None = None) -> Sweep:
    """Marginal of each catalogue entry of `kind` on `metric`, one change at a time, on seed build `xml`."""
    t0 = time.perf_counter()
    [base] = _score(pool, [Job(xml, mutations=_config(options), stat_keys=_keys(metric))], metric)
    if base is None:
        raise RuntimeError("sweep: the probe seed failed to evaluate")
    notes: list[str] = []
    cfg = _config(options)
    if kind == "keystone":
        entries = _tree_alloc(cat, pool, xml, cat.entries("keystone"), metric, options, engine, kind, base)
    elif kind == "ascendancy":
        asc = _seed_build(xml, engine).get("ascendancy")
        pool_ = [n for n in cat.entries("notable") if n.get("ascendancy") == asc]
        if not pool_:
            notes.append(f"no catalogue notables for ascendancy {asc!r}")
        entries = _tree_alloc(cat, pool, xml, pool_, metric, options, engine, kind, base)
        notes.append("ascendancy points are a separate 8-point pool; `points` is the path cost, not budget-checked here")
    elif kind.startswith("unique:"):
        slot = kind.split(":", 1)[1]
        if slot not in SLOTS:
            raise ValueError(f"unknown slot {slot!r}; one of {', '.join(SLOTS)}")
        eng = engine or PobEngine()
        entries, todo, jobs = [], [], []
        try:
            for u in cat.entries("unique"):
                if _unique_slot_kind(cat, u) != kind_of(slot):
                    continue
                row = SweepEntry("unique", u["name"], u["name"])
                entries.append(row)
                t = eng.call("unique_text", name=u["name"], base=u.get("base"))
                if not t.get("ok"):
                    row.flags.append("failed")
                    continue
                raw = t["raw"] if t["raw"].lstrip().lower().startswith("rarity:") else "Rarity: UNIQUE\n" + t["raw"]
                chk = eng.call("check_item", raw=raw)
                if not chk.get("ok") or chk.get("unparsed"):
                    row.flags.append("unparsed")      # PoB cannot parse some line: would score as a silent zero
                    continue
                todo.append(row)
                jobs.append(Job(xml, stat_keys=_keys(metric), slot_item=(SLOTS[slot], raw)))
        finally:
            if engine is None:
                eng.close()
        if options:
            notes.append("options ignored for unique sweeps (slot_item fast path takes no mutations); put them in the seed's config")
        for row, v in zip(todo, _score(pool, jobs, metric)):
            _finish(row, base, v, True)
    elif kind == "support":
        if skill_id is None:
            raise ValueError("support sweep needs skill_id")
        skill = cat.get("skill", skill_id)
        if supports is None:
            gems = _seed_build(xml, engine).get("mainSkillGroup") or []
            supports = [r.entry["id"] for g in gems[1:] if (r := cat.resolve("support", g["name"])).entry]
        fixed = [cat.get("support", i) for i in supports]
        if not compatible(skill, fixed):
            raise ValueError("current supports are not mutually compatible")
        cands = eligible(cat, skill, fixed)
        jobs = [Job(xml, mutations=(*cfg, *_support_job(cat, skill, [*supports, c["id"]], _keys(metric), xml).mutations), stat_keys=_keys(metric)) for c in cands]
        entries = []
        for c, v in zip(cands, _score(pool, jobs, metric)):
            row = SweepEntry("support", c["id"], c["name"])
            _finish(row, base, v, False)       # catalogue has no gem text: a zero is `no_effect`, not `possibly_unmodelled`
            entries.append(row)
        notes.append("each support is ADDED to the current set (socket limit not enforced); eligibility per G5 rules")
    else:
        raise ValueError(f"unknown sweep kind {kind!r}: keystone, ascendancy, unique:<slot>, support")
    return Sweep(kind, metric, base, _sort(entries), evals=1 + sum(1 for e in entries if e.value is not None),
                 seconds=time.perf_counter() - t0, notes=notes)


# ---- ablation ----------------------------------------------------------------------------------------------
def ablate(cat: Catalogue, pool: EnginePool, xml: str, key_pieces: Sequence[Mapping[str, Any]], metric: str = "TotalDPS", *,
           options: Mapping[str, Any] | None = None, skill_id: str | None = None, supports: Sequence[str] | None = None,
           threshold: float = CONFIRM_THRESHOLD, engine: PobEngine | None = None) -> list[Ablation]:
    """Remove each key piece ({kind, id, [slot]}) and re-measure. keystone/notable: deallocated. support: swapped for
    the best other eligible support. unique: unequipped from `slot` (the best-rare replacement of ideation.md is
    the slate runner's job, I5; unequipping over-states the loss, so a unique verdict is an upper bound)."""
    cfg = _config(options)
    [base] = _score(pool, [Job(xml, mutations=cfg, stat_keys=_keys(metric))], metric)
    if base is None:
        raise RuntimeError("ablate: the build failed to evaluate")
    out: list[Ablation] = []
    for p in key_pieces:
        kind, id_ = p["kind"], p["id"]
        res = Ablation(dict(p), base, None, None, "not_testable")
        try:
            if kind in ("keystone", "notable"):
                e = cat.resolve(kind, id_).entry
                if not e:
                    res.note = f"{kind} {id_!r} not in catalogue"
                    out.append(res)
                    continue
                job = Job(xml, mutations=(*cfg, ("dealloc_passive", {"node": e["node"]})), stat_keys=_keys(metric))
                # dealloc of an unallocated node errors in the engine; check first so the failure is a clear note
                eng = engine or PobEngine()
                try:
                    eng.load_build_xml(xml)
                    if not eng.dealloc_passive(e["node"]).get("ok"):
                        res.note = f"{kind} {e['name']!r} is not allocated in this build"
                        out.append(res)
                        continue
                finally:
                    if engine is None:
                        eng.close()
                [v] = _score(pool, [job], metric)
                has_text = _has_text(e)
            elif kind == "unique":
                slot = p.get("slot")
                if slot not in SLOTS:
                    res.note = "unique key piece needs a `slot`"
                    out.append(res)
                    continue
                [v] = _score(pool, [Job(xml, mutations=(*cfg, ("unequip_item", {"slot": SLOTS[slot]})), stat_keys=_keys(metric))], metric)
                has_text = True
                res.replacement = "(slot emptied)"
            elif kind == "support":
                if skill_id is None:
                    res.note = "support ablation needs skill_id"
                    out.append(res)
                    continue
                skill = cat.get("skill", skill_id)
                cur = list(supports) if supports is not None else None
                if cur is None:
                    gems = _seed_build(xml, engine).get("mainSkillGroup") or []
                    cur = [r.entry["id"] for g in gems[1:] if (r := cat.resolve("support", g["name"])).entry]
                sid = cat.resolve("support", id_).entry["id"] if cat.resolve("support", id_).entry else None
                if sid not in cur:
                    res.note = f"support {id_!r} is not in the main skill's group"
                    out.append(res)
                    continue
                rest = [i for i in cur if i != sid]
                fixed = [cat.get("support", i) for i in rest]
                cands = [c for c in eligible(cat, skill, fixed) if c["id"] != sid]
                jobs = [Job(xml, mutations=(*cfg, *_support_job(cat, skill, [*rest, c["id"]], _keys(metric), xml).mutations), stat_keys=_keys(metric)) for c in cands]
                jobs.append(Job(xml, mutations=(*cfg, *_support_job(cat, skill, rest, _keys(metric), xml).mutations), stat_keys=_keys(metric)))
                vals = _score(pool, jobs, metric)
                scored = [(v, c) for v, c in zip(vals[:-1], cands) if v is not None]
                v = vals[-1]                                   # nothing in the freed socket
                res.replacement = "(socket left empty)"
                if scored:
                    bv, bc = max(scored, key=lambda t: t[0])
                    if v is None or bv > v:
                        v, res.replacement = bv, bc["name"]
                has_text = False
            else:
                res.note = f"kind {kind!r} cannot be ablated (keystone, notable, support, unique)"
                out.append(res)
                continue
        except Exception as ex:   # a bad piece must not sink the rest of the slate
            res.note = f"{type(ex).__name__}: {ex}"
            out.append(res)
            continue
        if v is None:
            res.note = "engine failed on the ablated build"
            out.append(res)
            continue
        res.without = v
        res.delta_rel = (base - v) / base if base else None
        if res.delta_rel is not None and res.delta_rel >= threshold:
            res.verdict = "confirmed"
        elif abs(base - v) <= ZERO * max(abs(base), 1.0) and has_text:
            res.verdict = "possibly_unmodelled"
        else:
            res.verdict = "not_load_bearing"
            if res.delta_rel is not None and res.delta_rel < 0:
                res.note = "removing it RAISES the metric"
        out.append(res)
    return out
