"""Benchmark metrics (B2, docs/benchmarks.md): boss time-to-kill with a pass/fail gate, survival against named hits,
and a pack density proxy. Pure functions over PoB stat dicts plus `evaluate`, which runs one engine evaluation per
benchmark through an EnginePool. A constant whose `value` is null is unsourced: the result is marked incomplete and
the dependent metric is None, never a guess."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any

from . import data

# PoB outputs the metrics read (all listed in data/metrics.yaml stat_keys).
BENCH_KEYS = ("TotalDPS", "FullDPS", "Speed", "AverageHit", "AreaOfEffectRadiusMetres", "ProjectileCount",
              "TotalEHP", "TotalNumberOfHits", "EHPSurvivalTime", "PhysicalMaximumHitTaken", "FireMaximumHitTaken",
              "ColdMaximumHitTaken", "LightningMaximumHitTaken", "ChaosMaximumHitTaken")
DAMAGE_TYPES = ("physical", "fire", "cold", "lightning", "chaos")


def benchmarks() -> dict[str, dict]:
    return data._load("benchmarks.yaml")["benchmarks"]


def _v(x: Any) -> Any:
    """Value of a {value, source} cell (or a bare value)."""
    return x.get("value") if isinstance(x, dict) else x


def pob_options(b: dict) -> dict:
    return {k: v for k, v in (b.get("pob_options") or {}).items() if v is not None}


def benchmark_hash(bid: str) -> str:
    """Stable hash of a benchmark's PoB options; joins the result-cache key like profile_hash."""
    return hashlib.sha256(json.dumps(pob_options(benchmarks()[bid]), sort_keys=True).encode()).hexdigest()[:12]


def _cells(b: dict):
    """Yield (path, cell) for every sourced-number cell, so structure and nulls can be checked uniformly."""
    for k in ("life", "uptime", "base_life", "spread_radius_m"):
        if k in b:
            yield k, b[k]
    for k, c in (b.get("gates") or {}).items():
        yield f"gates.{k}", c
    for m in b.get("monsters") or []:
        yield f"monsters.{m['rarity']}.count", m["count"]
        yield f"monsters.{m['rarity']}.life_mult", m["life_mult"]


def validate_benchmark(bid: str) -> tuple[list[str], list[str]]:
    """(errors, unsourced). Errors are structural (the file is wrong); unsourced lists null values (B3 work)."""
    b = benchmarks().get(bid)
    if b is None:
        return [f"unknown benchmark {bid!r}; known: {', '.join(benchmarks())}"], []
    errors, unsourced = [], []
    if b.get("kind") not in ("boss", "pack"):
        errors.append(f"{bid}: kind must be boss or pack")
    if not b.get("patch"):
        errors.append(f"{bid}: patch label missing")
    for path, c in _cells(b):
        if not (isinstance(c, dict) and "value" in c and c.get("source")):
            errors.append(f"{bid}.{path}: must be {{value, source}} with a source")
        elif c["value"] is None:
            unsourced.append(f"{bid}.{path}")
    for n, h in enumerate(b.get("hits") or []):
        if not h.get("name") or not h.get("source"):
            errors.append(f"{bid}.hits[{n}]: name and source required")
        for t in h:
            if t not in ("name", "source") and t not in DAMAGE_TYPES:
                errors.append(f"{bid}.hits[{n}]: unknown key {t!r}")
        unsourced += [f"{bid}.hits.{h.get('name')}.{t}" for t in DAMAGE_TYPES if t in h and h[t] is None]
    return errors, unsourced


@dataclass
class BossResult:
    id: str
    patch: str
    ttk_s: float | None = None
    dps: float | None = None
    dps_metric: str | None = None
    gate_ttk: bool | None = None            # None = not evaluable
    hit_margins: dict[str, float | None] = field(default_factory=dict)   # per named hit; None = unsourced
    survive: bool | None = None             # None while any hit is unsourced; never a guess
    survive_basis: str = "generic"          # "named" once all hits are sourced
    generic_hits_to_die: float | None = None  # PoB's own Pinnacle/Uber hit (TotalNumberOfHits)
    ehp: float | None = None
    ehp_survival_s: float | None = None
    flags: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool | None:
        return None if None in (self.gate_ttk, self.survive) else (self.gate_ttk and self.survive)


