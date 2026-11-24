"""L6: prompt-to-report loop (docs/play.md).

player prompt -> ideas (a slate, written by the LLM client; the server has no embedded LLM, decided) -> screen every idea in
the sim -> creative improvement rounds (sim-verified single changes proposed from the finalists' own sweeps; a change is
kept only if the benchmarks improve) -> inner numeric loop (L3) on the finalists -> ranked, player-facing report with the
sim evidence for every kept change and a check of whether the build's core interaction compounds.
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .slate import Candidate, Slate, SlateReport
from .slate_run import EngineRunner, _audit, bench_value, rank_by_benchmarks, run_slate, screen_tier_for
from .sweep import Ablation

MIN_GAIN = 0.02            # a creative change is kept only if the mean benchmark value improves by at least this (relative)
BAD_FLAGS = {"audit_outlier", "possibly_unmodelled", "no_effect", "unreachable", "over_budget", "unparsed", "failed"}
SWEEP_KINDS = (("keystone", "keystones"), ("ascendancy", "notables"))   # sweep kind -> BuildSpec list the pick joins
SWEEP_MIN_REL = 0.03


# ---- pure helpers (unit-tested without an engine) ------------------------------------------------------------
def bench_gain(parent: Mapping[str, Any], child: Mapping[str, Any], bids: Sequence[str]) -> tuple[float | None, str]:
    """Mean relative improvement of `child` over `parent` across benchmarks both have a value for (lower value = better:
    time-to-kill, clear proxy). A child that fails a survival check the parent passes is never better. -> (gain, note)."""
    gains, notes, saved = [], [], False
    for b in bids:
        pv, pbad = bench_value(parent.get(b))
        cv, cbad = bench_value(child.get(b))
        if pv is None or cv is None or pv <= 0 or cv <= 0:
            continue
        if cbad and not pbad:
            notes.append(f"{b}: survival check lost")
            return -1.0, "; ".join(notes)
        gains.append(1.0 - cv / pv)
        if pbad and not cbad:
            notes.append(f"{b}: survival check now passes")
            saved = True                               # surviving the named hit outranks any value change
    if not gains:
        return None, "no benchmark value on both sides"
    g = sum(gains) / len(gains)
    return (max(g, MIN_GAIN) if saved else g), "; ".join(notes)


def joint_effect(base: float, without_all: float, singles: Sequence[float]) -> dict[str, Any]:
    """Does removing the core pieces together cost more than independent removal would? `singles` = each piece's metric
    with only that piece removed. Independent multiplicative effects predict joint share 1 - prod(1 - d_i); a larger measured
    share means the pieces feed each other (compounding), a smaller one means they overlap."""
    d = [max(0.0, 1.0 - s / base) for s in singles]
    expected = 1.0 - math.prod(1.0 - x for x in d)
    joint = 1.0 - without_all / base if base else 0.0
    return {"core_ratio": base / without_all if without_all else None, "joint_share": joint, "independent_share": expected,
            "synergy": joint - expected, "singles_share": d,
            "verdict": "compounds" if joint - expected > 0.02 else ("overlaps" if joint - expected < -0.02 else "independent")}


# ---- the runner (real engine) ------------------------------------------------------------------------------
def _best(res, tier: str):
    best = None
    for s in res.seeds:
        tr = s.tiers.get(tier)
        if tr and tr.ok and tr.value is not None and (best is None or tr.value > best[1].value):
            best = (s, tr)
    return best


class PlayRunner(EngineRunner):
    """`EngineRunner` plus what the outer loop needs: the screen build's xml, sweep proposals, rounds in the deep run, core check."""

    def __init__(self, *a, rounds: int = 3, **kw):
        super().__init__(*a, **kw)
        self.rounds = rounds
        self.last: dict[str, dict] = {}     # candidate -> {xml, supports, variant, tier_run(dict w/o xml), bench}

    # -- screening
    def _stash(self, c: Candidate, res, tier: str):
        b = _best(res, tier)
        if b is None:
            return None
        s, tr = b
        info = {"xml": tr.xml, "supports": list(s.supports), "variant": s.variant, "bench": dict(tr.bench), "value": tr.value,
                "tier_run": {k: v for k, v in tr.__dict__.items() if k != "xml"}}
        self.last[c.name] = info
        return info

    def screen(self, c, tier):
        res, abl = super().screen(c, tier)
        self._stash(c, res, tier)
        return res, abl

    def screen_light(self, c: Candidate, tier: str) -> dict | None:
        res = self._go(c, [tier], self.cfg["run"]["screen_realloc_rounds"], self.cfg["run"]["screen_tree_caps"])[0]
        return self._stash(c, res, tier)

    def deepen(self, c):
        tiers = list(self.slate.brief.get("tiers") or [self.cfg["run"]["screen_tier"]])
        from .orchestrate import DEFAULT_REALLOC_ROUNDS
        return self._go(c, tiers, DEFAULT_REALLOC_ROUNDS, None, rounds=self.rounds)[0]

    # -- creative step: sweeps on the finalist's own build
    def _options(self, c: Candidate) -> dict | None:
        from .benchmarks import benchmarks as _bms, pob_options
        bms = _bms()
        bid = next((b for b in self.slate.brief.get("benchmarks", []) if bms[b]["kind"] == "boss"), (self.slate.brief.get("benchmarks") or [None])[0])
        if not bid:
            return None
        o = pob_options(bms[bid])
        if c.spec is not None:
            from .data import conditions_not_in_fight
            o = {**conditions_not_in_fight(c.spec.conditions, bms[bid]["kind"])[0], **o}
        return o

    def propose(self, c: Candidate, n: int) -> list[tuple[Candidate, dict]]:
        """Up to `n` children of `c`: its best sweep picks (keystone, ascendancy notable) added to the spec. -> [(child, evidence)]."""
        from pos_engine.engine import PobEngine
        from pos_pool.pool import EnginePool
        from .sweep import sweep
        info, ctx = self.last[c.name], self.ctx[c.name]
        options = self._options(c)
        picks: list[tuple[float, str, str, Any]] = []
        with PobEngine() as eng, EnginePool(workers=max(1, self.workers // 2), cache=self.cache) as pool:   # half the pool: engine + workers OOM-killed at full width
            for kind, field in SWEEP_KINDS:
                sw = sweep(self.cat, pool, info["xml"], kind, ctx["metric"], options=options, engine=eng)
                have = set(getattr(c.spec, field))
                for e in sw.entries:
                    if e.rel is not None and e.rel >= SWEEP_MIN_REL and not (set(e.flags) & BAD_FLAGS) and e.id not in have and e.name not in have:
                        picks.append((e.rel, kind, field, e))
        picks.sort(key=lambda t: -t[0])
        out = []
        for rel, kind, field, e in picks[:n]:
            spec = replace(c.spec, **{field: [*getattr(c.spec, field), e.name]})
            child = replace(c, name=f"{c.name} + {e.name}", spec=spec, key_pieces=[*c.key_pieces, {"kind": "keystone" if kind == "keystone" else "notable", "id": e.name}],
                            source=f"sweep:{kind}")
            out.append((child, {"kind": kind, "id": e.id, "name": e.name, "sweep_rel": rel, "points": e.points}))
        return out

    # -- player-facing evidence on a deep build
    def core_check(self, c: Candidate, xml: str, variant, supports: Sequence[str], tier: str) -> dict:
        """Single ablation of every key piece plus the joint removal of the tree pieces: does the core interaction compound?"""
        from pos_engine.engine import PobEngine
        from pos_pool.pool import EnginePool, Job
        from .sweep import _config, _keys, _score
        ctx = self.ctx[c.name]
        sk = ctx["skill_id"].get(json.dumps(variant, sort_keys=True)) or next(iter(ctx["skill_id"].values()))
        abl = self._ablate(c, tier, xml, supports, ctx["metric"], sk, ctx["floors"])
        out: dict[str, Any] = {"ablations": [a.__dict__ for a in abl]}
        nodes = [a for a in abl if a.piece["kind"] in ("keystone", "notable") and a.without is not None]
        if len(nodes) < 2:
            out["joint"] = {"verdict": "n/a", "note": f"{len(nodes)} testable tree key piece(s); the joint test needs at least 2"}
            return out
        options = self._options(c)
        with PobEngine() as eng, EnginePool(workers=self.workers, cache=self.cache) as pool:
            muts = [("dealloc_passive", {"node": self.cat.resolve(a.piece["kind"], a.piece["id"]).entry["node"]}) for a in nodes]
            [v] = _score(pool, [Job(xml, mutations=(*_config(options), *muts), stat_keys=_keys(ctx["metric"]))], ctx["metric"])
        if v is None:
            out["joint"] = {"verdict": "n/a", "note": "engine failed on the all-removed build"}
        else:
            out["joint"] = {**joint_effect(nodes[0].baseline, v, [a.without for a in nodes]), "pieces": [a.piece["id"] for a in nodes]}
        return out

    def bench_xml(self, xml: str, c: Candidate) -> dict:
        """Benchmark any build (a meta export) under the same benchmarks and metric as the winner: {bid: result dict}."""
        from pos_pool.pool import EnginePool
        from .benchmarks import evaluate
        from dataclasses import asdict
        out = {}
        with EnginePool(workers=1, cache=None) as pool:
            for b in self.slate.brief.get("benchmarks", []):
                try:
                    out[b] = asdict(evaluate(pool, xml, b, self.ctx[c.name]["metric"], conditions=c.spec.conditions if c.spec else ()))
                except Exception as ex:   # noqa: BLE001
                    out[b] = {"error": f"{type(ex).__name__}: {ex}"}
        return out

    def diagnose_text(self, xml: str, c: Candidate) -> str:
        from .diagnose import diagnose, render
        try:
            return render(diagnose(xml, self.ctx[c.name]["metric"], self.slate.brief.get("benchmarks", [])), top=5)
        except Exception as ex:   # noqa: BLE001  a diagnosis failure must not sink the report
            return f"(diagnosis failed: {type(ex).__name__}: {ex})"


# ---- estimate ----------------------------------------------------------------------------------------------
def play_estimate(cands: Sequence[Candidate], brief: Mapping[str, Any], bases: Mapping[str, str], workers: int, *, k: int, outer_rounds: int,
                  children: int, inner_rounds: int, max_minutes: float, cfg: Mapping[str, Any] | None = None):
    """Upper bound: screen + ablate every idea, `outer_rounds` x k x `children` child screens (each as dear as the dearest screen),
    then k deep runs with the inner loop (`estimate(loop_rounds=)` is the L3 upper bound). Rates from data/rates.yaml."""
    from . import data
    from .orchestrate import estimate
    from .assemble import variants
    from .slate_run import estimate_slate
    cfg = cfg or data.ideation()
    slots = {c.name: max(1, len({**bases, **c.bases})) for c in cands}
    base = estimate_slate(cands, brief, slots, workers, max_minutes=max_minutes, k=0, cfg=cfg)
    n = len(cands) or 1
    per_screen = base.by_stage["screen"] / n
    extra_children = outer_rounds * min(k, n) * children * per_screen
    deep = sorted((estimate(len(variants(c.spec)) if c.spec else 1, max(1, len(brief.get("tiers", []))), slots[c.name], max(1, workers), max_minutes=max_minutes,
                            loop_rounds=inner_rounds).wall_seconds for c in cands), reverse=True)[:k]
    by = {**base.by_stage, "children": extra_children, "deepen": sum(deep)}
    return type(base)(base.candidates, min(k, len(cands)), sum(by.values()), max_minutes * 60, by, base.sources)


# ---- the loop ----------------------------------------------------------------------------------------------
def _retry(fn, log, what: str):
    """One retry: an engine killed by the memory watchdog (code -9) should not cost a finalist."""
    try:
        return fn()
    except Exception as ex:   # noqa: BLE001
        log(f"{what}: {type(ex).__name__}: {ex}; retrying once")
        return fn()


def play(slate: Slate, rep: SlateReport, runner, *, k: int = 3, outer_rounds: int = 2, children: int = 1, max_minutes: float | None = None,
         cfg: Mapping[str, Any] | None = None, out_dir: str | Path | None = None, estimate_text: str = "",
         log: Callable[[str], None] = lambda s: None) -> dict:
    from . import data
    t0 = time.perf_counter()
    cfg = cfg or data.ideation()
    bids = list(slate.brief.get("benchmarks", []))
    tier = screen_tier_for(slate.brief, cfg)
    tiers = list(slate.brief.get("tiers") or [tier])
    out_p = Path(out_dir) if out_dir else None
    sr = run_slate(slate, rep, runner, k=0, cfg=cfg, out_dir=(out_p / "screen") if out_p else None, estimate_text=estimate_text, log=log).to_dict()
    by_name = {c.name: c for c in slate.candidates}
    pool_: dict[str, dict] = {}
    for cr in sr["candidates"]:
        if cr["status"] == "screened":
            pool_[cr["name"]] = {"cand": by_name[cr["name"]], "bench": cr["screen"]["tier_run"].get("bench") or {}, "tr": cr["screen"]["tier_run"],
                                 "parent": None, "superseded_by": None, "round": 0, "evidence": None}
    if not pool_:
        raise RuntimeError("no candidate completed the screen")

    def ranked() -> list[str]:
        act = {n: p for n, p in pool_.items() if not p["superseded_by"]}
        return [n for n, _ in rank_by_benchmarks({n: p["bench"] for n, p in act.items()}, bids, _audit({n: p["tr"] for n, p in act.items()}))]

    steps: list[dict] = []
    stop = "rounds_done"
    for r in range(1, outer_rounds + 1):
        kept = 0
        for name in ranked()[:k]:
            if max_minutes and (time.perf_counter() - t0) / 60 > max_minutes:
                stop = "time_budget"
                break
            parent = pool_[name]
            try:
                kids = _retry(lambda: runner.propose(parent["cand"], children), log, f"propose {name}")
            except Exception as ex:   # noqa: BLE001
                steps.append({"round": r, "parent": name, "child": None, "kept": False, "note": f"proposal failed: {type(ex).__name__}: {ex}"})
                log(f"round {r}: proposals for {name} FAILED {ex}")
                continue
            if not kids:
                steps.append({"round": r, "parent": name, "child": None, "kept": False, "note": "no sweep pick above the threshold (or all flagged)"})
            for child, ev in kids:
                step = {"round": r, "parent": name, "child": child.name, "change": f"+ {ev['kind']} {ev['name']}", "sweep_rel": ev["sweep_rel"], "points": ev["points"]}
                try:
                    info = runner.screen_light(child, tier)
                except Exception as ex:   # noqa: BLE001
                    info, step["note"] = None, f"screen failed: {type(ex).__name__}: {ex}"
                if info is None:
                    step.update(kept=False, note=step.get("note", "child failed to evaluate"))
                else:
                    g, note = bench_gain(parent["bench"], info["bench"], bids)
                    step.update(gain=g, note=note, parent_bench=parent["bench"], child_bench=info["bench"])
                    step["kept"] = g is not None and g >= MIN_GAIN
                    if step["kept"]:
                        kept += 1
                        parent["superseded_by"] = child.name
                        pool_[child.name] = {"cand": child, "bench": info["bench"], "tr": info["tier_run"], "parent": name, "superseded_by": None, "round": r, "evidence": ev}
                steps.append(step)
                log(f"round {r}: {name} {step.get('change')}: gain {step.get('gain')} -> {'KEPT' if step['kept'] else 'rejected'}")
        if stop == "time_budget":
            break
        if not kept:
            stop = "no_gain"
            break

    finals = ranked()[:k]
    final_rows = []
    for name in finals:
        row = {"name": name, "parent": pool_[name]["parent"], "source": pool_[name]["cand"].source, "key_pieces": pool_[name]["cand"].key_pieces,
               "screen_bench": pool_[name]["bench"], "deep": None, "error": None}
        try:
            res = _retry(lambda: runner.deepen(pool_[name]["cand"]), log, f"deepen {name}")
            row["deep"] = {}
            for t in tiers:
                b = _best(res, t)
                if b:
                    s, tr = b
                    row["deep"][t] = {"variant": s.variant, "supports": s.supports, "tier_run": {kk: v for kk, v in tr.__dict__.items() if kk != "xml"}, "xml": tr.xml}
        except Exception as ex:   # noqa: BLE001
            row["error"] = f"{type(ex).__name__}: {ex}"
            log(f"deepen {name}: FAILED {row['error']}")
        final_rows.append(row)
    for t in tiers:
        have = {r["name"]: r["deep"][t]["tier_run"] for r in final_rows if r["deep"] and t in r["deep"]}
        for n, (nm, note) in enumerate(rank_by_benchmarks({a: b.get("bench") or {} for a, b in have.items()}, bids, _audit(have)), 1):
            row = next(x for x in final_rows if x["name"] == nm)
            row.setdefault("rank", {})[t] = n
            row.setdefault("rank_note", {})[t] = note
    top_t = tiers[-1]
    winner = min((r for r in final_rows if r.get("rank", {}).get(top_t)), key=lambda r: r["rank"][top_t], default=None)
    if winner:
        d = winner["deep"][top_t]
        c = pool_[winner["name"]]["cand"]
        try:
            winner["core"] = runner.core_check(c, d["xml"], d["variant"], d["supports"], top_t)
            winner["diagnosis"] = runner.diagnose_text(d["xml"], c)
        except Exception as ex:   # noqa: BLE001
            winner["core"] = {"error": f"{type(ex).__name__}: {ex}"}
    for r in final_rows:
        for d in (r["deep"] or {}).values():
            d.pop("xml", None)
    result = {"prompt": slate.prompt, "brief": dict(slate.brief), "screen_tier": tier, "tiers": tiers, "k": k, "outer_rounds": outer_rounds,
              "stop": stop, "minutes": round((time.perf_counter() - t0) / 60, 1), "estimate": estimate_text,
              "screened": [{"name": n, "parent": p["parent"], "superseded_by": p["superseded_by"], "round": p["round"], "source": p["cand"].source,
                            "bench": p["bench"], "evidence": p["evidence"]} for n, p in pool_.items()],
              "rejected": sr["rejected"], "failed": [{"name": c["name"], "error": c["error"]} for c in sr["candidates"] if c["status"] == "failed"],
              "steps": steps, "finalists": final_rows, "notes": [n for n in sr["notes"] if not n.startswith("successive halving")]}
    if out_p:
        out_p.mkdir(parents=True, exist_ok=True)
        (out_p / "play.json").write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")
        (out_p / "report.md").write_text(render_play_markdown(result), encoding="utf-8")
    return result


# ---- report ------------------------------------------------------------------------------------------------
def _bench_cell(b: Mapping[str, Any] | None) -> str:
    v, bad = bench_value(b)
    if v is None:
        return "n/a"
    unit = "s"
    return f"{v:,.0f}{unit}" + (" (dies)" if bad else "")


def render_play_markdown(d: dict, assumptions: Sequence[str] = ()) -> str:
    bids = list(d["brief"].get("benchmarks", []))
    L = [f"# Build report: {d['prompt']}", "",
         f"{len(d['screened'])} builds screened, {sum(1 for s in d['steps'] if s.get('kept'))} sim-verified improvements kept in {d['outer_rounds']} round(s) "
         f"(stopped: {d['stop']}), {len(d['finalists'])} finalists on the full pipeline. Run time {d['minutes']} min. "
         f"Benchmarks: {', '.join(bids)}; lower time is better. Tiers: {', '.join(d['tiers'])}.", ""]
    for a in assumptions:
        L += [f"> **ASSUMED:** {a}", ""]
    L += ["## Results", ""]
    for t in d["tiers"]:
        L += [f"### Tier {t}", "", "| rank | build | " + " | ".join(bids) + " | what it is |", "|---|---|" + "---|" * len(bids) + "---|"]
        for r in sorted((r for r in d["finalists"] if r.get("rank", {}).get(t)), key=lambda r: r["rank"][t]):
            tr = r["deep"][t]["tier_run"]
            sup = ", ".join(r["deep"][t]["supports"] or [])
            L.append(f"| {r['rank'][t]} | {r['name']} | " + " | ".join(_bench_cell((tr.get('bench') or {}).get(b)) for b in bids)
                     + f" | supports: {sup or '-'}; {tr.get('price') or 'no price'} |")
        L.append("")
    L += ["## How the ideas fared", "", "| idea | origin | " + " | ".join(bids) + " | outcome |", "|---|---|" + "---|" * len(bids) + "---|"]
    for s in d["screened"]:
        out = f"superseded by {s['superseded_by']}" if s["superseded_by"] else "in the final pool"
        L.append(f"| {s['name']} | {s['source']} (round {s['round']}) | " + " | ".join(_bench_cell(s["bench"].get(b)) for b in bids) + f" | {out} |")
    for r in d["rejected"]:
        L.append(f"| {r['name']} | gate | " + " | ".join("-" for _ in bids) + f" | rejected: {', '.join(r['codes'])} |")
    for r in d["failed"]:
        L.append(f"| {r['name']} | screen | " + " | ".join("-" for _ in bids) + f" | failed: {r['error']} |")
    L += ["", "## Improvement rounds", "",
          "Each row is one single change proposed from a finalist's own sweep and verified by the sim; kept only if the mean benchmark value improves by at least "
          f"{MIN_GAIN:.0%} and no survival check is lost.", "", "| round | parent | change | sweep says | sim says | verdict |", "|---|---|---|---|---|---|"]
    for s in d["steps"]:
        if not s.get("child"):
            L.append(f"| {s['round']} | {s['parent']} | - | - | - | {s['note']} |")
            continue
        g = s.get("gain")
        L.append(f"| {s['round']} | {s['parent']} | {s['change']} | {s['sweep_rel']:+.0%} DPS | " + (f"{g:+.1%} benchmark time" if g is not None else "n/a")
                 + f" | {'KEPT' if s['kept'] else 'rejected'} {s.get('note') or ''} |")
    L += ["", "The sweep predicts a DPS gain on the parent's build; the sim re-searches supports, tree and gear around the change and the benchmark decides, so a big sweep number can still lose.", ""]
    w = next((r for r in d["finalists"] if r.get("core")), None)
    if w:
        L += [f"## Does the core interaction compound? ({w['name']})", ""]
        core = w["core"]
        j = core.get("joint") or {}
        if "error" in core:
            L.append(f"Check failed: {core['error']}")
        elif j.get("verdict") == "n/a":
            L.append(f"Not testable: {j.get('note')}.")
        else:
            L += [f"Tree key pieces {', '.join(j['pieces'])}: removing them together loses {j['joint_share']:.0%} of the damage; independent multiplicative effects would predict {j['independent_share']:.0%} "
                  f"(synergy {j['synergy']:+.0%}, verdict **{j['verdict']}**). The build without them is {j['core_ratio']:.2f}x weaker.",
                  "Owner principle: the core interaction should give huge scaling; a core worth under about 2x, or `independent`/`overlaps`, is a marginal build, not a compounding one."]
        L += ["", "| key piece | worth (metric share lost) | EHP share lost | verdict |", "|---|---|---|---|"]
        for a in core.get("ablations", []):
            dr, er = a.get("delta_rel"), a.get("ehp_delta_rel")
            L.append(f"| {a['piece']['kind']}: {a['piece']['id']} | " + (f"{dr:.1%}" if dr is not None else "-") + " | " + (f"{er:.1%}" if er is not None else "-") + f" | {a['verdict']} {a.get('note') or ''} |")
        if w.get("diagnosis"):
            L += ["", "### What limits the winner (calibrated probes)", "", "```", w["diagnosis"].strip(), "```"]
    if d.get("meta"):
        L += ["", "## Comparison with a meta build", "", d["meta"]]
    L += ["", "## Notes", ""] + [f"- {n}" for n in d["notes"]]
    return "\n".join(L) + "\n"
