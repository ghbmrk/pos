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
    q = sub.add_parser("search", help="filter entries of one kind (read-only)")
    q.add_argument("kind", choices=KINDS)
    q.add_argument("text", nargs="*")
    q.add_argument("--skill-type", action="append")
    q.add_argument("--tag", action="append")
    q.add_argument("--ascendancy")
    q.add_argument("--class", dest="class_")
    q.add_argument("--limit", type=int, default=25)
    e = sub.add_parser("enablers", help="what grants or names a skill type")
    e.add_argument("skill_type")
    b = sub.add_parser("bridges", help="entries mentioning both terms")
    b.add_argument("term_a")
    b.add_argument("term_b")
    b.add_argument("--limit", type=int, default=15)
    x = sub.add_parser("explain", help="the full text of one entry (id: name for uniques/keystones/notables, gem id for skills/supports)")
    x.add_argument("kind", choices=KINDS)
    x.add_argument("id")
    a = ap.parse_args(argv)
    if a.cmd == "export":
        print(export_catalogue())
        return 0
    if a.cmd in ("search", "enablers", "bridges", "explain"):
        cat = Catalogue.load()
        if a.cmd == "search":
            r = cat.search(a.kind, text=" ".join(a.text) or None, skill_types=a.skill_type, tags=a.tag, ascendancy=a.ascendancy, class_=a.class_, limit=a.limit)
        elif a.cmd == "enablers":
            r = cat.enablers(a.skill_type)
        elif a.cmd == "bridges":
            r = cat.bridges(a.term_a, a.term_b, a.limit)
        else:
            try:
                r = cat.explain(a.kind, a.id)
            except KeyError as ex:
                print(ex, file=sys.stderr)
                return 1
        print(json.dumps(r, indent=1, ensure_ascii=False))
        return 0
    res = Catalogue.load().resolve(a.kind, a.text)
    print(json.dumps({"status": res.status, "matches": res.matches, "suggestions": [s["name"] for s in res.suggestions]}, indent=1))
    return 0 if res.status == "exact" else 1


if __name__ == "__main__":
    sys.exit(main())
