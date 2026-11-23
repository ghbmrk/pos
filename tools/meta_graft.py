"""Meta-graft loop (docs/squire-channels.md): how close does a Knight + Squire version of a strong build get to it?

Usage: python tools/meta_graft.py BUILD [BUILD ...]      BUILD = pobb.in link, file with a PoB code, or a .xml file
Per build, against PoB's Pinnacle boss (metric HitAilmentDPS):
  1. meta: the build as exported;
  2. no_asc: every ascendancy node deallocated (the Knight replaces the build's ascendancy; Knight node text adds no
     player damage, Standards unpublished);
  3. each Squire Presence/skill combo from COMBOS, uptime-blended (ASSUMED: Presence, items worn by the Squire);
  4. squire_own: the build's gear minus jewellery, no passive tree, same skill, x1.15 (Knight companion node), x0.75
     with Leer Cast on the Squire (ASSUMED: the Squire can use the skill and has gear as good as the player's).
ASSUMED what-if numbers; redo on 1.0 data.
"""
from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pos_engine.engine import PobEngine  # noqa: E402
from pos_pipeline import actors  # noqa: E402

BASE = {"enemyIsBoss": "Pinnacle"}
METRIC = "HitAilmentDPS"
COMPANION_NODE, LEER_SELF = 1.15, 0.75


def E(i, p=None, u=1.0):
    return actors.make_effect(i, p, u, "ASSUMED")


RES0 = lambda: [E("enemy_fire_res", {"value": 0}), E("enemy_cold_res", {"value": 0}), E("enemy_lightning_res", {"value": 0})]  # noqa: E731
COMBOS = {   # name -> (effects, Leer Cast on the Squire?)
    "Calamity + Leer": (RES0() + [E("ally_increased_damage", {"pct": 50})], True),
    "Calamity + Leer + shock 0.5": (RES0() + [E("ally_increased_damage", {"pct": 50}), E("enemy_shocked", None, 0.5)], True),
    "Perfidy + Leer + shock 0.5": ([E("enemy_intimidated"), E("ally_increased_damage", {"pct": 50}), E("enemy_shocked", None, 0.5)], True),
    "Calamity + shock 0.5 (no Leer)": (RES0() + [E("enemy_shocked", None, 0.5)], False),
}


def load(eng: PobEngine, src: str) -> str:
    if src.endswith(".xml"):
        eng.load_build_xml(Path(src).read_text())
    else:
        code = src
        if src.startswith("http"):
            url = src.rstrip("/") + ("/raw" if "pobb.in" in src and not src.endswith("/raw") else "")
            code = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode()
        elif Path(src).is_file():
            code = Path(src).read_text()
        eng.load_build_code(code.strip())
    eng.set_config(options=BASE)
    return eng.get_xml()


def metric(eng: PobEngine, xml: str, opts) -> float:
    eng.load_build_xml(xml)
    eng.set_config(options=dict(opts) or None)
    return float(eng.get_stats([METRIC])["stats"].get(METRIC) or 0.0)


def nodes(xml: str) -> list[int]:
    m = re.search(r'<Spec [^>]*nodes="([^"]*)"', xml)
    return [int(n) for n in m.group(1).split(",") if n] if m else []


def graft(eng: PobEngine, src: str) -> list[str]:
    xml = load(eng, src)
    b = eng.get_build()
    meta = metric(eng, xml, BASE)
    eng.load_build_xml(xml)
    for n in nodes(xml):
        if (eng.get_passive(n) or {}).get("ascendancy"):
            eng.dealloc_passive(n)
    noasc = eng.get_xml()
    no = metric(eng, noasc, BASE)
    eng.load_build_xml(noasc)
    for s in ("Amulet", "Ring 1", "Ring 2", "Belt"):
        try:
            eng.unequip_item(s)
        except Exception:  # noqa: BLE001
            pass
    for n in nodes(eng.get_xml()):
        try:
            eng.dealloc_passive(n)
        except Exception:  # noqa: BLE001
            pass
    sq = metric(eng, eng.get_xml(), BASE) * COMPANION_NODE
    model = actors.SeparateBuildModel("squire", lambda x, o: metric(eng, x, o), None, BASE)
    out = [f"## {b.get('ascendancy')} / {b.get('mainSkill')} (L{b.get('level')}) - {src}", "",
           "| Variant | Player | Squire own | Total | vs meta |", "|---|---|---|---|---|",
           f"| meta (reference) | {meta:,.0f} | - | {meta:,.0f} | 100% |",
           f"| ascendancy removed | {no:,.0f} | - | {no:,.0f} | {no / meta:.0%} |",
           f"| Squire own damage only | {no:,.0f} | {sq:,.0f} | {no + sq:,.0f} | {(no + sq) / meta:.0%} |"]
    for name, (eff, leer) in COMBOS.items():
        p = model.evaluate(noasc, None, eff).main
        s = sq * (LEER_SELF if leer else 1.0)
        out.append(f"| {name} | {p:,.0f} | {s:,.0f} | {p + s:,.0f} | {(p + s) / meta:.0%} |")
    return out


def main(argv: list[str]) -> int:
    lines = ["ASSUMED SQUIRE WHAT-IF (not game data; redo on 1.0)", ""]
    with PobEngine() as eng:
        for src in argv[1:]:
            lines += graft(eng, src) + [""]
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
