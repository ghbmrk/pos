"""`python -m pos_pipeline validate spec.yaml` — prints issues, exits 1 on errors."""
import sys

from pos_catalogue import Catalogue

from . import SpecError, data, load_spec, validate


def _print_issues(issues) -> None:
    for i in issues:
        tag = f"{i.severity}[{i.code}{'/' + i.confidence if i.confidence else ''}]"
        print(f"{tag} {i.path}: {i.message}" + (f"  suggestions: {', '.join(i.suggestions)}" if i.suggestions else ""))


def _slate(argv: list[str]) -> int:
    from . import slate as sl

    if argv and argv[0] == "run":
        return _slate_run(argv[1:])
    if len(argv) != 2 or argv[0] != "validate":
        print("usage: python -m pos_pipeline slate validate slate.yaml | slate run slate.yaml [slot=Base ...] [--preflight] [--workers N] [--max-minutes M] [--force] [--deepen-k K] [--out DIR]")
        return 2
    try:
        s = sl.load_slate(argv[1])
    except SpecError as e:
        print(f"error: {e}")
        return 1
    rep = sl.validate_slate(s, Catalogue.load(pob_sha=s.pob_sha))
    _print_issues(rep.issues)
    for r in rep.candidates:
        print(f"{'KEPT    ' if r.kept else 'REJECTED'} {r.name}" + (f"  [{r.vector['delivery']}/{r.vector['damage']}, metric {r.metric}]" if r.vector else ""))
        _print_issues(r.issues)
    print(f"{len(rep.kept)} of {len(rep.candidates)} kept; " + ("OK" if rep.ok else "slate NOT ok"))
    return 0 if rep.ok else 1


def _play(argv: list[str]) -> int:
    """`play "PROMPT" --slate slate.yaml [slot=Base ...]`: screen the ideas, improve rounds, deepen finalists, player report (docs/play.md)."""
    import argparse
    import os
    from pathlib import Path

    from . import slate as sl
    from .gear import SLOTS
    from .orchestrate import DEFAULT_MAX_MINUTES
    from .play import PlayRunner, play, play_estimate, render_play_markdown

    ap = argparse.ArgumentParser(prog="python -m pos_pipeline play")
    ap.add_argument("prompt", help="the player's high-level prompt (recorded in the report; the ideas come from --slate)")
    ap.add_argument("bases", nargs="*", help="default slot=Base for ideas that give no `bases:` of their own")
    ap.add_argument("--slate", required=True, help="ideas the LLM client wrote from the prompt (ideation_guide / prompt `ideate`); the server has no embedded LLM")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--k", type=int, default=3, help="finalists improved and deepened")
    ap.add_argument("--outer-rounds", type=int, default=2, help="creative improvement rounds (sweep-proposed, sim-verified)")
    ap.add_argument("--children", type=int, default=1, help="changes proposed per finalist per round")
    ap.add_argument("--inner-rounds", type=int, default=3, help="L3 numeric loop rounds on each finalist (dead-move skipping on; --direct stays off)")
    ap.add_argument("--max-minutes", type=float, default=DEFAULT_MAX_MINUTES, help="refuse above this estimate unless --force; also stops the creative rounds")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--preflight", action="store_true")
    ap.add_argument("--assumed", action="store_true", help="allow specs with companion.assumed (the labelled Squire what-if)")
    ap.add_argument("--assume", action="append", default=[], help="a line for the report's ASSUMED banner (stand-ins, assumed actors); repeatable")
    ap.add_argument("--meta", default=None, help="PoB build XML of a meta build, benchmarked under the same conditions as a comparison row")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    bases = dict(x.split("=", 1) for x in a.bases if "=" in x)
    if "ring" in bases:
        bases.setdefault("ring_1", bases["ring"]); bases.setdefault("ring_2", bases.pop("ring"))
    bad = [x for x in bases if x not in SLOTS]
    if bad:
        print(f"unknown slot(s): {', '.join(bad)}; known: {', '.join(SLOTS)}"); return 2
    try:
        s = sl.load_slate(a.slate)
    except SpecError as e:
        print(f"error: {e}"); return 1
    cat = Catalogue.load(pob_sha=s.pob_sha)
    rep = sl.validate_slate(s, cat)
    _print_issues(rep.issues)
    for r in rep.candidates:
        if not r.kept:
            print(f"REJECTED {r.name}"); _print_issues(r.errors)
    if not rep.ok:
        print("slate NOT ok; not running"); return 1
    s.prompt = a.prompt or s.prompt
    by = {c.name: c for c in s.candidates}
    kept = [by[r.name] for r in rep.kept]
    est = play_estimate(kept, s.brief, bases, a.workers, k=a.k, outer_rounds=a.outer_rounds, children=a.children, inner_rounds=a.inner_rounds, max_minutes=a.max_minutes)
    print(est.summary())
    if a.preflight:
        return 1 if est.over_cap else 0
    if est.over_cap and not a.force:
        print("refused: estimate above the cap; pass --force or raise --max-minutes"); return 3
    Path(a.out).mkdir(parents=True, exist_ok=True)
    runner = PlayRunner(cat, s, bases, workers=a.workers, cache=str(Path(a.out) / "cache.sqlite"), log=print, rounds=a.inner_rounds)
    runner.allow_assumed = a.assumed
    r = play(s, rep, runner, k=a.k, outer_rounds=a.outer_rounds, children=a.children, max_minutes=a.max_minutes, out_dir=a.out, estimate_text=est.summary(), log=print)
    if a.meta:
        w = next((x for x in r["finalists"] if x.get("core")), None)
        if w:
            mb = runner.bench_xml(Path(a.meta).read_text(), next(c for c in kept if c.name == w["name"]))
            r["meta"] = "Meta build (" + Path(a.meta).name + "): " + "; ".join(f"{b}: " + (str(v.get("ttk_s") or v.get("clear_s") or v.get("error") or v)) for b, v in mb.items())
    assumed_lines = list(a.assume)
    (Path(a.out) / "report.md").write_text(render_play_markdown(r, assumed_lines), encoding="utf-8")
    (Path(a.out) / "play.json").write_text(__import__("json").dumps(r, indent=1, default=str), encoding="utf-8")
    print((Path(a.out) / "report.md").read_text(encoding="utf-8")[:1500])
    return 0


