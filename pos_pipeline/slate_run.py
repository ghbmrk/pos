"""Slate runner (I5, docs/ideation.md sections 4-6, docs/slate-run.md).

A validated slate (`validate_slate`, I3) is run in three steps:
  screen   one cheap run per kept candidate at one tier (no realloc rounds, one tree cap), then ablation of its key pieces
  rank     cross-archetype ranking on the BENCHMARK metrics only (never the per-skill DPS: not comparable across skills)
  deepen   the top K by screen rank get the full run at every brief tier

Engine work is behind `CandidateRunner` so the control flow, ranking and report are testable without an engine;
`EngineRunner` is the real one (it wraps `orchestrate.run` and `sweep.ablate`). No game fact is supplied here: every
number is a PoB output or a benchmark formula over PoB outputs, labelled as in `report.py`.
"""
from __future__ import annotations

import json
import re
import sqlite3
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence

from pos_catalogue import Catalogue

from . import data
from .assemble import variants
from .orchestrate import DEFAULT_REALLOC_ROUNDS, Estimate, RunResult, estimate, load_rates
from .report import _bench_cell, _num
from .slate import Candidate, Slate, SlateReport
from .sweep import Ablation

PIECE_KINDS = ("keystone", "notable", "unique", "support")


# ---- result model -----------------------------------------------------------------------------------------
@dataclass
class CandidateRun:
    name: str
    source: str
    vector: dict[str, str]
    claims: list[dict]
    key_pieces: list[dict]
    status: str = "pending"                     # screened | failed
    error: str | None = None
    screen: dict | None = None                  # best tier run of the screen: {variant, supports, tier_run}
    ablations: list[dict] = field(default_factory=list)
    screen_rank: int | None = None
    rank_note: str = ""
    deep: dict | None = None                    # tier -> {variant, supports, tier_run}, from the full run
    deep_rank: dict[str, int] = field(default_factory=dict)   # tier -> rank among the deepened
    deepen_error: str | None = None
    conditions: list[str] = field(default_factory=list)   # declared config conditions (I11), applied in screen, ablation and deepen


@dataclass
class SlateRun:
    prompt: str
    brief: dict
    screen_tier: str
    deepen_k: int
    candidates: list[CandidateRun]
    estimate: str = ""
    rejected: list[dict] = field(default_factory=list)      # candidates the gate dropped: {name, codes}
    notes: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class CandidateRunner(Protocol):
    def screen(self, c: Candidate, tier: str) -> tuple[RunResult, list[Ablation]]: ...
    def deepen(self, c: Candidate) -> RunResult: ...


# ---- ranking on benchmark metrics -------------------------------------------------------------------------
def bench_value(b: Mapping[str, Any] | None) -> tuple[float | None, bool]:
    """(value to minimise, disqualified). Boss: time-to-kill, disqualified if the survival check says DIES (`survive`
    False; None = unsourced, not a penalty). Pack: clear time proxy. A missing / error / n/a cell gives value None."""
    if not b or "error" in b:
        return None, False
    if "ttk_s" in b:
        return b.get("ttk_s"), b.get("survive") is False
    return b.get("clear_s"), False


def artefact_flag(stats: Mapping[str, Any] | None, bench: Mapping[str, Any] | None) -> str | None:
    """G5 audit flag for a candidate: FullDPS > OUTLIER_FACTOR x TotalDPS while a boss time-to-kill rests on FullDPS (the
    Fiery Death pattern: a hidden trigger inflates FullDPS). Returns the note text, or None. Time-to-kill on TotalDPS is not
    affected by FullDPS, so it is not flagged."""
    from pos_pipeline.supports import OUTLIER_FACTOR
    full, total = (stats or {}).get("FullDPS"), (stats or {}).get("TotalDPS")
    if not full or not total or full <= OUTLIER_FACTOR * total:
        return None
    if not any(isinstance(b, Mapping) and b.get("dps_metric") == "FullDPS" and "ttk_s" in b for b in (bench or {}).values()):
        return None
    return f"ARTEFACT AUDIT: FullDPS {full:,.0f} > {OUTLIER_FACTOR:g}x TotalDPS {total:,.0f}; time-to-kill rests on FullDPS, ranked after unflagged candidates"


