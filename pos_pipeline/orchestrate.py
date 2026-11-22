"""Orchestrator (G8a, docs/orchestrator.md): spec -> seeds x tiers -> supports, tree (once per seed), gear (per tier).

Stages are injected through `Stages`, so the loop is testable without an engine and later metrics
(benchmark TTK / clear proxies, B2) plug in by replacing the stage that scores candidates. The default
`EngineStages` wraps the merged stage functions (G3b assemble, G5 supports, G6 tree, G7/G7b gear)."""
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import yaml

from . import data
from .assemble import variants

RATES = Path(__file__).resolve().parents[1] / "data" / "rates.yaml"
DEFAULT_MAX_MINUTES = 45.0
DEFAULT_REALLOC_ROUNDS = 4
# PoB outputs shown in the report next to the objective metric
REPORT_KEYS = ("TotalDPS", "HitAilmentDPS", "FullDPS", "Speed", "Life", "EnergyShield", "TotalEHP", "Armour", "Evasion",
               "FireResist", "ColdResist", "LightningResist", "ChaosResist")


def load_rates(path: Path = RATES) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# ---- preflight --------------------------------------------------------------------------------------------
@dataclass
class Estimate:
    seeds: int
    tiers: int
    slots: int
    engine_evals: int
    core_seconds: float
    wall_seconds: float
    max_wall_seconds: float
    workers: int
    by_stage: dict[str, float] = field(default_factory=dict)   # wall seconds per stage
    sources: list[str] = field(default_factory=list)

    @property
    def over_cap(self) -> bool:
        return self.wall_seconds > self.max_wall_seconds

    def summary(self) -> str:
        parts = ", ".join(f"{k} {v / 60:.1f} min" for k, v in self.by_stage.items())
        return (f"{self.seeds} seed(s) x {self.tiers} tier(s) x {self.slots} slot(s): ~{self.engine_evals:,} engine evals, "
                f"~{self.wall_seconds / 60:.1f} min wall on {self.workers} worker(s) ({parts}); "
                f"cap {self.max_wall_seconds / 60:.0f} min{' EXCEEDED' if self.over_cap else ''}")


def estimate(seeds: int, tiers: int, slots: int, workers: int, *, realloc_rounds: int = DEFAULT_REALLOC_ROUNDS,
             max_minutes: float = DEFAULT_MAX_MINUTES, rates: Mapping[str, Any] | None = None) -> Estimate:
    """Cost of a run from measured rates (`data/rates.yaml`). Tree seeds run one per core, so the tree stage's wall
    time is ceil(seeds/workers) x per-seed time; the other stages share all workers."""
    r = rates or load_rates()
    table = r["gear_per_slot_few"] if slots <= 3 else r["gear_per_slot"]
    g = table["realloc_0" if realloc_rounds == 0 else "realloc_4"]
    # realloc_rounds between 1 and 3 is interpolated linearly between the two measured points
    frac = 0.0 if realloc_rounds <= 0 else min(realloc_rounds, 4) / 4
    g_core = table["realloc_0"]["core_s"] + frac * (table["realloc_4"]["core_s"] - table["realloc_0"]["core_s"])
    g_evals = table["realloc_0"]["evals"] + frac * (table["realloc_4"]["evals"] - table["realloc_0"]["evals"])
    w = max(1, workers)
    asm = seeds * r["assemble"]["core_s_per_seed"]
    sup = seeds * r["supports"]["core_s_per_seed"]
    tree_wall = math.ceil(seeds / w) * r["tree"]["core_s_per_seed"] if seeds else 0.0
    gear = seeds * tiers * slots * g_core
    by = {"assemble": asm / w, "supports": sup / w, "tree": tree_wall, "gear": gear / w}
    evals = seeds * (r["supports"]["evals_per_seed"] + r["tree"]["evals_per_seed"]) + seeds * tiers * slots * g_evals
    return Estimate(seeds, tiers, slots, int(evals), asm + sup + seeds * r["tree"]["core_s_per_seed"] + gear,
                    sum(by.values()), max_minutes * 60, w, by,
                    [f"{k}: {v['source']}" for k, v in {**{n: r[n] for n in ("assemble", "supports", "tree")}, "gear": g}.items()])


