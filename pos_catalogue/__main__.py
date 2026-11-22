import argparse
import json
import sys

from .catalogue import KINDS, Catalogue
from .export import export_catalogue


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="pos_catalogue")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("export", help="write data/catalogue/<sha>.json from the pinned PoB")
    r = sub.add_parser("resolve", help="resolve a name")
    r.add_argument("kind", choices=KINDS)
    r.add_argument("text")
    a = ap.parse_args(argv)
    if a.cmd == "export":
        print(export_catalogue())
        return 0
    res = Catalogue.load().resolve(a.kind, a.text)
    print(json.dumps({"status": res.status, "matches": res.matches, "suggestions": [s["name"] for s in res.suggestions]}, indent=1))
    return 0 if res.status == "exact" else 1


if __name__ == "__main__":
    sys.exit(main())
