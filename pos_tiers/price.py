"""PriceModel: gear -> price estimate. AnchorSumModel is the Option 4 implementation (docs/price-tiers.md).

Swap in a regression or craft-cost model by implementing PriceModel; the variant generator only sees the interface.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .tiers import TierTable


@dataclass
class GearItem:
    slot: str
    affixes: list[tuple[str, int]] = field(default_factory=list)  # (group, rank)
    unique_band: str | None = None  # key of unique_bands; replaces affixes


@dataclass
class Estimate:
    div: float | None  # None when any slot lacks an anchor
    points: float
    label: str
    missing: list[str] = field(default_factory=list)


class PriceModel(Protocol):
    def price(self, gear: list[GearItem]) -> Estimate: ...


class AnchorSumModel:
    def __init__(self, table: TierTable):
        self.t = table

    def item_points(self, it: GearItem) -> float:
        if it.unique_band:
            return float(self.t.raw["unique_bands"][it.unique_band]["points"])
        return sum(self.t.affix_points(g, r) for g, r in it.affixes)

    def item_tier(self, it: GearItem) -> str:
        """Cheapest tier whose default slot budget covers the item (mirror = uncapped catch-all)."""
        pts = self.item_points(it)
        for name in self.t.tier_names:
            cap = self.t.slot_budget(name, it.slot)
            if cap is None or pts <= cap:
                return name
        raise AssertionError("unreachable")

    def price(self, gear: list[GearItem]) -> Estimate:
        total_div, total_pts, missing, samples, dates = 0.0, 0.0, [], 0, []
        for it in gear:
            total_pts += self.item_points(it)
            if it.unique_band:
                total_div += float(self.t.raw["unique_bands"][it.unique_band]["div"])
                continue
            tier = self.item_tier(it)
            a = (self.t.raw.get("anchors") or {}).get(it.slot, {}).get(tier)
            if not a or a.get("div") is None:
                missing.append(f"{it.slot}:{tier}")
                continue
            total_div += float(a["div"])
            samples += int(a.get("samples", 0))
            dates.append(str(a.get("date", "undated")))
        if missing:
            return Estimate(None, total_pts, "no price: missing anchors " + ", ".join(missing), missing)
        when = max(dates) if dates else "hand-set bands only"
        return Estimate(total_div, total_pts, f"estimate, anchored on {samples} samples, dated {when}")
