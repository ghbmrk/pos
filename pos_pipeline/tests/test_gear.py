"""Gear search tests: pure helpers, plus the real engine, pool and committed catalogue (need LuaJIT)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_catalogue import Catalogue  # noqa: E402
from pos_engine.engine import PobEngine  # noqa: E402
from pos_pipeline.assemble import assemble  # noqa: E402
from pos_pipeline.gear import (ITEM_LEVEL, MAX_PREFIX, MAX_SUFFIX, GearSearcher, _Floors,  # noqa: E402
                               roll_line, spawnable)
from pos_pipeline.spec import parse_spec  # noqa: E402
from pos_pool.pool import EnginePool  # noqa: E402
from pos_tiers.resolver import ModIndex, default_index  # noqa: E402

BASES = {"weapon": "Acrid Wand", "body_armour": "Abyssal Cuirass", "amulet": "Absent Amulet"}


def test_roll_line():
    assert roll_line("(10-20)% increased Spell Damage") == "15% increased Spell Damage"
    assert roll_line("Adds (1-3) to (10-12) Lightning Damage", 1.0) == "Adds 3 to 12 Lightning Damage"
    assert roll_line("(1.5-2.5)% of Damage Leeched", 0.5) == "2% of Damage Leeched"
    assert roll_line("+4 to Level of all Spell Skills") == "+4 to Level of all Spell Skills"


def test_spawnable_first_matching_tag_decides():
    m = {"keys": ["str_armour", "body_armour", "default"], "vals": [0, 1, 0]}
    assert not spawnable(m, ["body_armour", "str_armour", "default"])  # str_armour listed first -> 0
    assert spawnable(m, ["body_armour", "int_armour", "default"])
    assert not spawnable(m, ["ring", "default"])


def test_floors_deficit():
    f = _Floors({"FireResist": 75, "Int": "ReqInt"})
    assert f.deficit({"FireResist": 70, "Int": 100, "ReqInt": 90}) == 5
    assert f.deficit({"FireResist": 80, "Int": 50, "ReqInt": 90}) == 40
    assert set(f.keys) == {"FireResist", "Int", "ReqInt"}


@pytest.fixture(scope="module")
def cat():
    return Catalogue.load()


@pytest.fixture(scope="module")
def eng():
    with PobEngine() as e:
        yield e


@pytest.fixture(scope="module")
def pool():
    with EnginePool(workers=2) as p:
        yield p


@pytest.fixture(scope="module")
def seed(cat, eng):
    spec = parse_spec({"pob_sha": cat.pob_sha[:7], "class": "Sorceress", "ascendancy": "Stormweaver", "level": 90,
                       "main_skill": {"gem": "Spark"}, "tiers": ["budget"]})
    a = assemble(spec, cat, eng)
    assert a.ok, a.issues
    return a.xml


def test_unparsed_mods_are_never_offered(cat, pool, eng):
    real = default_index().mods
    mods = {k: v for k, v in real.items() if v["group"] == "WeaponSpellDamage"}
    mods["PosBogus1"] = {"type": "Prefix", "level": 1, "group": "PosBogus", "affix": "", "keys": ["wand"], "vals": [1],
                         "text": ["Your spells summon a friendly dragon"]}
    g = GearSearcher(cat, pool, eng, index=ModIndex(mods), metric="FullDPS", unique_prices={})
    opts = g.affix_options(BASES["weapon"])
    assert "PosBogus" not in opts and "WeaponSpellDamage" in opts
    assert g.rejected == ["PosBogus1"]


def test_search_improves_and_respects_budget_and_rules(cat, pool, eng, seed):
    g = GearSearcher(cat, pool, eng, metric="FullDPS", shortlist=5, unique_prices={})
    slots = ("weapon", "amulet")
    r = g.search(seed, "budget", BASES, slots=slots, passes=1, realloc_rounds=1)
    assert r.value > r.baseline > 0
    start = sum(g.t.slot_budget("budget", s) for s in slots)
    assert abs(sum(r.slot_budgets.values()) - start) < 1e-6        # reallocation conserves points
    idx = default_index().mods
    for s in slots:
        it = r.items[s]
        assert it.points <= r.slot_budgets[s] + 1e-9
        assert it.points == pytest.approx(sum(g.t.affix_points(a.group, a.rank) for a in it.affixes))
        assert len({a.group for a in it.affixes}) == len(it.affixes)
        assert sum(a.type == "Prefix" for a in it.affixes) <= MAX_PREFIX
        assert sum(a.type == "Suffix" for a in it.affixes) <= MAX_SUFFIX
        assert all(idx[a.mod_id]["level"] <= ITEM_LEVEL for a in it.affixes)
        assert eng.call("check_item", raw=it.raw)["unparsed"] == []
    assert r.items["weapon"].affixes, "a spell wand at the budget tier should take at least one affix"
    assert r.price is not None and r.price.points == pytest.approx(sum(r.items[s].points for s in slots))
    eng.load_build_xml(r.xml)  # the returned build holds the chosen items
    assert eng.get_stats(["FullDPS"])["stats"]["FullDPS"] == pytest.approx(r.value)


def test_floor_ranks_ahead_of_metric(cat, pool, eng, seed):
    # Seed fire resistance is -50; a floor of -20 needs about +30 from the amulet, which DPS alone would never buy.
    g = GearSearcher(cat, pool, eng, metric="FullDPS", floors={"FireResist": -20}, shortlist=4, unique_prices={})
    r = g.search(seed, "mid", BASES, slots=("amulet",), passes=1, realloc_rounds=0)
    assert r.floors_met, (r.deficit, r.items["amulet"].affixes)
    assert any(a.group == "FireResistance" or "Resist" in a.group for a in r.items["amulet"].affixes)


def test_priced_unique_is_considered_within_budget(cat, pool, eng, seed):
    g = GearSearcher(cat, pool, eng, metric="FullDPS", unique_prices={"Astramentis": "cheap"})
    u, obj = g._best_unique(seed, "amulet", budget=10)
    assert u is not None and u.unique == "Astramentis" and obj is not None
    assert u.points == g.t.raw["unique_bands"]["cheap"]["points"]
    assert g._best_unique(seed, "amulet", budget=1) == (None, None)     # band costs more than the budget
    assert g._best_unique(seed, "weapon", budget=None) == (None, None)  # not a weapon
