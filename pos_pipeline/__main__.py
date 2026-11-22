"""`python -m pos_pipeline validate spec.yaml` — prints issues, exits 1 on errors."""
import sys

from pos_catalogue import Catalogue

from . import SpecError, load_spec, validate


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
    if len(argv) == 2 and argv[0] == "import":
        return _import(argv[1])
    if len(argv) != 2 or argv[0] != "validate":
        print("usage: python -m pos_pipeline validate spec.yaml | assemble spec.yaml [out_dir] | import code.pobcode")
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
