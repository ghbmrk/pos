"""Whole-catalogue census of zero-delta pieces by cause (L2, docs/loop.md 2.5 step 1, docs/probes.md).

Runs the existing sweeps (keystones, regular notables, the seed's ascendancy notables) on one probe seed, once per condition
profile, and counts every `possibly_unmodelled` entry by its engine-derived cause. It also ranks the stat-line primitives behind the
causes that mean "PoB has no model" (unparsed, no_compute) so the true size of the no-model set is counted, not guessed.
Notables of OTHER ascendancies cannot be allocated on this seed; run the census again with a spec of that ascendancy.
"""
from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from typing import Any, Mapping, Sequence

from pos_catalogue import Catalogue
from pos_engine.engine import PobEngine
from pos_pool.pool import EnginePool

from . import data
from .sweep import CAUSES, SweepEntry, _primitive, _tree_alloc, _score, _keys, _config, Job, sweep

KINDS = ("keystone", "notable", "ascendancy")


def _entries(cat: Catalogue, kind: str, xml: str, eng: PobEngine) -> list[dict]:
    if kind == "keystone":
        return cat.entries("keystone")
    if kind == "notable":
        return [n for n in cat.entries("notable") if not n.get("ascendancy")]
    asc = (eng.get_build() if eng.load_build_xml(xml) is not None else {}).get("ascendancy")
    return [n for n in cat.entries("notable") if n.get("ascendancy") == asc]


def _stats_of(cat: Catalogue, kind: str, node) -> list[str]:
    for e in cat.entries("keystone" if kind == "keystone" else "notable"):
        if e["node"] == int(node):
            return list(e.get("stats") or [])
    return []


def census(cat: Catalogue, pool: EnginePool, xml: str, metric: str, *, kinds: Sequence[str] = KINDS,
           profiles: Mapping[str, Mapping[str, Any]] | None = None, engine: PobEngine | None = None, log=print) -> dict:
    """{profile: {kind: {total, nonzero, by_cause: {cause: n}, unmodelled: [{name, cause, detail, stats}]}}, primitives: [...]}"""
    profiles = profiles or {"base": {}}
    own = engine is None
    eng = engine or PobEngine()
    out: dict[str, Any] = {"metric": metric, "pob_sha": cat.pob_sha, "profiles": {}, "causes": CAUSES}
    prims: dict[str, Counter] = defaultdict(Counter)
    try:
        for pname, opts in profiles.items():
            res: dict[str, Any] = {}
            for kind in kinds:
                t0 = time.perf_counter()
                ents = _entries(cat, kind, xml, eng)
                [base] = _score(pool, [Job(xml, mutations=_config(opts), stat_keys=_keys(metric))], metric)
                rows: list[SweepEntry] = _tree_alloc(cat, pool, xml, ents, metric, opts, None, kind, base)
                zero = [r for r in rows if "possibly_unmodelled" in r.flags]
                by = Counter(r.cause or "not_classified" for r in zero)
                for r in zero:
                    for ln in _stats_of(cat, kind, r.id):
                        prims[r.cause or "not_classified"][_primitive(ln)] += 1
                res[kind] = {"total": len(rows), "evaluated": sum(1 for r in rows if r.value is not None),
                             "unreachable": sum(1 for r in rows if "unreachable" in r.flags),
                             "nonzero": sum(1 for r in rows if r.value is not None and "possibly_unmodelled" not in r.flags and "no_effect" not in r.flags),
                             "possibly_unmodelled": len(zero), "by_cause": dict(by.most_common()),
                             "unmodelled": [{"name": r.name, "cause": r.cause, "detail": r.cause_detail} for r in zero],
                             "seconds": round(time.perf_counter() - t0, 1)}
                log(f"[{pname}] {kind}: {len(rows)} entries, {len(zero)} zero-delta by cause {dict(by)} ({res[kind]['seconds']}s)")
            out["profiles"][pname] = res
    finally:
        if own:
            eng.close()
    out["primitives"] = {c: [{"primitive": k, "count": n} for k, n in cnt.most_common(40)] for c, cnt in prims.items()}
    return out


def render(c: dict) -> str:
    lines = [f"# Zero-delta census on {c['metric']} (pin {c['pob_sha']})", ""]
    for pname, res in c["profiles"].items():
        lines += [f"## profile `{pname}`", "", "| kind | entries | evaluated | non-zero | zero-delta | by cause |", "|---|---|---|---|---|---|"]
        for k, r in res.items():
            lines.append(f"| {k} | {r['total']} | {r['evaluated']} | {r['nonzero']} | {r['possibly_unmodelled']} | " + ", ".join(f"{a} {b}" for a, b in r["by_cause"].items()) + " |")
        lines.append("")
    lines += ["## Causes", ""] + [f"- `{k}`: {v}" for k, v in c["causes"].items()] + [""]
    for cause in ("unparsed", "no_compute"):
        if c["primitives"].get(cause):
            lines += [f"## Missing primitives: `{cause}` (stat lines, numbers as #)", ""] + [f"- {p['count']}x {p['primitive']}" for p in c["primitives"][cause][:25]] + [""]
    return "\n".join(lines)
