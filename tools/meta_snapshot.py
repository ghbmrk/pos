#!/usr/bin/env python3
"""Snapshot poe.ninja's build index (class / class+skill shares per league) for PoE1 and PoE2 into data/meta/.

Evidence for data/meta_lessons.yaml (docs/meta-lessons.md). poe.ninja keeps the current league plus the last few
(`status` 1-2 = old); per-build exports are not in this API. Private leagues and leagues without statistics are dropped.

    python tools/meta_snapshot.py            # writes data/meta/ninja-<UTC date>.json
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import urllib.request
from pathlib import Path

URL = "https://poe.ninja/{game}/api/data/build-index-state"
ROOT = Path(__file__).resolve().parent.parent


def fetch(game: str) -> list[dict]:
    req = urllib.request.Request(URL.format(game=game), headers={"User-Agent": "pos-meta-snapshot"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    out = []
    for lg in data.get("leagueBuilds", []):
        if "(PL" in lg.get("leagueName", "") or not lg.get("statistics"):
            continue
        out.append({k: lg.get(k) for k in ("leagueName", "leagueUrl", "total", "status", "hardcore", "statistics")})
    return out


def main(argv: list[str]) -> int:
    day = dt.datetime.now(dt.timezone.utc).date().isoformat()
    snap = {"source": "poe.ninja build-index-state", "fetched": day, "url": URL,
            "games": {g: fetch(g) for g in ("poe1", "poe2")}}
    path = ROOT / "data" / "meta" / f"ninja-{day}.json"
    path.write_text(json.dumps(snap, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
