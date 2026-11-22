"""`python -m pos_pipeline validate spec.yaml` — prints issues, exits 1 on errors."""
import sys

from pos_catalogue import Catalogue

from . import SpecError, load_spec, validate


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "validate":
        print("usage: python -m pos_pipeline validate spec.yaml")
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