def boss_metrics(bid: str, stats: dict, dps_metric: str = "TotalDPS") -> BossResult:
    b = benchmarks()[bid]
    r = BossResult(bid, b["patch"], dps_metric=dps_metric)
    dps, life, up = stats.get(dps_metric), _v(b["life"]), _v(b["uptime"])
    r.dps = dps
    if dps and life and up:
        r.ttk_s = life / (dps * up)
        gmax = _v(b["gates"].get("ttk_s_max"))
        r.gate_ttk = None if gmax is None else r.ttk_s <= gmax
    else:
        r.flags.append("ttk unavailable: " + ("no DPS" if not dps else "life/uptime unsourced"))
    if dps_metric == "FullDPS":
        r.flags.append("FullDPS includes all-hits-landing and ailment/DoT: an upper bound")
    r.ehp, r.ehp_survival_s = stats.get("TotalEHP"), stats.get("EHPSurvivalTime")
    r.generic_hits_to_die = stats.get("TotalNumberOfHits")
    unsourced = False
    for h in b.get("hits") or []:
        margins = []
        for t in DAMAGE_TYPES:
            dmg, maxhit = h.get(t), stats.get(f"{t.capitalize()}MaximumHitTaken")
            if t in h and dmg is None:
                unsourced = True
            elif dmg and maxhit:
                margins.append(maxhit / dmg)
        r.hit_margins[h["name"]] = min(margins) if margins and not any(t in h and h[t] is None for t in DAMAGE_TYPES) else None
    if b.get("hits") and not unsourced and all(m is not None for m in r.hit_margins.values()):
        r.survive_basis = "named"
        r.survive = all(m >= 1 for m in r.hit_margins.values()) if _v(b["gates"].get("survive_all_hits")) else None
    else:
        r.flags.append("named hits unsourced: survival not judged, generic PoB hit shown (generic_hits_to_die)")
    _, un = validate_benchmark(bid)
    if un:
        r.flags.append("incomplete: " + ", ".join(u.split(".", 1)[1] for u in un))
    return r


@dataclass
class PackResult:
    id: str
    patch: str
    hits_to_kill: dict[str, int | None] = field(default_factory=dict)   # per rarity; None = unsourced
    coverage: float | None = None
    clear_s: float | None = None
    gate_clear: bool | None = None
    complete: bool = True
    flags: list[str] = field(default_factory=lambda: [
        "density proxy only: no movement, monster movement, on-kill effects or ailment spread; no swarm survival in v1"])


def pack_metrics(bid: str, stats: dict, projectile: bool = False) -> PackResult:
    b = benchmarks()[bid]
    r = PackResult(bid, b["patch"])
    base, hit = _v(b["base_life"]), stats.get("AverageHit")
    mons = b["monsters"]
    total = sum(_v(m["count"]) or 0 for m in mons)
    for m in mons:
        mult = _v(m["life_mult"])
        if base is None or mult is None:
            r.hits_to_kill[m["rarity"]], r.complete = None, False
        elif hit:
            r.hits_to_kill[m["rarity"]] = math.ceil(base * mult / hit)
        else:
            r.hits_to_kill[m["rarity"]], r.complete = None, False
    if not hit:
        r.flags.append("no AverageHit from PoB: hits-to-kill unavailable")
    if not r.complete:
        r.flags.append("incomplete: " + ", ".join(u.split(".", 1)[1] for u in validate_benchmark(bid)[1]))
    spread, radius, proj = _v(b["spread_radius_m"]), stats.get("AreaOfEffectRadiusMetres"), stats.get("ProjectileCount") or 1
    if radius and spread:
        r.coverage = min(1.0, (radius / spread) ** 2 * (proj if projectile else 1))
    elif projectile and total:
        r.coverage = min(1.0, proj / total)
        r.flags.append("no AoE radius: projectiles treated as single-target, coverage = projectiles / monsters")
    else:
        r.flags.append("no AoE radius: coverage unavailable")
    speed = stats.get("Speed")
    if r.complete and r.coverage and speed:
        r.clear_s = max(v for v in r.hits_to_kill.values() if v) / r.coverage / speed
        gmax = _v(b["gates"].get("clear_s_max"))
        r.gate_clear = None if gmax is None else r.clear_s <= gmax
    return r


def evaluate(pool, xml: str, bid: str, dps_metric: str = "TotalDPS", projectile: bool = False) -> BossResult | PackResult:
    """One engine evaluation under the benchmark's PoB options (cache key includes them via the mutation)."""
    b = benchmarks()[bid]
    errors, _ = validate_benchmark(bid)
    if errors:
        raise ValueError("; ".join(errors))
    from pos_pool.pool import Job

    keys = tuple(sorted(set(BENCH_KEYS) | {dps_metric}))
    [res] = pool.map([Job(xml, mutations=(("set_config", {"options": pob_options(b)}),), stat_keys=keys, tag=bid)])
    if not res.ok:
        raise RuntimeError(f"benchmark {bid}: engine failed: {res.error}")
    return boss_metrics(bid, res.stats, dps_metric) if b["kind"] == "boss" else pack_metrics(bid, res.stats, projectile)