def _slate_run(argv: list[str]) -> int:
    import argparse
    import os
    from pathlib import Path

    from . import slate as sl
    from .gear import SLOTS
    from .orchestrate import DEFAULT_MAX_MINUTES
    from .slate_run import EngineRunner, estimate_slate, run_slate

    ap = argparse.ArgumentParser(prog="python -m pos_pipeline slate run")
    ap.add_argument("slate")
    ap.add_argument("bases", nargs="*", help="default slot=Base for candidates that give no `bases:` of their own")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--max-minutes", type=float, default=DEFAULT_MAX_MINUTES, help="refuse above this estimate unless --force")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--preflight", action="store_true", help="print the cost estimate and exit")
    ap.add_argument("--deepen-k", type=int, default=None)
    ap.add_argument("--out", default=None, help="directory for slate_run.json, slate_report.md, slate_results.sqlite, cache.sqlite")
    ap.add_argument("--no-objective", action="store_true", help="search on the bare metric instead of the benchmark objective (L1 baseline)")
    ap.add_argument("--hard-ttk", action="store_true", help="the benchmark TTK gate is a hard constraint in the search objective")
    a = ap.parse_args(argv)
    bases = dict(x.split("=", 1) for x in a.bases if "=" in x)
    if "ring" in bases:
        bases.setdefault("ring_1", bases["ring"]); bases.setdefault("ring_2", bases.pop("ring"))
    bad = [s for s in bases if s not in SLOTS]
    if bad:
        print(f"unknown slot(s): {', '.join(bad)}; known: {', '.join(SLOTS)}"); return 2
    try:
        s = sl.load_slate(a.slate)
    except SpecError as e:
        print(f"error: {e}"); return 1
    cat = Catalogue.load(pob_sha=s.pob_sha)
    rep = sl.validate_slate(s, cat)
    _print_issues(rep.issues)
    for r in rep.candidates:
        if not r.kept:
            print(f"REJECTED {r.name}"); _print_issues(r.errors)
    if not rep.ok:
        print("slate NOT ok; not running"); return 1
    by = {c.name: c for c in s.candidates}
    kept = [by[r.name] for r in rep.kept]
    slots = {c.name: len({**bases, **c.bases}) for c in kept}
    for n, v in slots.items():
        if not v:
            print(f"note: {n} has no bases: no gear is searched (unarmed / bare build)")
    est = estimate_slate(kept, s.brief, {n: v or 1 for n, v in slots.items()}, a.workers, max_minutes=a.max_minutes, k=a.deepen_k)
    print(est.summary())
    if a.preflight:
        for src in est.sources:
            print("  rate:", src)
        return 1 if est.over_cap else 0
    if est.over_cap and not a.force:
        print("refused: estimate above the cap; pass --force or raise --max-minutes"); return 3
    cache = str(Path(a.out) / "cache.sqlite") if a.out else None
    if a.out:
        Path(a.out).mkdir(parents=True, exist_ok=True)
    runner = EngineRunner(cat, s, bases, workers=a.workers, cache=cache, log=print)
    r = run_slate(s, rep, runner, k=a.deepen_k, out_dir=a.out, estimate_text=est.summary(), log=print)
    for c in sorted((c for c in r.candidates if c.screen_rank), key=lambda c: c.screen_rank):
        print(f"{c.screen_rank}. {c.name}" + (f"  ({c.rank_note})" if c.rank_note else ""))
    for c in r.candidates:
        if c.status == "failed":
            print(f"FAILED {c.name}: {c.error}")
    return 0


