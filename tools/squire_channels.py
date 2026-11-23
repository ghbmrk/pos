"""Rank the Squire value-channel runs (docs/squire-channels.md). ASSUMED what-if numbers only.

Usage: python tools/squire_channels.py OUT_DIR [--md FILE]
Reads OUT_DIR/<scenario>/run.json written by tools/squire_channels.sh and prints one row per scenario: player alone,
player with the Squire's effects (uptime-blended), the Squire's own damage, combined, the gain over `own_damage`
(Squire as a plain second damage source), EHP with every effect on vs off, and the Arbiter benchmark.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def rows(out: Path) -> list[dict]:
    res = []
    for d in sorted(p for p in out.iterdir() if (p / "run.json").is_file()):
        r = json.loads((d / "run.json").read_text())
        for s in r.get("seeds", []):
            for tier, t in (s.get("tiers") or {}).items():
                a = t.get("actor") or {}
                b = (t.get("bench") or {}).get("arbiter_ash") or {}
                sv = a.get("survival") or {}
                res.append({
                    "scenario": d.name, "tier": tier, "ok": t.get("ok"), "error": t.get("error") or a.get("error"),
                    "player": a.get("without_companion") if a.get("without_companion") is not None else t.get("value"),
                    "with_effects": a.get("main"), "squire": a.get("companion"), "combined": a.get("total"),
                    "ehp": sv.get("TotalEHP") or (t.get("stats") or {}).get("TotalEHP"),
                    "ehp_without": sv.get("TotalEHP_without") or (t.get("stats") or {}).get("TotalEHP"),
                    "ttk": b.get("ttk_s"), "survive": b.get("survive"), "hits_to_die": b.get("generic_hits_to_die"),
                    "metric": r.get("metric"),
                })
    base = {(x["tier"]): x["combined"] for x in res if x["scenario"] == "own_damage" and x["combined"]}
    for x in res:
        ref = base.get(x["tier"])
        x["vs_own_damage"] = (x["combined"] / ref) if (ref and x["combined"]) else None
    return sorted(res, key=lambda x: -(x["combined"] or 0))


def fmt(v, nd=0):
    if v is None:
        return "n/a"
    if isinstance(v, bool):
        return "yes" if v else "no"
    return f"{v:,.{nd}f}"


def table(rs: list[dict]) -> str:
    head = ("| Scenario | Player alone | Player with effects | Squire own | Combined | x own_damage | EHP on / off | "
            "Arbiter TTK s | Hits to die |\n|---|---|---|---|---|---|---|---|---|")
    lines = [head]
    for x in rs:
        if x["error"]:
            lines.append(f"| {x['scenario']} | error: {x['error']} |||||||")
            continue
        lines.append(f"| {x['scenario']} | {fmt(x['player'])} | {fmt(x['with_effects'])} | {fmt(x['squire'])} | "
                     f"{fmt(x['combined'])} | {fmt(x['vs_own_damage'], 2)} | {fmt(x['ehp'])} / {fmt(x['ehp_without'])} | "
                     f"{fmt(x['ttk'], 1)} | {fmt(x['hits_to_die'], 1)} |")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    out = Path(argv[1])
    t = "ASSUMED SQUIRE WHAT-IF (not game data; redo on 1.0)\n\n" + table(rows(out))
    if "--md" in argv:
        Path(argv[argv.index("--md") + 1]).write_text(t + "\n", encoding="utf-8")
    print(t)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