# ---- stages -----------------------------------------------------------------------------------------------
@dataclass
class Stages:
    """Callables the loop uses. `assemble(variant) -> obj(ok, xml, issues, main_skill)`;
    `supports(xml, skill_id) -> obj(best.supports, gain, evals, notes)`; `apply_supports(xml, skill_id, ids) -> xml`;
    `trees(xmls) -> [obj(ok, xml, error, gain, final, start, notes)]`;
    `gear(xml, tier, variant) -> obj(value, baseline, xml, items, price, floors_met, evals, notes)`."""
    assemble: Callable[[dict], Any]
    supports: Callable[[str, str], Any]
    apply_supports: Callable[[str, str, Sequence[str]], str]
    trees: Callable[[Sequence[str]], list]
    gear: Callable[[str, str, dict], Any]
    # optional (B4): `bench(xml, benchmark_id, variant) -> BossResult | PackResult`; `stats(xml, variant) -> dict` (report keys)
    bench: Callable[[str, str, dict], Any] | None = None
    stats: Callable[[str, dict], dict] | None = None
    # optional (K2): `actor(xml, variant) -> actors.Combined` for the spec's companion (effects, blend, combined metric)
    actor: Callable[[str, dict], Any] | None = None


@dataclass
class TierRun:
    tier: str
    ok: bool
    value: float | None = None
    baseline: float | None = None
    floors_met: bool | None = None
    price: str | None = None
    evals: int = 0
    items: dict[str, str] = field(default_factory=dict)     # slot -> readable description
    seconds: float = 0.0
    xml: str = ""
    notes: list[str] = field(default_factory=list)
    error: str | None = None
    stats: dict[str, Any] = field(default_factory=dict)      # PoB outputs of the final build (REPORT_KEYS)
    bench: dict[str, dict] = field(default_factory=dict)     # benchmark id -> BossResult/PackResult as dict, or {"error": ...}
    unparsed: list[str] = field(default_factory=list)        # mod ids / lines PoB could not parse (candidates rejected)
    actor: dict[str, Any] = field(default_factory=dict)      # companion result (K2): main, companion, total, without_companion, effects, blended


@dataclass
class SeedRun:
    variant: dict[str, str]
    ok: bool
    supports: list[str] = field(default_factory=list)
    supports_gain: float | None = None
    tree_gain: float | None = None
    tree_points: int | None = None
    seconds: dict[str, float] = field(default_factory=dict)
    tiers: dict[str, TierRun] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class RunResult:
    metric: str
    estimate: Estimate
    seeds: list[SeedRun]
    notes: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)       # spec summary, benchmark provenance, limitations (report header)

    def to_dict(self, xml: bool = False) -> dict:
        def clean(o):
            if isinstance(o, dict):
                return {k: clean(v) for k, v in o.items() if xml or k != "xml"}
            if isinstance(o, (list, tuple)):
                return [clean(v) for v in o]
            return o
        from dataclasses import asdict
        return clean(asdict(self))

    def best_per_tier(self) -> dict[str, tuple[dict[str, str], float]]:
        out: dict[str, tuple[dict[str, str], float]] = {}
        for s in self.seeds:
            for t, tr in s.tiers.items():
                if tr.ok and tr.value is not None and (t not in out or tr.value > out[t][1]):
                    out[t] = (s.variant, tr.value)
        return out


class RunRefused(Exception):
    """Preflight estimate is above the cap and `force` was not set."""
    def __init__(self, est: Estimate):
        super().__init__(est.summary() + " -- pass force=True (CLI --force) or raise the cap")
        self.estimate = est


def _jsonable(o: Any) -> Any:
    """Stats/benchmark dicts may carry numpy-ish or non-finite values; keep them JSON-safe (inf/nan -> None)."""
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, float) and not math.isfinite(o):
        return None
    return o


def actor_dict(c) -> dict:
    """actors.Combined -> JSON-safe dict for run.json / the report."""
    return _jsonable({"main": c.main, "companion": c.companion, "total": c.total, "without_companion": c.without_companion,
                      "blended": c.blended, "effects": [{"id": e.id, "uptime": e.uptime, "options": e.options, "source": e.source} for e in c.effects]})