def _assemble(path: str, out_dir: str | None) -> int:
    from pathlib import Path

    from pos_engine.engine import PobEngine

    from .assemble import assemble, variants

    spec = load_spec(path)
    cat = Catalogue.load(pob_sha=spec.pob_sha)
    rep = validate(spec, cat)
    _print_issues(rep.issues)
    if not rep.ok:
        print(f"{len(rep.errors)} validation error(s); not assembling")
        return 1
    bad = 0
    with PobEngine() as eng:
        for n, v in enumerate(variants(spec)):
            a = assemble(spec, cat, eng, v)
            print(f"variant {v or '(none)'}: {'OK' if a.ok else 'FAILED'}; main skill {a.main_skill}; "
                  f"TotalDPS {a.stats.get('TotalDPS')}" + (f"; deferred to gear stage: {a.deferred_axes}" if a.deferred_axes else ""))
            _print_issues(a.issues)
            bad += not a.ok
            if a.ok and out_dir:
                Path(out_dir).mkdir(parents=True, exist_ok=True)
                (Path(out_dir) / f"seed_{n}.xml").write_text(a.xml, encoding="utf-8")
    return 1 if bad else 0


def _supports(path: str, workers: int) -> int:
    from pos_engine.engine import PobEngine
    from pos_pool.pool import EnginePool

    from .assemble import assemble, variants
    from .supports import search_supports

    spec = load_spec(path)
    cat = Catalogue.load(pob_sha=spec.pob_sha)
    rep = validate(spec, cat)
    _print_issues(rep.issues)
    if not rep.ok:
        print(f"{len(rep.errors)} validation error(s); not searching")
        return 1
    allow = [cat.resolve("support", n).entry["id"] for n in data.profiles()[spec.config_profile].get("allow_triggered") or []]
    with PobEngine() as eng, EnginePool(workers=workers) as pool:
        for v in variants(spec):
            a = assemble(spec, cat, eng, v)
            if not a.ok:
                print(f"variant {v or '(none)'}: seed FAILED"); _print_issues(a.issues)
                continue
            skill = cat.resolve("skill", v.get("main_skill", spec.main_skill)).entry
            fixed = [cat.resolve("support", s).entry["id"] for s in spec.supports]
            r = search_supports(cat, pool, a.xml, skill["id"], fixed, rep.metric, allow_triggered=allow)
            names = lambda ids: ", ".join(cat.get("support", i)["name"] for i in ids) or "(none)"  # noqa: E731
            print(f"variant {v or '(none)'}: {r.metric} {r.baseline.value:.1f} -> {r.best.value:.1f} ({r.gain:+.1%}); "
                  f"supports: {names(r.best.supports)}; {r.evals} evals ({r.cached} cached, {r.failures} failed)")
            for n in r.notes:
                print("  note:", n)
    return 0


