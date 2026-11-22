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

    if len(argv) != 2 or argv[0] != "validate":
        print("usage: python -m pos_pipeline slate validate slate.yaml")
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
    from .orchestrate import DEFAULT_MAX_MINUTES, DEFAULT_REALLOC_ROUNDS, RunRefused, engine_stages, run

    ap = argparse.ArgumentParser(prog="python -m pos_pipeline run")
    ap.add_argument("spec")
    ap.add_argument("bases", nargs="*", help="slot=Base, e.g. weapon='Acrid Wand' (ring=Base sets both rings)")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--max-minutes", type=float, default=DEFAULT_MAX_MINUTES, help="refuse above this estimate unless --force")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--preflight", action="store_true", help="print the cost estimate and exit")
    ap.add_argument("--realloc-rounds", type=int, default=DEFAULT_REALLOC_ROUNDS, help="0 = cheap gear mode (about 2.3x faster, weaker)")
    ap.add_argument("--out", default=None, help="directory for run.json and cache.sqlite")
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
    kw = dict(metric=rep.metric, slots=len(bases) or len(SLOTS), workers=a.workers, realloc_rounds=a.realloc_rounds,
              max_minutes=a.max_minutes, log=print)
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
        with engine_stages(spec, cat, rep, bases, workers=a.workers, cache=cache, realloc_rounds=a.realloc_rounds) as (st, skill_of):
            r = run(spec, st, skill_id=skill_of, force=a.force, out_dir=a.out, meta=meta, **kw)
    except RunRefused as e:
        print(f"refused: {e}"); return 3
    for t, (v, val) in r.best_per_tier().items():
        print(f"tier {t}: best {r.metric} {val:.1f} with {v or '(no axes)'}")
    return 1 if any(not s.ok for s in r.seeds) else 0


def _sweep(path: str, kind: str, workers: int, top: int, pieces: list[str] | None = None) -> int:
    """`sweep spec.yaml KIND [workers] [top]` / `ablate spec.yaml kind:id ...` on the assembled (unsearched) seed."""
    from pos_engine.engine import PobEngine
    from pos_pool.pool import EnginePool

    from .assemble import assemble, variants
    from .sweep import ablate, sweep

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
        s = sweep(cat, pool, a.xml, kind, rep.metric, skill_id=sk, engine=eng)
    print(f"{s.kind} sweep on {s.metric}: baseline {s.baseline:.1f}, {len(s.entries)} entries, {s.seconds:.0f} s")
    for e in s.entries[:top]:
        print(f"  {e.name:36} {'-' if e.delta is None else format(e.delta, '+.1f'):>10}  pts {e.points}  {','.join(e.flags)}")
    for n in s.notes:
        print("note:", n)
    return 0


def main(argv: list[str]) -> int:
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
        return _sweep(argv[1], argv[2], int(argv[3]) if len(argv) > 3 else 2, int(argv[4]) if len(argv) > 4 else 15)
    if len(argv) >= 3 and argv[0] == "ablate":
        return _sweep(argv[1], "", 2, 0, argv[2:])
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
        print("usage: python -m pos_pipeline validate spec.yaml | slate validate slate.yaml | sweep spec.yaml KIND [workers] [top] (KIND keystone|ascendancy|unique:<slot>|support) | ablate spec.yaml kind:id[@slot]... | assemble spec.yaml [out_dir] | supports spec.yaml [workers] | tree spec.yaml [workers] [candidates; default best of 100/200/400] | gear spec.yaml TIER slot=Base... | import code.pobcode | report DIR [OUT] | run spec.yaml slot=Base... [--preflight] [--workers N] [--max-minutes M] [--force] [--realloc-rounds N] [--out DIR]")
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