# ---- the loop ---------------------------------------------------------------------------------------------
def run(spec, stages: Stages, *, metric: str, slots: int, workers: int, skill_id: str | Callable[[dict], str],
        realloc_rounds: int = DEFAULT_REALLOC_ROUNDS, max_minutes: float = DEFAULT_MAX_MINUTES, force: bool = False,
        dry_run: bool = False, benchmarks: Sequence[str] = (), meta: Mapping[str, Any] | None = None, out_dir: str | Path | None = None, log: Callable[[str], None] = lambda s: None) -> RunResult:
    """Per seed (axis combination): assemble -> supports -> tree, once; then per tier: gear.

    Supports are searched on the ungeared seed (G5 measured it that way): picks made before gear exists can differ
    from picks on a geared build; the per-tier support re-check from docs/pipeline.md is not built (see docs/orchestrator.md).
    A failed seed or tier is recorded and skipped; the rest of the run continues."""
    tiers = list(spec.tiers) or ["mid"]
    if getattr(spec, "companion", None) is not None:
        from . import actors
        actors.require_available(spec.companion.kind)   # pending actor: ActorUnavailable, before any work or number
        if not dry_run and stages.actor is None:
            raise actors.ActorUnavailable(spec.companion.kind, ["no actor stage supplied to run()"])
    vs = variants(spec)
    est = estimate(len(vs), len(tiers), slots, workers, realloc_rounds=realloc_rounds, max_minutes=max_minutes)
    log(est.summary())
    if est.over_cap and not force:
        raise RunRefused(est)
    from .report import run_meta
    bench_ids = list(benchmarks) or list(getattr(spec, "benchmarks", []) or [])
    res = RunResult(metric, est, [], meta={**run_meta(spec, bench_ids), **(meta or {})})
    if dry_run:
        return res

    # stage 1+2 per seed
    live: list[tuple[SeedRun, str, str]] = []          # (seed, xml, skill id)
    for v in vs:
        s = SeedRun(v, False)
        res.seeds.append(s)
        t0 = time.perf_counter()
        a = stages.assemble(v)
        s.seconds["assemble"] = time.perf_counter() - t0
        if not a.ok:
            s.error = "assemble failed: " + "; ".join(i.message for i in getattr(a, "issues", []) if i.severity == "error")
            log(f"seed {v or '(none)'}: {s.error}")
            continue
        for k, val in getattr(a, "deferred_axes", {}).items():
            s.notes.append(f"axis {k}={val}: used by the gear stage as the weapon base when it names a catalogue base, otherwise ignored")
        sk = skill_id(v) if callable(skill_id) else skill_id
        t0 = time.perf_counter()
        sup = stages.supports(a.xml, sk)
        s.seconds["supports"] = time.perf_counter() - t0
        s.supports, s.supports_gain = list(sup.best.supports), sup.gain
        s.notes += list(sup.notes)
        live.append((s, stages.apply_supports(a.xml, sk, s.supports), sk))
        log(f"seed {v or '(none)'}: supports {s.supports_gain:+.1%}")

    # tree: once per seed, seeds in parallel
    t0 = time.perf_counter()
    trees = stages.trees([x for _, x, _ in live]) if live else []
    dt = time.perf_counter() - t0
    gear_in: list[tuple[SeedRun, str]] = []
    for (s, _, _), tr in zip(live, trees):
        s.seconds["tree"] = dt
        if not tr.ok:
            s.error = f"tree failed: {tr.error}"
            log(f"seed {s.variant or '(none)'}: {s.error}")
            continue
        s.tree_gain, s.tree_points = tr.gain, tr.points_used
        s.notes += list(tr.notes)
        gear_in.append((s, tr.xml))

    # gear per seed x tier
    for s, xml in gear_in:
        s.ok = True
        for t in tiers:
            t0 = time.perf_counter()
            try:
                g = stages.gear(xml, t, s.variant)
            except Exception as ex:  # one bad tier must not sink the run
                s.tiers[t] = TierRun(t, False, error=f"{type(ex).__name__}: {ex}", seconds=time.perf_counter() - t0)
                log(f"seed {s.variant or '(none)'} tier {t}: FAILED {ex}")
                continue
            items = {sl: (c.unique or ", ".join(f"{a.group} r{a.rank}" for a in c.affixes) or "(no affixes)") + f" [{c.base}]"
                     for sl, c in g.items.items()}
            tr = TierRun(t, True, g.value, g.baseline, g.floors_met, getattr(g.price, "label", None), g.evals,
                         items, 0.0, g.xml, list(g.notes), unparsed=list(getattr(g, "rejected_unparsed", []) or []))
            tr.stats = _jsonable(stages.stats(g.xml, s.variant) if stages.stats else getattr(g, "stats", {}) or {})
            if stages.actor is not None and getattr(spec, "companion", None) is not None:
                try:
                    tr.actor = actor_dict(stages.actor(g.xml, s.variant))
                except Exception as ex:  # companion failure marks the cell; the player's numbers stand
                    tr.actor = {"error": f"{type(ex).__name__}: {ex}"}
            for bid in bench_ids:
                if stages.bench is None:
                    tr.bench[bid] = {"error": "no benchmark stage"}
                    continue
                try:
                    from dataclasses import asdict, is_dataclass
                    b = stages.bench(g.xml, bid, s.variant)
                    tr.bench[bid] = _jsonable(asdict(b) if is_dataclass(b) else dict(b))
                except Exception as ex:  # benchmark failure marks that cell, not the tier
                    tr.bench[bid] = {"error": f"{type(ex).__name__}: {ex}"}
            tr.seconds = time.perf_counter() - t0
            s.tiers[t] = tr
            log(f"seed {s.variant or '(none)'} tier {t}: {metric} {g.baseline} -> {g.value}")
    res.notes.append("pure-DPS metric leaves boots/belt (and other stat-only slots) without damage affixes; "
                     "survivability comes only from floors (G7b finding, not solved here)")
    if out_dir:
        d = Path(out_dir)
        d.mkdir(parents=True, exist_ok=True)
        (d / "run.json").write_text(json.dumps(res.to_dict(), indent=1, default=str), encoding="utf-8")
        from .report import write_report
        write_report(res.to_dict(), d)
    return res