def _tree(path: str, workers: int, candidates: int) -> int:
    from pos_engine.engine import PobEngine

    from .assemble import assemble, variants
    from .tree import DEFAULT_CAPS, search_trees

    spec = load_spec(path)
    cat = Catalogue.load(pob_sha=spec.pob_sha)
    rep = validate(spec, cat)
    _print_issues(rep.issues)
    if not rep.ok:
        print(f"{len(rep.errors)} validation error(s); not searching")
        return 1
    seeds = []
    with PobEngine() as eng:
        for v in variants(spec):
            a = assemble(spec, cat, eng, v)
            if a.ok:
                seeds.append((v, a.xml))
            else:
                print(f"variant {v or '(none)'}: seed FAILED"); _print_issues(a.issues)
    require = list(spec.keystones) + list(spec.notables)
    out = search_trees([x for _, x in seeds], rep.metric, workers=workers, require=require,
                       **({"candidates": candidates} if candidates else {"caps": DEFAULT_CAPS}))
    bad = 0
    for (v, _), r in zip(seeds, out):
        if not r.ok:
            print(f"variant {v or '(none)'}: FAILED {r.error}"); bad += 1; continue
        print(f"variant {v or '(none)'}: {r.metric} {r.start:.1f} -> {r.final:.1f} ({r.gain:+.0%}); {len(r.allocated)} picks, "
              f"{r.points_used} points used, {r.points_remaining} left; {r.seconds:.1f} s")
        for n in r.notes:
            print("  note:", n)
    return 1 if bad else 0


def _gear(path: str, tier: str, base_args: list[str], workers: int = 2) -> int:
    from pos_engine.engine import PobEngine
    from pos_pool.pool import EnginePool

    from .assemble import assemble, variants
    from .gear import SLOTS, search_gear

    bases = dict(a.split("=", 1) for a in base_args)
    if "ring" in bases:                       # one base for both rings
        bases.setdefault("ring_1", bases["ring"]); bases.setdefault("ring_2", bases.pop("ring"))
    spec = load_spec(path)
    cat = Catalogue.load(pob_sha=spec.pob_sha)
    rep = validate(spec, cat)
    _print_issues(rep.issues)
    if not rep.ok:
        print(f"{len(rep.errors)} validation error(s); not searching")
        return 1
    slots = tuple(s for s in SLOTS if s in bases)
    with PobEngine() as eng, EnginePool(workers=workers) as pool:
        for v in variants(spec):
            a = assemble(spec, cat, eng, v)
            if not a.ok:
                print(f"variant {v or '(none)'}: seed FAILED"); _print_issues(a.issues)
                continue
            r = search_gear(cat, pool, eng, a.xml, tier, bases, rep.metric, slots=slots)
            print(f"variant {v or '(none)'} tier {tier}: {r.metric} {r.baseline:.1f} -> {r.value:.1f}; "
                  f"{r.evals} evals ({r.cached} cached, {r.failures} failed); price: {r.price.label}")
            for s, it in r.items.items():
                what = it.unique or ", ".join(f"{x.group} r{x.rank}" for x in it.affixes) or "(no affixes)"
                print(f"  {s} [{it.base}] {it.points:g}/{r.slot_budgets[s] if r.slot_budgets[s] is not None else 'inf'} pts: {what}")
            for n in r.notes:
                print("  note:", n)
    return 0


