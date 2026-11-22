"""Export the catalogue for the pinned PoB: LuaJIT dumps Lua data (tools/export_catalogue.lua), tree.json adds the passive tree.

Output: data/catalogue/<pob_sha>.json, deterministic (sorted, no timestamps) so re-pins diff cleanly.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from pos_engine.paths import ROOT, bundled_luajit, pob_src_dir

SCHEMA = 1
CATALOGUE_DIR = ROOT / "data" / "catalogue"


def pob_sha(pob_root: Path | None = None) -> str:
    root = pob_root or pob_src_dir().parent
    return subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()


def _latest_tree_dir(src: Path) -> Path:
    def key(p: Path):
        return tuple(int(x) for x in p.name.split("_"))
    dirs = [p for p in (src / "TreeData").iterdir() if re.fullmatch(r"\d+(_\d+)*", p.name) and (p / "tree.json").exists()]
    if not dirs:
        raise RuntimeError(f"no TreeData/<version>/tree.json under {src}")
    return max(dirs, key=key)


def export_tree(src: Path) -> dict:
    tdir = _latest_tree_dir(src)
    tree = json.loads((tdir / "tree.json").read_text(encoding="utf-8"))
    classes, ascendancies = [], []
    for c in tree["classes"]:
        classes.append({"name": c["name"], "ascendancies": [a["name"] for a in c.get("ascendancies", [])]})
        for a in c.get("ascendancies", []):
            ascendancies.append({"name": a["name"], "class": c["name"]})
    keystones, notables = {}, {}
    for n in tree["nodes"].values():
        name = n.get("name")
        if not name or n.get("isOnlyImage"):
            continue
        entry = {"name": name, "node": n["skill"], "stats": n.get("stats", []), "ascendancy": n.get("ascendancyName")}
        if n.get("isKeystone"):
            keystones[(name, n["skill"])] = entry
        elif n.get("isNotable"):
            notables[(name, n["skill"])] = entry
    def ordered(d):
        return [d[k] for k in sorted(d, key=lambda k: (k[0], k[1]))]
    return {
        "version": tdir.name,
        "classes": sorted(classes, key=lambda c: c["name"]),
        "ascendancies": sorted(ascendancies, key=lambda a: a["name"]),
        "keystones": ordered(keystones),
        "notables": ordered(notables),
    }


def run_lua(src: Path, luajit: Path | None = None) -> dict:
    lj = luajit or bundled_luajit()
    if lj is None:
        raise RuntimeError("LuaJIT not built: run tools/build_luajit.sh")
    script = ROOT / "tools" / "export_catalogue.lua"
    p = subprocess.run([str(lj), str(script), str(src)], capture_output=True, text=True, check=True)
    return json.loads(p.stdout)


def build(src: Path | None = None, sha: str | None = None, luajit: Path | None = None) -> dict:
    src = src or pob_src_dir()
    lua = run_lua(src, luajit)
    gems = lua["gems"]
    tree = export_tree(src)
    return {
        "schema": SCHEMA,
        "pob_sha": sha or pob_sha(src.parent),
        "tree_version": tree.pop("version"),
        "skills": [g for g in gems if not g["support"]],
        "supports": [g for g in gems if g["support"]],
        "bases": lua["bases"],
        "uniques": lua["uniques"],
        **tree,
    }


def export_catalogue(out_dir: Path | None = None, **kw) -> Path:
    cat = build(**kw)
    out_dir = out_dir or CATALOGUE_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{cat['pob_sha'][:7]}.json"
    path.write_text(json.dumps(cat, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