# ---- real stages ------------------------------------------------------------------------------------------
def engine_stages(spec, cat, rep, bases: Mapping[str, str], *, workers: int, cache: str | Path | None = None,
                  realloc_rounds: int = DEFAULT_REALLOC_ROUNDS, floors: Mapping[str, Any] | None = None, tree_caps: Sequence[int] | None = None):
    """Context manager yielding (Stages, skill_id_fn). Owns one PobEngine and one EnginePool."""
    from contextlib import contextmanager

    @contextmanager
    def cm():
        from pos_engine.engine import PobEngine
        from pos_pool.pool import EnginePool

        from .assemble import assemble, _gem_line
        from .gear import STANDARD_FLOORS, search_gear
        from .supports import search_supports
        from .tree import DEFAULT_CAPS, search_trees

        fl = dict(floors if floors is not None else (STANDARD_FLOORS if spec.floors.get("resist_capped") else {}))
        allow = [cat.resolve("support", n).entry["id"] for n in data.profiles()[spec.config_profile].get("allow_triggered") or []]
        fixed = [cat.resolve("support", n).entry["id"] for n in spec.supports]
        require = list(spec.keystones) + list(spec.notables)
        with PobEngine() as eng, EnginePool(workers=workers, cache=cache) as pool:
            def skill_of(v):
                return cat.resolve("skill", v.get("main_skill", spec.main_skill)).entry["id"]

            def apply_supports(xml, skill_id, ids):
                text = "\n".join(_gem_line(e["name"]) for e in [cat.get("skill", skill_id)] + [cat.get("support", i) for i in ids])
                eng.load_build_xml(xml)
                eng.paste_skill(text)
                return eng.get_xml()

            def gear(xml, tier, variant):
                b = dict(bases)
                wb = variant.get("weapon_base")
                if wb and cat.resolve("base", wb).entry is not None:
                    b["weapon"] = cat.resolve("base", wb).entry["name"]
                return search_gear(cat, pool, eng, xml, tier, b, rep.metric, slots=tuple(b), floors=fl,
                                   realloc_rounds=realloc_rounds)

            def bench(xml, bid, variant):
                from .benchmarks import evaluate
                sk = cat.get("skill", skill_of(variant))
                return evaluate(pool, xml, bid, rep.metric, projectile="Projectile" in (sk.get("skill_types") or []))

            def stats(xml, variant):
                eng.load_build_xml(xml)
                return eng.get_stats(list(dict.fromkeys([rep.metric, *REPORT_KEYS])))["stats"]

            actor = None
            if spec.companion is not None:
                from . import actors
                from .assemble import assemble_companion
                prof_opts = data.profiles()[spec.config_profile].get("options") or {}
                mod = actors.actor(spec.companion.kind).get("model")
                if mod != "separate_build":   # native_pob waits for 1.0 data (K4); pending raised earlier in run()
                    actors.require_available(spec.companion.kind)
                    raise NotImplementedError(f"actor model {mod!r} is not built")
                cache_comp: dict[str, Any] = {}

                def player_metric(xml, options):
                    eng.load_build_xml(xml)
                    eng.set_config(options=dict(options) or None)
                    return float(eng.get_stats([rep.metric])["stats"][rep.metric])

                def companion_metric(cxml):
                    eng.load_build_xml(cxml)
                    return float(eng.get_stats([rep.metric])["stats"].get(rep.metric) or 0.0)

                def actor(xml, variant):
                    if "xml" not in cache_comp:
                        ca = assemble_companion(spec, cat, eng)
                        if not ca.ok:
                            raise RuntimeError("companion assembly failed: " + "; ".join(i.message for i in ca.errors))
                        cache_comp["xml"] = ca.xml
                    ids = [cat.resolve("skill", k.gem).entry["id"] for k in spec.companion.skills]
                    eff = actors.effects_for(spec.companion, ids)
                    m = actors.model_for(spec.companion.kind, player_metric=player_metric, companion_metric=companion_metric, base=prof_opts)
                    return m.evaluate(xml, cache_comp["xml"], eff)

            yield Stages(
                assemble=lambda v: assemble(spec, cat, eng, v),
                supports=lambda xml, sk: search_supports(cat, pool, xml, sk, fixed, rep.metric, allow_triggered=allow),
                apply_supports=apply_supports,
                trees=lambda xmls: search_trees(xmls, rep.metric, workers=workers, require=require, caps=tuple(tree_caps or DEFAULT_CAPS)),
                gear=gear, bench=bench, stats=stats, actor=actor,
            ), skill_of
    return cm()
