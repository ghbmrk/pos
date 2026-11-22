import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_engine.paths import bundled_luajit  # noqa: E402
from pos_tiers.price import AnchorSumModel, GearItem  # noqa: E402
from pos_tiers.resolver import ModIndex, default_index  # noqa: E402
from pos_tiers.tiers import TierTable  # noqa: E402

needs_lj = pytest.mark.skipif(bundled_luajit() is None, reason="run tools/build_luajit.sh")


@pytest.fixture(scope="module")
def table():
    return TierTable.load()


def test_table_valid(table):
    assert table.tier_names[0] == "starter" and table.budget("mirror") is None


def test_bad_allocation_rejected(table):
    bad = {**table.raw, "default_allocation": {**table.raw["default_allocation"], "belt": 0.5}}
    with pytest.raises(ValueError):
        TierTable(bad).validate()


def test_points_scale_with_rank_and_premium(table):
    assert table.affix_points("Strength", 1) > table.affix_points("Strength", 3) > table.affix_points("Strength", 9)
    assert table.affix_points("BaseSpirit", 1) == 4 * table.affix_points("Strength", 1)


def test_synthetic_resolver():
    mods = {
        f"G{i}": {"type": "Prefix", "level": lv, "group": "G", "affix": "", "keys": ["ring", "default"],
                  "vals": [1, 0], "text": [f"+{lv}"]}
        for i, lv in enumerate([1, 30, 60])
    }
    mods["X1"] = {"type": "Suffix", "level": 5, "group": "X", "affix": "", "keys": ["belt"], "vals": [1], "text": []}
    idx = ModIndex(mods)
    assert idx.resolve(["ring"], "G", 1).level == 60
    assert idx.resolve(["ring"], "G", 99).rank == 3  # clamps to lowest tier
    with pytest.raises(KeyError):
        idx.resolve(["ring"], "X", 1)  # belt-only group


@needs_lj
def test_real_mods_resolve(table):
    idx = default_index()
    assert len(idx.mods) > 2000
    top = idx.resolve(table.slot_tags("ring"), "Strength", 1)
    low = idx.resolve(table.slot_tags("ring"), "Strength", 99)
    assert top.level > low.level and top.of == low.of and top.text


@needs_lj
def test_every_slot_has_mods_and_rules_match_groups(table):
    idx = default_index()
    for slot in table.raw["slots"]:
        assert idx.eligible(table.slot_tags(slot)), slot
    # stale-rule check: after a re-pin, a premium rule matching no group needs review
    for rule in table.raw["premium_weights"]:
        assert any(re.fullmatch(rule["pattern"], g) for g in idx.groups), rule["pattern"]


def test_price_model(table):
    m = AnchorSumModel(table)
    it = GearItem("ring", [("Strength", 1), ("BaseSpirit", 1)])  # 4 + 16 = 20 pts
    assert m.item_points(it) == 20
    assert m.item_tier(it) == "high"  # ring slot: starter 2.4, budget 7.2, mid 19.2, high 48
    est = m.price([it])
    assert est.div is None and "ring:high" in est.missing


def test_anchor_sum_and_unique_band(table):
    raw = {**table.raw, "anchors": {"ring": {"high": {"div": 30.0, "samples": 4, "date": "2026-12-20"}}}}
    m = AnchorSumModel(TierTable(raw))
    est = m.price([GearItem("ring", [("Strength", 1), ("BaseSpirit", 1)]), GearItem("amulet", unique_band="mid")])
    assert est.div == 40.0 and est.points == 55
    assert "4 samples" in est.label and "2026-12-20" in est.label
