"""Load and validate data/tiers.yaml; point costing."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_PATH = Path(__file__).resolve().parents[1] / "data" / "tiers.yaml"


@dataclass
class TierTable:
    raw: dict

    @classmethod
    def load(cls, path: Path | str = DEFAULT_PATH) -> "TierTable":
        t = cls(yaml.safe_load(Path(path).read_text()))
        t.validate()
        return t

    def validate(self) -> None:
        r = self.raw
        if r.get("schema_version") != 1:
            raise ValueError("unsupported tiers.yaml schema_version")
        total = sum(r["default_allocation"].values())
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"default_allocation sums to {total}, expected 1")
        for s in r["default_allocation"]:
            if s not in r["slots"]:
                raise ValueError(f"allocation slot {s!r} has no slots entry")
        budgets = [v["budget"] for v in r["tiers"].values() if v["budget"] is not None]
        if budgets != sorted(budgets):
            raise ValueError("tier budgets must ascend (null/uncapped last)")
        for rule in r["premium_weights"]:
            re.compile(rule["pattern"])

    @property
    def tier_names(self) -> list[str]:
        return list(self.raw["tiers"])

    def slot_tags(self, slot: str) -> list[str]:
        return self.raw["slots"][slot]["tags"]

    def budget(self, tier: str) -> float | None:
        return self.raw["tiers"][tier]["budget"]

    def slot_budget(self, tier: str, slot: str) -> float | None:
        b = self.budget(tier)
        return None if b is None else b * self.raw["default_allocation"][slot]

    def premium(self, group: str) -> float:
        for rule in self.raw["premium_weights"]:
            if re.fullmatch(rule["pattern"], group):
                return float(rule["weight"])
        return 1.0

    def affix_points(self, group: str, rank: int) -> float:
        for band in self.raw["rank_points"]:
            if rank <= band["max_rank"]:
                return band["points"] * self.premium(group)
        raise ValueError("rank_points has no catch-all band")