def rank_by_benchmarks(cells: Mapping[str, Mapping[str, Mapping[str, Any] | None]], bids: Sequence[str],
                       audit: Mapping[str, str] | None = None) -> list[tuple[str, str]]:
    """`cells[name][bid]` -> [(name, note)] best first. Per benchmark the candidates with a value are ordered by
    (survival-failed last, value, name) and given positions; a candidate's score is (benchmarks available, mean position),
    so a candidate missing a benchmark ranks after one that has it, with the gap stated in the note. Ties and the
    no-benchmark-available group are ordered by name, so the output is deterministic. `audit[name]` (from `artefact_flag`)
    puts a candidate after every unflagged one and states the reason in its note."""
    audit = audit or {}
    names = list(cells)
    pos: dict[str, dict[str, int]] = {n: {} for n in names}
    dies: dict[str, list[str]] = {n: [] for n in names}
    for bid in bids:
        have = []
        for n in names:
            v, bad = bench_value(cells[n].get(bid))
            if v is not None:
                have.append((bad, v, n))
                if bad:
                    dies[n].append(bid)
        for i, (_, _, n) in enumerate(sorted(have), 1):
            pos[n][bid] = i
    def key(n: str):
        p = pos[n]
        return (n in audit, -len(p), (sum(p.values()) / len(p)) if p else 0.0, n)
    out = []
    for n in sorted(names, key=key):
        missing = [b for b in bids if b not in pos[n]]
        note = []
        if missing:
            note.append("no value for " + ", ".join(missing))
        if dies[n]:
            note.append("survival check FAILED on " + ", ".join(dies[n]))
        if n in audit:
            note.append(audit[n])
        out.append((n, "; ".join(note)))
    return out


