"""python -m pos_repin report --old data/catalogue/<old>.json --new data/catalogue/<new>.json [--specs specs] [--old-sha SHA] [--out docs/repin/<new7>.md]

Exit 1 if any saved spec fails revalidation. Always writes the report. Run by tools/repin.sh.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from pos_catalogue import Catalogue
from pos_engine.paths import ROOT, pob_src_dir
from pos_tiers.tiers import TierTable

from . import diff, revalidate, tiercheck


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="pos_repin")
    ap.add_argument("cmd", choices=["report"])
    ap.add_argument("--old", required=True, type=Path)
    ap.add_argument("--new", required=True, type=Path)
    ap.add_argument("--specs", type=Path, default=ROOT / "specs")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--skip-tiers", action="store_true", help="skip the ModItem group check (needs LuaJIT and git history)")
    a = ap.parse_args(argv)

    old = json.loads(a.old.read_text(encoding="utf-8"))
    new_text = a.new.read_text(encoding="utf-8")
    new = json.loads(new_text)
    d = diff.diff_catalogues(old, new)
    parts = [f"# Re-pin report: {old['pob_sha'][:7]} -> {new['pob_sha'][:7]}\n", diff.render(d)]

    results = revalidate.revalidate_specs(a.specs, Catalogue(new))
    parts.append(revalidate.render(results, a.specs))

    if a.skip_tiers:
        parts.append("## Tier table\n\nSkipped.\n")
    else:
        pob_root = pob_src_dir().parent
        with tempfile.TemporaryDirectory() as td:
            og = tiercheck.groups_of(tiercheck.old_mod_file(pob_root, old["pob_sha"], Path(td) / "old.lua"))
            ng = tiercheck.groups_of(pob_src_dir() / "Data" / "ModItem.lua")
        parts.append(tiercheck.render(tiercheck.check_tiers(og, ng, TierTable.load())))

    parts.append("## Still manual\n\n- Golden run: `pytest pos_engine/tests` includes the Fireball golden DPS; review value shifts, do not update goldens blindly.\n"
                 "- Skills/supports/passives that Lua parses differently at 1.0 surface only as engine test failures or unparsed-mod warnings.\n")
    text = "\n".join(parts)
    out = a.out or ROOT / "docs" / "repin" / f"{new['pob_sha'][:7]}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    failing = sum(not r.ok for r in results)
    print(f"report: {out}\ncatalogue breaking entries: {d.breaking}; specs failing: {failing}/{len(results)}")
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