def _import(path: str) -> int:
    from pathlib import Path

    import yaml

    from pos_engine.engine import PobEngine

    from .assemble import import_pob

    cat = Catalogue.load()
    with PobEngine() as eng:
        spec, issues = import_pob(Path(path).read_text(encoding="utf-8").strip(), cat, eng)
    _print_issues(issues)
    d = {"pob_sha": spec.pob_sha, "class": spec.class_, "ascendancy": spec.ascendancy, "level": spec.level,
         "main_skill": {"gem": spec.main_skill},
         "fixed": {"supports": spec.supports, "keystones": spec.keystones, "notables": spec.notables, "uniques": spec.uniques},
         "tiers": spec.tiers or ["mid"], "config_profile": spec.config_profile}
    print(yaml.safe_dump(d, sort_keys=False))
    return 0


def _run(argv: list[str]) -> int:
    import argparse
    import os

    from .gear import SLOTS
    from .orchestrate import (DEFAULT_MAX_MINUTES, DEFAULT_REALLOC_ROUNDS, AssumedNotAllowed, RunRefused, engine_stages,
                              gear_slot_count, run)

    ap = argparse.ArgumentParser(prog="python -m pos_pipeline run")
    ap.add_argument("spec")
    ap.add_argument("bases", nargs="*", help="slot=Base, e.g. weapon='Acrid Wand' (ring=Base sets both rings)")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--max-minutes", type=float, default=DEFAULT_MAX_MINUTES, help="refuse above this estimate unless --force")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--preflight", action="store_true", help="print the cost estimate and exit")
    ap.add_argument("--realloc-rounds", type=int, default=DEFAULT_REALLOC_ROUNDS, help="0 = cheap gear mode (about 2.3x faster, weaker)")
    ap.add_argument("--out", default=None, help="directory for run.json and cache.sqlite")
    ap.add_argument("--no-objective", action="store_true", help="search on the bare metric instead of the benchmark objective (L1 baseline)")
    ap.add_argument("--hard-ttk", action="store_true", help="treat the boss TTK gate as a hard constraint in the objective")
    ap.add_argument("--rounds", type=int, default=1, help="improvement rounds (L3): re-search supports, tree and gear from the geared build "
                    "until a round gains < --min-gain or this many rounds ran; 1 = single pass")
    ap.add_argument("--min-gain", type=float, default=0.01, help="stop the loop when a round gains less than this fraction of the objective")
    ap.add_argument("--loop-minutes", type=float, default=None, help="wall-clock budget per seed x tier for the loop")
    ap.add_argument("--direct", action="store_true", help="L4 diagnosis direction: per-round diagnosis skips advised-away stages and weights the tree (off by default: did not beat plain rounds on golden Spark, docs/loop.md 6.1)")
    ap.add_argument("--tree-warm", action="store_true", help="loop tree move keeps the current tree (reset=False) instead of re-planning it")
    ap.add_argument("--assumed", action="store_true", help="allow a spec with companion.assumed (ASSUMED Squire what-if, docs/squire-assumed.md)")
    a = ap.parse_args(argv)
    bases = dict(x.split("=", 1) for x in a.bases if "=" in x)
    if "ring" in bases:
        bases.setdefault("ring_1", bases["ring"]); bases.setdefault("ring_2", bases.pop("ring"))
    bad = [s for s in bases if s not in SLOTS]
    if bad:
        print(f"unknown slot(s): {', '.join(bad)}; known: {', '.join(SLOTS)}"); return 2
    spec = load_spec(a.spec)
    cat = Catalogue.load(pob_sha=spec.pob_sha)
    rep = validate(spec, cat)
    _print_issues(rep.issues)
    if not rep.ok:
        print(f"{len(rep.errors)} validation error(s); not running"); return 1
    if not bases and not a.preflight:
        print("no bases given (slot=Base ...): gear search needs one per slot"); return 2
    kw = dict(metric=rep.metric, slots=gear_slot_count(spec, bases), workers=a.workers, realloc_rounds=a.realloc_rounds,
              max_minutes=a.max_minutes, rounds=a.rounds, loop_minutes=a.loop_minutes, log=print)
    try:
        if a.preflight:
            r = run(spec, None, skill_id="", dry_run=True, force=True, **kw)  # type: ignore[arg-type]
            for src in r.estimate.sources:
                print("  rate:", src)
            return 1 if r.estimate.over_cap else 0
        from pathlib import Path
        cache = str(Path(a.out) / "cache.sqlite") if a.out else None
        if a.out:
            Path(a.out).mkdir(parents=True, exist_ok=True)
        meta = {"metric_note": rep.metric_note, "limitations": [f"[{i.confidence or i.severity}] {i.message}" for i in rep.issues if i.code == "limitation"]}
        with engine_stages(spec, cat, rep, bases, workers=a.workers, cache=cache, realloc_rounds=a.realloc_rounds,
                           objective=not a.no_objective, hard_ttk=a.hard_ttk, tree_reset=not a.tree_warm,
                           min_gain=a.min_gain, direct=a.direct) as (st, skill_of):
            r = run(spec, st, skill_id=skill_of, force=a.force, allow_assumed=a.assumed, out_dir=a.out, meta=meta, **kw)
    except RunRefused as e:
        print(f"refused: {e}"); return 3
    except AssumedNotAllowed as e:
        print(f"refused: {e}"); return 3
    for t, (v, val) in r.best_per_tier().items():
        print(f"tier {t}: best {r.metric} {val:.1f} with {v or '(no axes)'}")
    return 1 if any(not s.ok for s in r.seeds) else 0


