"""`python -m pos_pipeline validate spec.yaml` — prints issues, exits 1 on errors."""
import sys

from pos_catalogue import Catalogue

from . import SpecError, data, load_spec, validate


def _print_issues(issues) -> None:
    for i in issues:
        tag = f"{i.severity}[{i.code}{'/' + i.confidence if i.confidence else ''}]"
        print(f"{tag} {i.path}: {i.message}" + (f"  suggestions: {', '.join(i.suggestions)}" if i.suggestions else ""))


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


def main(argv: list[str]) -> int:
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
        print("usage: python -m pos_pipeline validate spec.yaml | assemble spec.yaml [out_dir] | supports spec.yaml [workers] | tree spec.yaml [workers] [candidates; default best of 100/200/400] | gear spec.yaml TIER slot=Base... | import code.pobcode")
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
