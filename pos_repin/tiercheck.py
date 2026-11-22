"""Tier-table checks after a re-pin: affix groups new in ModItem.lua with no premium weight, dead premium rules, stale anchors."""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from pos_tiers.resolver import ModIndex, load_mods
from pos_tiers.tiers import TierTable


@dataclass
class TierCheck:
    new_groups_unweighted: list[str] = field(default_factory=list)  # in new ModItem, not in old, fall to default weight 1.0
    removed_groups: list[str] = field(default_factory=list)
    dead_rules: list[str] = field(default_factory=list)             # premium patterns matching no group now
    stale_anchors: list[str] = field(default_factory=list)          # every anchor: an economy reset invalidates them


def old_mod_file(pob_root: Path, old_sha: str, dest: Path) -> Path:
    """Write Data/ModItem.lua as of old_sha (LuaJIT reads it as plain data)."""
    txt = subprocess.run(["git", "-C", str(pob_root), "show", f"{old_sha}:src/Data/ModItem.lua"], capture_output=True, text=True, check=True).stdout
    dest.write_text(txt, encoding="utf-8")
    return dest


def check_tiers(old_groups: set[str], new_groups: set[str], table: TierTable) -> TierCheck:
    c = TierCheck()
    for g in sorted(new_groups - old_groups):
        if not any(re.fullmatch(r["pattern"], g) for r in table.raw["premium_weights"]):
            c.new_groups_unweighted.append(g)
    c.removed_groups = sorted(old_groups - new_groups)
    for r in table.raw["premium_weights"]:
        if not any(re.fullmatch(r["pattern"], g) for g in new_groups):
            c.dead_rules.append(r["pattern"])
    for slot, tiers in (table.raw.get("anchors") or {}).items():
        for tier, a in tiers.items():
            c.stale_anchors.append(f"{slot}/{tier}: {a.get('div')} div, dated {a.get('date')}")
    return c


def groups_of(mod_file: Path) -> set[str]:
    return ModIndex(load_mods(mod_file)).groups


def render(c: TierCheck, limit: int = 60) -> str:
    out = ["## Tier table", ""]
    def lst(title, items, hint=""):
        out.append(f"**{title}**: {len(items) or 'none'}{hint if items else ''}")
        out.extend(f"- `{i}`" for i in items[:limit])
        if len(items) > limit:
            out.append(f"- ... {len(items) - limit} more")
    lst("New affix groups with no premium weight (priced at default 1.0; decide whether each needs a weight)", c.new_groups_unweighted)
    lst("Removed affix groups", c.removed_groups)
    lst("Premium rules matching no group now (delete or fix in data/tiers.yaml)", c.dead_rules)
    lst("Price anchors to treat as stale (economy reset: resample after launch)", c.stale_anchors)
    return "\n".join(out) + "\n"