def _sweep(path: str, kind: str, workers: int, top: int, pieces: list[str] | None = None, weapon: str | None = None) -> int:
    """`sweep spec.yaml KIND [workers] [top]` / `ablate spec.yaml kind:id ...` on the assembled (unsearched) seed."""
    from pos_engine.engine import PobEngine
    from pos_pool.pool import EnginePool

    from .assemble import assemble, variants
    from .sweep import ablate, equip_probe_weapon, sweep

    spec = load_spec(path)
    cat = Catalogue.load(pob_sha=spec.pob_sha)
    rep = validate(spec, cat)
    if not rep.ok:
        _print_issues(rep.issues)
        return 1
    with PobEngine() as eng, EnginePool(workers=workers) as pool:
        a = assemble(spec, cat, eng, variants(spec)[0])
        if not a.ok:
            _print_issues(a.issues)
            return 1
        sk = cat.resolve("skill", spec.main_skill).entry["id"]
        if pieces is not None:
            kp = [{"kind": k, "id": i.split("@")[0], **({"slot": i.split("@")[1]} if "@" in i else {})} for k, i in (x.split(":", 1) for x in pieces)]
            for r in ablate(cat, pool, a.xml, kp, rep.metric, skill_id=sk, engine=eng):
                d = "-" if r.delta_rel is None else f"{r.delta_rel:+.1%}"
                print(f"{r.verdict:20} {r.piece['kind']}:{r.piece['id']}  worth {d}  {r.replacement or ''} {r.note}")
            return 0
        xml = a.xml
        if weapon:
            try:
                xml = equip_probe_weapon(cat, eng, xml, weapon)
            except ValueError as ex:
                print(f"error: {ex}"); return 1
        s = sweep(cat, pool, xml, kind, rep.metric, skill_id=sk, engine=eng)
    print(f"{s.kind} sweep on {s.metric}: baseline {s.baseline:.1f}, {len(s.entries)} entries, {s.seconds:.0f} s")
    for e in s.entries[:top]:
        print(f"  {e.name:36} {'-' if e.delta is None else format(e.delta, '+.1f'):>10}  pts {e.points}  {','.join(e.flags)}")
    for n in s.notes:
        print("note:", n)
    return 0


