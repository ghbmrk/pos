"""Path resolution for the engine layer (forked from poe2-build-mcp, MIT; see LICENSE.maxwilk-poe2-build-mcp).

PoB-PoE2 is a pinned git submodule at third_party/PathOfBuilding-PoE2 (zero local patches).
LuaJIT must be recent enough for `+=` syntax (PoB-PoE2 dev uses it): see tools/build_luajit.sh.
Override with POS_POB_SRC / POB_LUAJIT.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pob_src_dir() -> Path:
    override = os.environ.get("POS_POB_SRC")
    return Path(override) if override else ROOT / "third_party" / "PathOfBuilding-PoE2" / "src"


def pob_headless_script() -> Path:
    return Path(__file__).resolve().parent / "pob_headless.lua"


def bundled_luajit() -> Path | None:
    cand = ROOT / "runtime" / "luajit" / "bin" / "luajit"
    return cand if cand.exists() else None
