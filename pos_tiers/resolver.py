"""Resolve (slot, affix group, rank) to a concrete mod from the pinned PoB ModItem.lua.

ModItem.lua is loaded by LuaJIT (tools/build_luajit.sh) and dumped to JSON, so parsing is exact and
re-pinning PoB needs no code change. Rank 1 = highest-level tier of the group eligible on the slot.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pos_engine.paths import bundled_luajit, pob_src_dir

_DUMP_LUA = r"""
local function esc(s) return (s:gsub('[%c"\\]', function(c) return string.format("\\u%04x", c:byte()) end)) end
local mods = dofile(arg[1])
local out = {}
for id, m in pairs(mods) do
  local keys, vals, lines = {}, {}, {}
  for i, k in ipairs(m.weightKey or {}) do keys[#keys+1] = '"'..esc(k)..'"'; vals[#vals+1] = tostring(m.weightVal[i] or 0) end
  for _, l in ipairs(m) do lines[#lines+1] = '"'..esc(l)..'"' end
  out[#out+1] = string.format('"%s":{"type":"%s","level":%d,"group":"%s","affix":"%s","keys":[%s],"vals":[%s],"text":[%s]}',
    esc(id), esc(m.type), m.level or 0, esc(m.group or ""), esc(m.affix or ""), table.concat(keys, ","), table.concat(vals, ","), table.concat(lines, ","))
end
io.write("{", table.concat(out, ","), "}")
"""


@dataclass(frozen=True)
class ModRoll:
    id: str
    group: str
    type: str  # Prefix | Suffix
    level: int
    rank: int
    of: int  # tiers available in this group on the slot
    text: tuple[str, ...]


def load_mods(mod_file: Path | None = None, luajit: Path | None = None) -> dict:
    lj = luajit or bundled_luajit()
    if lj is None:
        raise RuntimeError("LuaJIT not built: run tools/build_luajit.sh")
    mod_file = mod_file or pob_src_dir() / "Data" / "ModItem.lua"
    p = subprocess.run([str(lj), "-e", f"arg={{[1]={json.dumps(str(mod_file))}}} " + _DUMP_LUA],
                       capture_output=True, text=True, check=True)
    return json.loads(p.stdout)


class ModIndex:
    def __init__(self, mods: dict):
        self.mods = mods
        self.groups = {m["group"] for m in mods.values() if m["group"]}

    def eligible(self, tags: list[str]) -> dict[str, list[tuple[str, dict]]]:
        """group -> [(id, mod)] sorted by level descending, for mods spawnable on any of `tags`."""
        out: dict[str, list] = {}
        for mid, m in self.mods.items():
            if not m["group"]:
                continue
            w = dict(zip(m["keys"], m["vals"]))
            if any(w.get(t, 0) > 0 for t in tags):
                out.setdefault(m["group"], []).append((mid, m))
        for lst in out.values():
            lst.sort(key=lambda x: (-x[1]["level"], x[0]))
        return out

    def resolve(self, tags: list[str], group: str, rank: int) -> ModRoll:
        tiers = self.eligible(tags).get(group)
        if not tiers:
            raise KeyError(f"group {group!r} not spawnable on {tags}")
        if rank < 1:
            raise ValueError("rank starts at 1")
        mid, m = tiers[min(rank, len(tiers)) - 1]
        return ModRoll(mid, group, m["type"], m["level"], min(rank, len(tiers)), len(tiers), tuple(m["text"]))


@lru_cache(maxsize=1)
def default_index() -> ModIndex:
    return ModIndex(load_mods())