def _census(args: list[str]) -> int:
    """census spec.yaml [--kinds keystone,notable,ascendancy] [--conditions none|all|a,b] [--workers N] [--out DIR]"""
    import json as _json
    from pathlib import Path

    from pos_engine.engine import PobEngine
    from pos_pool.pool import EnginePool

    from . import data
    from .assemble import assemble, variants
    from .census import KINDS, census, render

    opt = {"--kinds": ",".join(KINDS), "--conditions": "all", "--workers": "2", "--out": ""}
    rest = []
    it = iter(args)
    for a in it:
        if a in opt:
            opt[a] = next(it, opt[a])
        else:
            rest.append(a)
    if len(rest) != 1:
        print("usage: python -m pos_pipeline census spec.yaml [--kinds keystone,notable,ascendancy] [--conditions none|all|a,b] [--workers N] [--out DIR]")
        return 2
    spec = load_spec(rest[0])
    cat = Catalogue.load(pob_sha=spec.pob_sha)
    rep = validate(spec, cat)
    if not rep.ok:
        _print_issues(rep.issues)
        return 1
    names = list(data.conditions()) if opt["--conditions"] == "all" else [n for n in opt["--conditions"].split(",") if n and n != "none"]
    profiles = {"base": {}}
    if names:
        profiles["conditions:" + ("all" if opt["--conditions"] == "all" else "+".join(names))] = data.condition_options(names)
    with PobEngine() as eng, EnginePool(workers=int(opt["--workers"])) as pool:
        a = assemble(spec, cat, eng, variants(spec)[0])
        if not a.ok:
            _print_issues(a.issues)
            return 1
        res = census(cat, pool, a.xml, rep.metric, kinds=opt["--kinds"].split(","), profiles=profiles, engine=eng)
    print(render(res))
    if opt["--out"]:
        out = Path(opt["--out"]); out.mkdir(parents=True, exist_ok=True)
        (out / "census.json").write_text(_json.dumps(res, indent=1))
        (out / "census.md").write_text(render(res))
    return 0


def _diagnose(args: list[str]) -> int:
    """diagnose BUILD.xml [--metric FullDPS] [--bench id[,id]] [--json] | diagnose --calibrate"""
    import json as _json

    from .diagnose import calibration, diagnose, render
    if "--calibrate" in args:
        cal = calibration(refresh=True)
        for c in cal.values():
            print(f"{'ok  ' if c.ok else 'FAIL'} {c.id:18s} {c.reason}")
        return 0 if all(c.ok for c in cal.values()) else 1
    opt = {"--metric": "FullDPS", "--bench": ""}
    rest = []
    it = iter(args)
    for a in it:
        if a in opt:
            opt[a] = next(it, opt[a])
        elif a != "--json":
            rest.append(a)
    if len(rest) != 1:
        print("usage: python -m pos_pipeline diagnose BUILD.xml [--metric FullDPS] [--bench arbiter_ash,breach_t15] [--json] | diagnose --calibrate")
        return 2
    d = diagnose(open(rest[0], encoding="utf-8").read(), opt["--metric"], [b for b in opt["--bench"].split(",") if b])
    print(_json.dumps(d.to_dict(), indent=1) if "--json" in args else render(d))
    return 0


def _ceilings(args: list[str]) -> int:
    """ceilings BUILD.xml [--metric FullDPS] [--ids a,b] [--required N] [--line id=TEXT]... [--json]"""
    import json as _json

    from . import ceilings as C
    opt = {"--metric": "FullDPS", "--ids": "", "--required": ""}
    lines: dict[str, str] = {}
    rest = []
    it = iter(args)
    for a in it:
        if a == "--line":
            k, _, v = next(it, "=").partition("=")
            lines[k] = v
        elif a in opt:
            opt[a] = next(it, opt[a])
        elif a != "--json":
            rest.append(a)
    if len(rest) != 1:
        print("usage: python -m pos_pipeline ceilings BUILD.xml [--metric FullDPS] [--ids id,id] [--required N] [--line id=STAT LINE] [--json]")
        return 2
    xml = open(rest[0], encoding="utf-8").read()
    ids = [i for i in opt["--ids"].split(",") if i] or None
    res = C.evaluate(xml, ids, metric=opt["--metric"], lines=lines)
    joint = C.interaction(res, xml, metric=opt["--metric"])
    req = float(opt["--required"]) if opt["--required"] else None
    if "--json" in args:
        print(_json.dumps({"results": [r.to_dict() for r in res], "joint": joint}, indent=1))
    else:
        print(C.render(res, opt["--metric"], req, joint))
    return 0