def _audit(tier_runs: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
    return {n: f for n, tr in tier_runs.items() if (f := artefact_flag(tr.get("stats"), tr.get("bench")))}


def best_run(res: RunResult | dict, tier: str) -> dict | None:
    """Highest-objective completed tier run at `tier` across seeds (axis variants): {variant, supports, tier_run}."""
    d = res if isinstance(res, dict) else res.to_dict()
    best = None
    for s in d["seeds"]:
        tr = s["tiers"].get(tier)
        if tr and tr["ok"] and tr["value"] is not None and (best is None or tr["value"] > best["tier_run"]["value"]):
            best = {"variant": s["variant"], "supports": s["supports"], "tier_run": tr}
    return best


def screen_tier_for(brief: Mapping[str, Any], cfg: Mapping[str, Any]) -> str:
    """The configured screen tier, or the brief's highest tier when that is lower. Tier order = tiers.yaml order."""
    from pos_tiers.tiers import TierTable
    order = TierTable.load().tier_names
    want = cfg["run"]["screen_tier"]
    asked = [t for t in brief.get("tiers", []) if t in order]
    if not asked:
        return want
    top = max(asked, key=order.index)
    return top if order.index(top) < order.index(want) else want


# ---- preflight --------------------------------------------------------------------------------------------
@dataclass
class SlateEstimate:
    candidates: int
    deepened: int
    wall_seconds: float
    max_wall_seconds: float
    by_stage: dict[str, float]
    sources: list[str]

    @property
    def over_cap(self) -> bool:
        return self.wall_seconds > self.max_wall_seconds

    def summary(self) -> str:
        parts = ", ".join(f"{k} {v / 60:.1f} min" for k, v in self.by_stage.items())
        return (f"{self.candidates} candidate(s) screened, top {self.deepened} deepened: ~{self.wall_seconds / 60:.1f} min wall "
                f"({parts}); cap {self.max_wall_seconds / 60:.0f} min{' EXCEEDED' if self.over_cap else ''}")


def estimate_slate(cands: Sequence[Candidate], brief: Mapping[str, Any], slots: Mapping[str, int], workers: int, *,
                   max_minutes: float, k: int | None = None, cfg: Mapping[str, Any] | None = None,
                   rates: Mapping[str, Any] | None = None) -> SlateEstimate:
    """Per candidate: screen (1 tier, cheap gear, one tree cap) + ablation of its key pieces; plus the full run for the
    K most expensive candidates (the top K are not known in advance, so this is an upper bound). `slots[name]` = number
    of searched slots. Rates from data/rates.yaml, assumptions labelled there."""
    cfg = cfg or data.ideation()
    r = rates or load_rates()
    k = cfg["run"]["deepen_k"] if k is None else k
    scr_rates = {**r, "tree": {**r["tree"], "core_s_per_seed": r["tree_screen"]["core_s_per_seed"]}}
    w = max(1, workers)
    screen = abl = 0.0
    deep: list[float] = []
    n_tiers = max(1, len(brief.get("tiers", [])))
    for c in cands:
        nseeds = len(variants(c.spec)) if c.spec else 1
        n = slots.get(c.name, 1)
        screen += estimate(nseeds, 1, n, w, realloc_rounds=cfg["run"]["screen_realloc_rounds"], max_minutes=max_minutes,
                           rates=scr_rates).wall_seconds
        core = 0.0
        for p in c.key_pieces:
            kind = {"unique": "unique", "support": "support"}.get(p["kind"], "tree_node")
            core += r["ablation"][kind]["core_s"]
        abl += core / w
        deep.append(estimate(nseeds, n_tiers, n, w, max_minutes=max_minutes, rates=r).wall_seconds)
    deep_total = sum(sorted(deep, reverse=True)[:k])
    by = {"screen": screen, "ablation": abl, "deepen": deep_total}
    src = [f"{key}: {r[key]['source']}" for key in ("tree_screen",)] + [f"ablation.{kk}: {v['source']}" for kk, v in r["ablation"].items()]
    return SlateEstimate(len(cands), min(k, len(cands)), sum(by.values()), max_minutes * 60, by, src)


# ---- the loop ---------------------------------------------------------------------------------------------
def run_slate(slate: Slate, rep: SlateReport, runner: CandidateRunner, *, k: int | None = None, cfg: Mapping[str, Any] | None = None,
              out_dir: str | Path | None = None, estimate_text: str = "", log: Callable[[str], None] = lambda s: None) -> SlateRun:
    cfg = cfg or data.ideation()
    if not rep.ok:
        raise ValueError("slate did not validate (no kept candidate or a slate-level error); run `slate validate` first")
    bids = list(slate.brief.get("benchmarks", []))
    if not bids:
        raise ValueError("brief.benchmarks is empty: cross-archetype ranking is defined on benchmark metrics only")
    k = cfg["run"]["deepen_k"] if k is None else k
    tier = screen_tier_for(slate.brief, cfg)
    by_name = {c.name: c for c in slate.candidates}
    kept = [(by_name[r.name], r) for r in rep.kept]
    out = SlateRun(slate.prompt, dict(slate.brief), tier, k, [], estimate=estimate_text)
    out.rejected = [{"name": r.name, "codes": sorted({i.code for i in r.errors})} for r in rep.candidates if not r.kept]
    runs: dict[str, CandidateRun] = {}
    for c, r in kept:
        cr = CandidateRun(c.name, c.source, dict(r.vector), [asdict(cl) for cl in c.claims], list(c.key_pieces))
        cr.conditions = list(c.spec.conditions) if c.spec else []
        out.candidates.append(cr)
        runs[c.name] = cr
        try:
            res, abl = runner.screen(c, tier)
        except Exception as ex:   # one bad candidate must not sink the slate
            cr.status, cr.error = "failed", f"{type(ex).__name__}: {ex}"
            log(f"screen {c.name}: FAILED {cr.error}")
            continue
        cr.screen = best_run(res, tier)
        cr.ablations = [asdict(a) for a in abl]
        if cr.screen is None:
            cr.status = "failed"
            cr.error = "; ".join(filter(None, [s.error for s in res.seeds])) or f"no completed run at tier {tier}"
            log(f"screen {c.name}: FAILED {cr.error}")
            continue
        cr.status = "screened"
        log(f"screen {c.name}: done")

    ok = [c for c in out.candidates if c.status == "screened"]
    order = rank_by_benchmarks({c.name: c.screen["tier_run"].get("bench") or {} for c in ok}, bids,
                               _audit({c.name: c.screen["tier_run"] for c in ok}))
    for n, (name, note) in enumerate(order, 1):
        runs[name].screen_rank, runs[name].rank_note = n, note
    top = [name for name, _ in order[:k]]
    if len(ok) > k:
        out.notes.append(f"successive halving: top {k} of {len(ok)} by screen rank deepened; the rest keep their screen numbers")
    for name in top:
        cr = runs[name]
        try:
            res = runner.deepen(by_name[name])
        except Exception as ex:
            cr.deepen_error = f"{type(ex).__name__}: {ex}"
            log(f"deepen {name}: FAILED {cr.deepen_error}")
            continue
        tiers = list(slate.brief.get("tiers") or [tier])
        cr.deep = {t: b for t in tiers if (b := best_run(res, t))}
        log(f"deepen {name}: done")
    for t in slate.brief.get("tiers") or [tier]:
        runs_t = {c.name: c.deep[t]["tier_run"] for c in out.candidates if c.deep and t in c.deep}
        have = {n: r.get("bench") or {} for n, r in runs_t.items()}
        for n, (name, _) in enumerate(rank_by_benchmarks(have, bids, _audit(runs_t)), 1):
            runs[name].deep_rank[t] = n
    out.notes.append("ranking basis: benchmark metrics only (boss time-to-kill with its survival check, pack clear proxy); a candidate "
                     "missing a benchmark value ranks after those that have it. Per-skill DPS is shown but never ranks across archetypes.")
    out.notes.append("ablation measures the objective metric under the first benchmark's PoB options, not time-to-kill, and also TotalEHP: a piece is confirmed when removal costs either at least the threshold; "
                     "a unique key piece is replaced by the best rare for its slot at the screen tier.")
    if out_dir:
        d = Path(out_dir)
        d.mkdir(parents=True, exist_ok=True)
        (d / "slate_run.json").write_text(json.dumps(out.to_dict(), indent=1, default=str), encoding="utf-8")
        write_slate_report(out.to_dict(), d)
    return out


# ---- real runner ------------------------------------------------------------------------------------------
def unique_slot(xml: str, name: str) -> str | None:
    """Search-slot key (`weapon`, `ring_1`, ...) whose equipped item text contains the unique `name`, or None."""
    from .gear import SLOTS
    inv = {v: k for k, v in SLOTS.items()}
    root = ET.fromstring(xml)
    text = {it.get("id"): (it.text or "") for it in root.iter("Item")}
    want = re.sub(r"\s+", " ", name).strip().lower()
    for sl in root.iter("Slot"):
        key = inv.get(sl.get("name", ""))
        if key and sl.get("itemId") in text and want in re.sub(r"\s+", " ", text[sl.get("itemId")]).lower():
            return key
    return None


class EngineRunner:
    """`CandidateRunner` over the real stages. One engine + pool per candidate run; the result cache is shared through
    `cache` (keyed on build + mutations, so reuse across candidates and tiers is safe)."""

    def __init__(self, cat: Catalogue, slate: Slate, default_bases: Mapping[str, str], *, workers: int, cache: str | None = None,
                 cfg: Mapping[str, Any] | None = None, log: Callable[[str], None] = lambda s: None):
        self.cat, self.slate, self.defaults, self.workers, self.cache = cat, slate, dict(default_bases), workers, cache
        self.cfg, self.log = cfg or data.ideation(), log

    def bases_of(self, c: Candidate) -> dict[str, str]:
        return {**self.defaults, **c.bases}

    def _go(self, c: Candidate, tiers: list[str], realloc: int, caps: Sequence[int] | None):
        from .gear import STANDARD_FLOORS
        from .orchestrate import engine_stages, run
        from .validate import validate
        spec = replace(c.spec, tiers=tiers, benchmarks=list(self.slate.brief.get("benchmarks", [])))
        rep = validate(spec, self.cat)
        if not rep.ok:
            raise ValueError("spec no longer validates: " + "; ".join(i.message for i in rep.errors))
        bases = self.bases_of(c)
        if not bases:
            raise ValueError("no bases for the gear search: give `bases:` on the candidate or slot=Base on the command line")
        floors = {**(STANDARD_FLOORS if spec.floors.get("resist_capped") else {}), **(self.slate.brief.get("floors") or {})}
        meta = {"metric_note": rep.metric_note}
        with engine_stages(spec, self.cat, rep, bases, workers=self.workers, cache=self.cache, realloc_rounds=realloc,
                           floors=floors, tree_caps=caps) as (st, skill_of):
            res = run(spec, st, metric=rep.metric, slots=len(bases), workers=self.workers, skill_id=skill_of, realloc_rounds=realloc,
                      force=True, benchmarks=spec.benchmarks, meta=meta, log=self.log)
            return res, rep, skill_of, floors

    def screen(self, c: Candidate, tier: str) -> tuple[RunResult, list[Ablation]]:
        res, rep, skill_id, floors = self._go(c, [tier], self.cfg["run"]["screen_realloc_rounds"], self.cfg["run"]["screen_tree_caps"])
        best = None
        for s in res.seeds:
            tr = s.tiers.get(tier)
            if tr and tr.ok and tr.value is not None and (best is None or tr.value > best[1].value):
                best = (s, tr)
        if best is None:
            return res, []
        return res, self._ablate(c, tier, best[1].xml, best[0].supports, rep.metric, skill_id(best[0].variant), floors)

    def deepen(self, c: Candidate) -> RunResult:
        tiers = list(self.slate.brief.get("tiers") or [self.cfg["run"]["screen_tier"]])
        return self._go(c, tiers, DEFAULT_REALLOC_ROUNDS, None)[0]

    def _ablate(self, c: Candidate, tier: str, xml: str, supports: Sequence[str], metric: str, skill_id: str, floors) -> list[Ablation]:
        from pos_engine.engine import PobEngine
        from pos_pool.pool import EnginePool
        from .benchmarks import benchmarks as _bms, pob_options
        from .gear import GearSearcher
        from .sweep import ablate
        bms = _bms()
        bid = next((b for b in self.slate.brief.get("benchmarks", []) if bms[b]["kind"] == "boss"), (self.slate.brief.get("benchmarks") or [None])[0])
        options = pob_options(bms[bid]) if bid else None
        pieces = [{"kind": p["kind"], "id": p["id"]} for p in c.key_pieces if p["kind"] in PIECE_KINDS]
        with PobEngine() as eng, EnginePool(workers=self.workers, cache=self.cache) as pool:
            searcher = GearSearcher(self.cat, pool, eng, metric=metric, floors=floors)
            replace_unique = make_rare_replacer(self.cat, searcher, tier)
            return ablate(self.cat, pool, xml, pieces, metric, options=options, skill_id=skill_id, supports=list(supports),
                          threshold=self.cfg["run"]["ablation_threshold"], engine=eng, replace_unique=replace_unique)


def make_rare_replacer(cat: Catalogue, searcher, tier: str):
    """`replace_unique(xml, piece) -> (xml with the best rare in the unique's slot, label)` for `sweep.ablate`.
    The rare is the gear search's best item for that slot on the unique's own base within the tier's slot budget, uniques
    excluded. Raises ValueError (-> `not_testable`) when the unique is not in the final build, e.g. because the gear
    search overwrote its slot. If the rare search itself fails, the slot is emptied instead (an upper bound, labelled)."""
    def replace_unique(xml: str, piece: Mapping[str, Any]) -> tuple[str, str]:
        e = cat.resolve("unique", piece["id"]).entry
        if not e:
            raise ValueError(f"unique {piece['id']!r} not in catalogue")
        slot = unique_slot(xml, e["name"])
        if slot is None:
            raise ValueError(f"unique {e['name']!r} is not equipped in the final build (the gear search replaced its slot, "
                             "or it never equipped); nothing to ablate")
        try:
            chosen, _ = searcher.best_item(xml, slot, e["base"], searcher.slot_budget(tier, slot),
                                           exclude_uniques=[*searcher.uniques, e["name"]])
            what = ", ".join(f"{a.group} r{a.rank}" for a in chosen.affixes) or "unmodded base"
            return searcher.equip(xml, slot, chosen.raw), f"best rare at {tier} [{e['base']}]: {what}"
        except Exception as ex:   # base without mods, engine refusal: fall back to the upper bound, say so
            searcher.eng.load_build_xml(xml)
            from .gear import SLOTS
            if not searcher.eng.unequip_item(SLOTS[slot]).get("ok"):
                raise
            return searcher.eng.get_xml(), f"(slot emptied: best-rare search failed: {type(ex).__name__}: {ex}; verdict is an upper bound)"
    return replace_unique


# ---- report -----------------------------------------------------------------------------------------------
def _arch(v: Mapping[str, str]) -> str:
    return f"{v.get('class_asc', '')} / {v.get('delivery', '')} / {v.get('damage', '')} / {v.get('defence', '')}"


def _verdicts(c: Mapping[str, Any]) -> str:
    if not c["ablations"]:
        return "n/a"
    return ", ".join(f"{a['piece']['id']}: {a['verdict']}" for a in c["ablations"])


def render_slate_markdown(d: dict) -> str:
    bids = list(d["brief"].get("benchmarks", []))
    cands = d["candidates"]
    L: list[str] = []
    a = L.append
    a("# Slate report")
    a("")
    a(f"- Prompt: {d['prompt']}")
    a(f"- Benchmarks: {', '.join(bids)}. Brief tiers: {', '.join(d['brief'].get('tiers', []))}. Screen tier: `{d['screen_tier']}`. Deepened: top {d['deepen_k']}.")
    if d.get("estimate"):
        a(f"- Preflight estimate: {d['estimate']}")
    for n in d["notes"]:
        a(f"- {n}")
    a("- Numbers are PoB outputs or benchmark formulas over them (`proxy` = density proxy, `ASSUMPTION` = owner-tunable constant). "
      "Mechanism claims are quoted from catalogue text; ablation tests whether they matter.")
    a("")
    a("## Screen ranking")
    a("")
    a("| # | candidate | source | archetype | " + " | ".join(bids) + " | price | key pieces (ablation) | deepened |")
    a("|---|---|---|---|" + "---|" * len(bids) + "---|---|---|")
    for c in sorted((c for c in cands if c["screen_rank"]), key=lambda c: c["screen_rank"]):
        tr = c["screen"]["tier_run"]
        price = "n/a" if not tr.get("price") else tr["price"] if tr["price"].startswith("no price") else f"~{tr['price']}"
        row = [str(c["screen_rank"]), c["name"], c["source"], _arch(c["vector"])]
        row += [_bench_cell((tr.get("bench") or {}).get(b)) for b in bids]
        row += [price, _verdicts(c), "yes" if c["deep"] is not None else "no"]
        a("| " + " | ".join(row) + " |")
    a("")
    for c in cands:
        if c["rank_note"] and c["screen_rank"]:
            a(f"- {c['name']}: {c['rank_note']}")
    a("")
    for t in d["brief"].get("tiers", []):
        rows = sorted((c for c in cands if c["deep_rank"].get(t)), key=lambda c: c["deep_rank"][t])
        if not rows:
            continue
        a(f"## Full run, tier `{t}`")
        a("")
        a("| # | candidate | " + " | ".join(bids) + " | EHP | price | floors |")
        a("|---|---|" + "---|" * len(bids) + "---:|---|---|")
        for c in rows:
            tr = c["deep"][t]["tier_run"]
            st = tr.get("stats") or {}
            price = "n/a" if not tr.get("price") else tr["price"] if tr["price"].startswith("no price") else f"~{tr['price']}"
            a("| " + " | ".join([str(c["deep_rank"][t]), c["name"], *[_bench_cell((tr.get("bench") or {}).get(b)) for b in bids],
                                 _num(st.get("TotalEHP")), price, {True: "met", False: "NOT met", None: "n/a"}[tr.get("floors_met")]]) + " |")
        a("")
    a("## Candidates")
    a("")
    for c in sorted(cands, key=lambda c: (c["screen_rank"] is None, c["screen_rank"] or 0, c["name"])):
        a(f"### {c['name']}")
        a("")
        if c["status"] == "failed":
            a(f"Screen FAILED: {c['error']}")
            a("")
            continue
        a(f"Source: `{c['source']}`. Archetype: {_arch(c['vector'])}. Main skill: {c['vector'].get('main_skill')}.")
        if c.get("conditions"):
            from . import data as _d
            tab = _d.conditions()
            a("Measured under declared conditions (assumed, not earned by the build): "
              + "; ".join(f"{n} ({tab[n]['description']}; needs {tab[n]['needs']})" if n in tab else n for n in c["conditions"]) + ".")
        if c["deepen_error"]:
            a(f"Full run FAILED: {c['deepen_error']}")
        a("")
        for cl in c["claims"]:
            a(f"- Claim: {cl['text']}")
            for ct in cl["cites"]:
                a(f"  - {ct['kind']} {ct['id']}: \"{ct['quote']}\"")
        a("")
        if c["ablations"]:
            a("| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |")
            a("|---|---|---:|---:|---|---|")
            for ab in c["ablations"]:
                w = "n/a" if ab["delta_rel"] is None else f"{ab['delta_rel']:+.1%}"
                we = "n/a" if ab.get("ehp_delta_rel") is None else f"{ab['ehp_delta_rel']:+.1%}"
                a(f"| {ab['piece']['kind']}: {ab['piece']['id']} | {ab['verdict']} | {w} | {we} | {ab['replacement'] or ''} | {ab['note']} |")
            a("")
    if d["rejected"]:
        a("## Dropped by the gate")
        a("")
        for r in d["rejected"]:
            a(f"- {r['name']}: {', '.join(r['codes'])}")
        a("")
    a("## Across the slate")
    a("")
    winners = [(t, min((c for c in cands if c["deep_rank"].get(t) == 1), key=lambda c: c["name"], default=None)) for t in d["brief"].get("tiers", [])]
    for t, c in winners:
        if c:
            a(f"- Tier `{t}`: {c['name']} ({_arch(c['vector'])}, source `{c['source']}`).")
    srcs = sorted({c["source"].split(":")[0] for c in cands if c["status"] == "screened"})
    a(f"- Generators represented among screened candidates: {', '.join(srcs) or 'none'}.")
    conf = sum(ab["verdict"] == "confirmed" for c in cands for ab in c["ablations"])
    tot = sum(1 for c in cands for ab in c["ablations"])
    a(f"- Ablation: {conf} of {tot} key pieces confirmed (removal costs at least the configured share of the metric).")
    a("")
    return "\n".join(L)


SCHEMA = """
CREATE TABLE candidates(name TEXT PRIMARY KEY, source TEXT, status TEXT, screen_rank INTEGER, rank_note TEXT, vector TEXT, error TEXT, screen TEXT, deep TEXT);
CREATE TABLE ablations(candidate TEXT, kind TEXT, piece TEXT, verdict TEXT, delta_rel REAL, baseline REAL, without REAL, replacement TEXT, note TEXT, ehp_delta_rel REAL);
CREATE TABLE deep_rank(candidate TEXT, tier TEXT, rank INTEGER);
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
"""


def write_slate_sqlite(d: dict, path: Path) -> None:
    path.unlink(missing_ok=True)
    j = lambda x: json.dumps(x, sort_keys=True, default=str)  # noqa: E731
    with sqlite3.connect(path) as c:
        c.executescript(SCHEMA)
        c.executemany("INSERT INTO meta VALUES(?,?)", [("prompt", d["prompt"]), ("brief", j(d["brief"])), ("screen_tier", d["screen_tier"]),
                                                       ("deepen_k", str(d["deepen_k"])), ("estimate", d.get("estimate", ""))])
        for cr in d["candidates"]:
            c.execute("INSERT INTO candidates VALUES(?,?,?,?,?,?,?,?,?)", (cr["name"], cr["source"], cr["status"], cr["screen_rank"], cr["rank_note"],
                                                                          j(cr["vector"]), cr["error"], j(cr["screen"]), j(cr["deep"])))
            for ab in cr["ablations"]:
                c.execute("INSERT INTO ablations VALUES(?,?,?,?,?,?,?,?,?,?)", (cr["name"], ab["piece"]["kind"], ab["piece"]["id"], ab["verdict"],
                                                                              ab["delta_rel"], ab["baseline"], ab["without"], ab["replacement"], ab["note"],
                                                                              ab.get("ehp_delta_rel")))
            for t, rk in cr["deep_rank"].items():
                c.execute("INSERT INTO deep_rank VALUES(?,?,?)", (cr["name"], t, rk))


def write_slate_report(d: dict, out_dir: Path | str) -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    md, db = out / "slate_report.md", out / "slate_results.sqlite"
    md.write_text(render_slate_markdown(d), encoding="utf-8")
    write_slate_sqlite(d, db)
    return md, db
