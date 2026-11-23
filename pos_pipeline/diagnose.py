"""Diagnosis by calibrated probes (L2, docs/loop.md 2.2, docs/probes.md).

A probe is one PoB custom-modifier line from `data/probes.yaml`. `diagnose(xml)` applies each probe to a build, reads the
engine's outputs, and returns shadow prices (relief of the binding constraint per tier point), the binding constraint
and the probes that failed. A probe is excluded, never reported as zero, when PoB did not parse its line, when the engine
failed, or when it fails a calibration case (reference build, expected sign and tolerance). A parsed, calibrated probe
that moves nothing is a real zero and is marked `inert`. Numbers come from the engine only.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Sequence

from pos_engine.engine import PobEngine, recycle

from . import data
from .benchmarks import BENCH_KEYS, benchmarks, boss_metrics, pack_metrics, pob_options, _v

METRIC_KEY = {"dps": "FullDPS", "ehp": "TotalEHP", "life": "Life", "es": "EnergyShield"}
CAL_KEYS = tuple(METRIC_KEY.values())
CACHE_DIR = Path(__file__).resolve().parents[1] / "runtime"
HEADLESS = Path(__file__).resolve().parents[1] / "pos_engine" / "pob_headless.lua"


def probes() -> list[dict]:
    return data._load("probes.yaml")["probes"]


def references() -> dict[str, dict]:
    return data._load("probes.yaml")["references"]


def rejected() -> list[dict]:
    return data._load("probes.yaml").get("rejected") or []


def probe_cost(p: dict, tiers=None) -> float | None:
    """Tier points of the probe step: affix points of (group, rank) x affixes; None when no gear affix buys the lever."""
    c = p.get("cost")
    if not c:
        return None
    if tiers is None:
        from pos_tiers.tiers import TierTable
        tiers = TierTable.load()
    return tiers.affix_points(c["group"], int(c.get("rank", 3))) * float(c.get("affixes", 1))


# ---- engine helpers ---------------------------------------------------------------------------------------------------
def _apply_probe(eng: PobEngine, line: str, keys: Sequence[str], options: dict | None = None) -> tuple[dict, int]:
    """(stats, parsed mod count) with the probe line applied on top of the loaded build."""
    r = eng.set_config(options=options or None, custom_mods=line, keys=list(keys))
    return r.get("stats") or {}, int((r.get("customMods") or {}).get("count", 0))


def _clear(eng: PobEngine) -> None:
    eng.set_config(custom_mods="")


def _rel(after: float | None, before: float | None) -> float | None:
    if after is None or before is None:
        return None
    if not before:
        return None if after else 0.0
    return after / before - 1.0


def _build_reference(eng: PobEngine, ref: dict) -> None:
    eng.new_build()
    eng.paste_skill(ref["skill"])
    if ref.get("options"):
        eng.set_config(options=ref["options"])


# ---- calibration ------------------------------------------------------------------------------------------------------
@dataclass
class CaseResult:
    ref: str
    metric: str
    rel: float | None
    rel_min: float
    rel_max: float
    ok: bool


@dataclass
class Calibration:
    id: str
    line: str
    parsed: bool
    ok: bool
    cases: list[CaseResult] = field(default_factory=list)
    reason: str = ""


def calibrate(engine: PobEngine | None = None, only: Sequence[str] | None = None) -> dict[str, Calibration]:
    """Run every calibration case of every probe on its reference build. ~15 s."""
    eng = engine or PobEngine()
    out: dict[str, Calibration] = {}
    try:
        base: dict[str, dict] = {}
        for rid, ref in references().items():
            _build_reference(eng, ref)
            base[rid] = eng.get_stats(list(CAL_KEYS))["stats"]
        for p in probes():
            if only and p["id"] not in only:
                continue
            cal = Calibration(p["id"], p["line"], parsed=True, ok=True)
            for case in p.get("expect") or []:
                rid, m = case["ref"], case["metric"]
                if engine is None:
                    eng = recycle(eng)
                _build_reference(eng, references()[rid])
                stats, n = _apply_probe(eng, p["line"], CAL_KEYS)
                if n == 0:
                    cal.parsed, cal.ok, cal.reason = False, False, "PoB did not parse the line (it is dropped silently)"
                    break
                rel = _rel(stats.get(METRIC_KEY[m]), base[rid].get(METRIC_KEY[m]))
                good = rel is not None and case["rel_min"] - 1e-3 <= rel <= case["rel_max"] + 1e-3
                cal.cases.append(CaseResult(rid, m, rel, case["rel_min"], case["rel_max"], good))
                if not good:
                    cal.ok = False
                    cal.reason = f"{rid}/{m}: measured {rel if rel is None else round(rel, 4)} outside [{case['rel_min']}, {case['rel_max']}]"
            if not p.get("expect"):
                cal.ok, cal.reason = False, "no calibration case"
            out[p["id"]] = cal
    finally:
        if engine is None:
            eng.close()
    return out


def _calibration_key(pob_sha: str) -> str:
    h = hashlib.sha256()
    h.update((data.DATA / "probes.yaml").read_bytes())
    h.update(HEADLESS.read_bytes())
    h.update(pob_sha.encode())
    return h.hexdigest()[:16]


_MEM: dict[str, dict[str, Calibration]] = {}


def calibration(pob_sha: str | None = None, engine: PobEngine | None = None, refresh: bool = False) -> dict[str, Calibration]:
    """Calibration of every probe, cached per (probes.yaml, engine script, PoB pin) in memory and in runtime/."""
    if pob_sha is None:
        from pos_catalogue import Catalogue
        pob_sha = Catalogue.load().pob_sha
    key = _calibration_key(pob_sha)
    if not refresh and key in _MEM:
        return _MEM[key]
    f = CACHE_DIR / f"probe_calibration_{key}.json"
    if not refresh and f.exists():
        raw = json.loads(f.read_text())
        _MEM[key] = {k: Calibration(**{**v, "cases": [CaseResult(**c) for c in v["cases"]]}) for k, v in raw.items()}
        return _MEM[key]
    res = calibrate(engine)
    CACHE_DIR.mkdir(exist_ok=True)
    f.write_text(json.dumps({k: asdict(v) for k, v in res.items()}))
    _MEM[key] = res
    return res


# ---- diagnosis --------------------------------------------------------------------------------------------------------
@dataclass
class Constraint:
    name: str                 # survive@<bench> | ttk@<bench> | clear@<bench>
    pressure: float           # required / actual: > 1 means the constraint is violated, bigger = further from satisfied
    detail: str = ""


@dataclass
class ProbeResult:
    id: str
    line: str
    status: str               # ok | inert | failed
    reason: str = ""
    cost_points: float | None = None
    gains: dict[str, float | None] = field(default_factory=dict)       # relative change per output (dps, ehp) and relief per constraint
    price: float | None = None                                         # relief of the binding constraint per tier point
    notes: list[str] = field(default_factory=list)                     # e.g. sign reversed vs calibration on this build


@dataclass
class Diagnosis:
    metric: str
    baseline: dict[str, float | None]
    constraints: list[Constraint]                 # tightest first
    binding: str                                  # name of the binding constraint, or "objective" when none is judged
    probes: list[ProbeResult]                     # ok first, best shadow price first
    failed: list[ProbeResult]                     # excluded: never shown as zero
    unjudged: list[str] = field(default_factory=list)   # constraints whose gate or constants are unsourced
    seconds: float = 0.0

    def top(self, n: int = 5) -> list[ProbeResult]:
        return [p for p in self.probes if p.status == "ok"][:n]

    def to_dict(self) -> dict:
        return asdict(self)


def _constraints(bid: str, stats: dict, dps_metric: str) -> tuple[dict[str, Constraint], list[str]]:
    b = benchmarks()[bid]
    out: dict[str, Constraint] = {}
    unjudged: list[str] = []
    if b["kind"] == "boss":
        r = boss_metrics(bid, stats, dps_metric)
        gmax = _v(b["gates"].get("ttk_s_max"))
        if r.ttk_s and gmax:
            out[f"ttk@{bid}"] = Constraint(f"ttk@{bid}", r.ttk_s / gmax, f"TTK {r.ttk_s:.0f}s vs gate {gmax}s")
        else:
            unjudged.append(f"ttk@{bid}")
        margins = [m for m in r.hit_margins.values() if m]
        if r.survive_basis == "named" and margins:
            out[f"survive@{bid}"] = Constraint(f"survive@{bid}", 1.0 / min(margins), f"min hit margin {min(margins):.2f} (need >= 1)")
        else:
            unjudged.append(f"survive@{bid}")
    else:
        r = pack_metrics(bid, stats)
        gmax = _v(b["gates"].get("clear_s_max"))
        if r.clear_s and gmax:
            out[f"clear@{bid}"] = Constraint(f"clear@{bid}", r.clear_s / gmax, f"clear {r.clear_s:.0f}s vs gate {gmax}s")
        else:
            unjudged.append(f"clear@{bid}")
    return out, unjudged


def _measure(eng: PobEngine, xml: str, keys, line: str = "", options: dict | None = None) -> tuple[dict, int]:
    """Stats of the build under `options` with `line` applied. The build is reloaded first so no earlier option or probe
    leaks in (set_config mutates the engine's config)."""
    eng.load_build_xml(xml)
    return _apply_probe(eng, line, keys, options)


def diagnose(xml: str, metric: str = "FullDPS", benchmark_ids: Sequence[str] = (), *, engine: PobEngine | None = None,
             cal: dict[str, Calibration] | None = None, only: Sequence[str] | None = None, tiers=None) -> Diagnosis:
    """Apply every calibrated probe to the build and rank levers by shadow price on the binding constraint.
    With no benchmark gate that can be judged, the binding constraint is `objective` and levers rank by relative gain in `metric`."""
    import time
    t0 = time.perf_counter()
    cal = cal if cal is not None else calibration()
    eng = engine or PobEngine()
    keys = tuple(dict.fromkeys([metric, "TotalEHP", *BENCH_KEYS]))
    bench = {bid: pob_options(benchmarks()[bid]) for bid in benchmark_ids}
    try:
        base_stats, _ = _measure(eng, xml, keys)
        if not base_stats.get(metric):
            raise ValueError(f"build has no {metric}: nothing to diagnose (attack skill without a weapon?)")
        base_c: dict[str, Constraint] = {}
        unjudged: list[str] = []
        for bid, opts in bench.items():
            st, _ = _measure(eng, xml, keys, "", opts)
            c, u = _constraints(bid, st, metric)
            base_c.update(c)
            unjudged += u
        binding = max(base_c.values(), key=lambda c: c.pressure).name if base_c else "objective"
        results: list[ProbeResult] = []
        for p in probes():
            if only and p["id"] not in only:
                continue
            pr = ProbeResult(p["id"], p["line"], "ok", cost_points=probe_cost(p, tiers))
            c = cal.get(p["id"])
            if c is None or not c.ok:
                pr.status, pr.reason = "failed", "calibration: " + (c.reason if c else "not calibrated")
                results.append(pr)
                continue
            try:
                if engine is None:
                    eng = recycle(eng)   # owned engine: the per-load leak would otherwise reach the hard cap mid-diagnosis
                st, n = _measure(eng, xml, keys, p["line"])
                if n == 0:
                    pr.status, pr.reason = "failed", "PoB did not parse the line on this build"
                    results.append(pr)
                    continue
                pr.gains["dps"] = _rel(st.get(metric), base_stats.get(metric))
                pr.gains["ehp"] = _rel(st.get("TotalEHP"), base_stats.get("TotalEHP"))
                for bid, opts in bench.items():
                    sb, _ = _measure(eng, xml, keys, p["line"], opts)
                    cs, _u = _constraints(bid, sb, metric)
                    for name, c0 in base_c.items():
                        if name in cs:
                            pr.gains[name] = (c0.pressure - cs[name].pressure) / c0.pressure   # relief; > 0 helps
                exp = [case for case in (next(q for q in probes() if q["id"] == p["id"]).get("expect") or []) if case["metric"] == "dps"]
                d = pr.gains["dps"]
                if d is not None and p.get("universal") and any(c_["rel_min"] > 0 for c_ in exp):
                    if d < -1e-6:
                        pr.notes.append("sign REVERSED vs calibration: a mechanism in this build flips the lever (e.g. Rakiata's Flow inverts enemy resistances); the measured value is true for this build")
                    elif abs(d) < 1e-9:
                        pr.notes.append("zero here though calibration expects a gain: a mechanism in this build removes the lever")
                relief = pr.gains.get(binding) if binding != "objective" else pr.gains["dps"]
                if relief is not None and pr.cost_points:
                    pr.price = relief / pr.cost_points
                if all((v is None or abs(v) < 1e-9) for v in pr.gains.values()):
                    pr.status = "inert"
            except Exception as ex:   # one bad probe must not sink the diagnosis
                pr.status, pr.reason = "failed", f"{type(ex).__name__}: {ex}"
            results.append(pr)
    finally:
        if engine is None:
            eng.close()
    key = binding if binding != "objective" else "dps"
    ok = [r for r in results if r.status != "failed"]
    ok.sort(key=lambda r: (r.status == "inert", r.price is None, -(r.price if r.price is not None else (r.gains.get(key) or 0.0))))
    failed = [r for r in results if r.status == "failed"]
    return Diagnosis(metric, {k: base_stats.get(k) for k in (metric, "TotalEHP")}, sorted(base_c.values(), key=lambda c: -c.pressure),
                     binding, ok, failed, unjudged, round(time.perf_counter() - t0, 1))


def render(d: Diagnosis, top: int = 8) -> str:
    """Plain-text diagnosis: binding constraint, levers by shadow price, excluded probes."""
    lines = [f"metric {d.metric} = {d.baseline.get(d.metric):,.0f}; EHP {d.baseline.get('TotalEHP') or 0:,.0f}; {d.seconds}s"]
    if d.constraints:
        lines.append("constraints (pressure = required/actual; > 1 violated):")
        lines += [f"  {c.name}: {c.pressure:.2f}  {c.detail}{'   <- BINDING' if c.name == d.binding else ''}" for c in d.constraints]
    else:
        lines.append("no benchmark constraint could be judged: levers ranked by relative gain in the metric")
    if d.unjudged:
        lines.append("unjudged (gate or constants unsourced): " + ", ".join(d.unjudged))
    key = d.binding if d.binding != "objective" else "dps"
    lines.append(f"levers on {d.binding} (relief per tier point; relief = share of the pressure removed):")
    for p in d.top(top):
        pr = "n/a (no gear affix)" if p.price is None else f"{p.price:.4f}/pt"
        lines.append(f"  {p.id:18s} {p.line:48s} relief {p.gains.get(key) or 0:+.1%}  cost {p.cost_points if p.cost_points is not None else '-'}  price {pr}" + "".join(f"\n      ! {n}" for n in p.notes))
    inert = [p.id for p in d.probes if p.status == "inert"]
    if inert:
        lines.append("inert here (parsed, calibrated, no effect): " + ", ".join(inert))
    if d.failed:
        lines.append("EXCLUDED (failed, not zero): " + "; ".join(f"{p.id} ({p.reason})" for p in d.failed))
    return "\n".join(lines)