def main(argv: list[str]) -> int:
    if argv and argv[0] == "ceilings":
        return _ceilings(argv[1:])
    if argv and argv[0] == "play":
        return _play(argv[1:])
    if argv and argv[0] == "slate":
        return _slate(argv[1:])
    if argv and argv[0] == "run":
        return _run(argv[1:])
    if argv and argv[0] == "report":
        from pathlib import Path

        from .report import load_run, write_report
        out = argv[2] if len(argv) > 2 else (argv[1] if Path(argv[1]).is_dir() else str(Path(argv[1]).parent))
        write_report(load_run(argv[1]), out)
        print(f"wrote report.md and results.sqlite in {out}")
        return 0
    if len(argv) >= 3 and argv[0] == "sweep":
        rest = list(argv[3:])
        weapon = rest.pop(rest.index("--weapon") + 1) if "--weapon" in rest and rest.index("--weapon") + 1 < len(rest) else None
        if "--weapon" in rest:
            rest.remove("--weapon")
        return _sweep(argv[1], argv[2], int(rest[0]) if rest else 2, int(rest[1]) if len(rest) > 1 else 15, weapon=weapon)
    if len(argv) >= 3 and argv[0] == "ablate":
        return _sweep(argv[1], "", 2, 0, argv[2:])
    if argv and argv[0] == "census":
        return _census(argv[1:])
    if argv and argv[0] == "diagnose":
        return _diagnose(argv[1:])
    if len(argv) >= 2 and argv[0] == "assemble":
        return _assemble(argv[1], argv[2] if len(argv) > 2 else None)
    if len(argv) >= 2 and argv[0] == "supports":
        return _supports(argv[1], int(argv[2]) if len(argv) > 2 else 2)
    if len(argv) >= 2 and argv[0] == "tree":
        return _tree(argv[1], int(argv[2]) if len(argv) > 2 else 2, int(argv[3]) if len(argv) > 3 else 0)
    if len(argv) >= 3 and argv[0] == "gear":
        return _gear(argv[1], argv[2], [a for a in argv[3:] if "=" in a])
    if len(argv) == 2 and argv[0] == "import":
        return _import(argv[1])
    if len(argv) != 2 or argv[0] != "validate":
        print("usage: python -m pos_pipeline validate spec.yaml | slate validate slate.yaml | sweep spec.yaml KIND [workers] [top] [--weapon Base] (KIND keystone|ascendancy|unique:<slot>|support) | ablate spec.yaml kind:id[@slot]... | assemble spec.yaml [out_dir] | supports spec.yaml [workers] | tree spec.yaml [workers] [candidates; default best of 100/200/400] | gear spec.yaml TIER slot=Base... | census spec.yaml [--kinds K] [--conditions C] [--out DIR] | diagnose BUILD.xml [--metric M] [--bench ids] [--json] | diagnose --calibrate | ceilings BUILD.xml [--metric M] [--ids a,b] [--required N] [--line id=TEXT] [--json] | import code.pobcode | report DIR [OUT] | run spec.yaml slot=Base... [--preflight] [--workers N] [--max-minutes M] [--force] [--realloc-rounds N] [--out DIR]")
        return 2
    try:
        spec = load_spec(argv[1])
    except SpecError as e:
        print(f"error: {e}")
        return 1
    rep = validate(spec, Catalogue.load(pob_sha=spec.pob_sha))
    for i in rep.issues:
        tag = f"{i.severity}[{i.code}{'/' + i.confidence if i.confidence else ''}]"
        print(f"{tag} {i.path}: {i.message}" + (f"  suggestions: {', '.join(i.suggestions)}" if i.suggestions else ""))
    print(f"metric: {rep.metric} ({rep.metric_note}); config profile hash: {rep.profile_hash}")
    print("OK" if rep.ok else f"{len(rep.errors)} error(s)")
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
