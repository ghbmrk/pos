"""I13: declared conditions are credited only in the fights where they can hold (`fights` in config_profiles.yaml)."""
from pos_pipeline import data


def test_trash_conditions_are_pack_only():
    table = data.conditions()
    assert table["corpses_nearby"]["fights"] == ["pack"]
    assert table["killed_recently"]["fights"] == ["pack"]
    assert all(set(c.get("fights") or ["boss", "pack"]) <= {"boss", "pack"} for c in table.values())


def test_off_options_switch_off_only_the_off_fight_conditions():
    names = ["corpses_nearby", "enemy_shocked", "killed_recently"]
    off, dropped = data.conditions_not_in_fight(names, "boss")
    assert dropped == ["corpses_nearby", "killed_recently"]
    assert off == {"multiplierNearbyCorpse": 0, "conditionKilledRecently": False}
    assert data.conditions_not_in_fight(names, "pack") == ({}, [])


def test_glory_support_is_gated_like_triggered_ones():
    """I13: PoB has no Glory, so Zerphi's Infamy reads as free damage; the support search and ablation skip it."""
    from pos_catalogue import Catalogue
    from pos_pipeline.supports import eligible, has_unmodelled_cost
    cat = Catalogue.load(pob_sha="601768b")
    z = cat.get("support", cat.resolve("support", "Zerphi's Infamy").entry["id"])
    assert has_unmodelled_cost(z)
    skill = cat.get("skill", cat.resolve("skill", "Boneshatter").entry["id"])
    assert z["id"] in {s["id"] for s in eligible(cat, skill, [])}
    assert z["id"] not in {s["id"] for s in eligible(cat, skill, [], allow_triggered=())}


def test_use_condition_supports_are_unmodelled_costs():
    from pos_catalogue import Catalogue
    from pos_pipeline.supports import has_unmodelled_cost
    cat = Catalogue.load(pob_sha="601768b")
    get = lambda n: cat.get("support", cat.resolve("support", n).entry["id"])
    assert all(has_unmodelled_cost(get(n)) for n in ["Hit and Run", "Ancestral Aid", "Catharsis", "Zerphi's Infamy"])
    assert not any(has_unmodelled_cost(get(n)) for n in ["Garukhan's Resolve", "Daresso's Passion", "Brutality III"])
