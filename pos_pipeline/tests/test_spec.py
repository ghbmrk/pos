import copy
import re
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_catalogue import Catalogue  # noqa: E402
from pos_pipeline import SpecError, validate  # noqa: E402
from pos_pipeline import data  # noqa: E402
from pos_pipeline.spec import parse_spec  # noqa: E402

E = lambda name, **kw: {"name": name, **kw}  # noqa: E731


@pytest.fixture(scope="module")
def cat():
    return Catalogue({
        "pob_sha": "abc1234" + "0" * 33,
        "classes": [E("Witch", ascendancies=["Infernalist"]), E("Monk", ascendancies=["Invoker"])],
        "ascendancies": [E("Infernalist", **{"class": "Witch"}), E("Invoker", **{"class": "Monk"})],
        "skills": [
            E("Fireball", id="FireballPlayer", gem_id="G/Fireball", skill_types=["Spell", "Fire", "Projectile", "Damage"]),
            E("Raise Zombie", id="ZombiePlayer", skill_types=["Minion", "CreatesMinion", "Spell"]),
            E("Herald", id="HeraldPlayer", skill_types=["Buff", "Persistent"]),
            E("Mana Tempest", id="MTPlayer", skill_types=["Spell", "Damage"]),
            E("Spiritual Cry", id="SCPlayer", skill_types=["Spell", "Meta", "Damage"]),
        ],
        "supports": [
            E("Fire Mastery", id="SupFM", family=["FM"], require_types=["Fire"], exclude_types=["Minion"], tags="Fire"),
            E("Fire Mastery II", id="SupFM2", family=["FM"], require_types=["Fire"]),
            E("Needs Charge", id="SupNC", require_types=["ConsumesCharges"]),
            E("Gives Charge", id="SupGC", require_types=["Fire"], add_types=["ConsumesCharges"]),
            E("Command", id="SupCmd", tags="Minion, Command"),
            E("A", id="A"), E("B", id="B"), E("C", id="C"), E("D", id="D"), E("F", id="F"),
        ],
        "uniques": [E("Andvarius", base="Gold Ring"), E("Grand Spectrum", base="Ruby"), E("Grand Spectrum", base="Emerald")],
        "bases": [E("Gold Ring", type="Ring"), E("Oak Staff", type="Staff"), E("Wand", type="Wand"), E("Fo", type="Focus")],
        "keystones": [E("Chaos Inoculation", ascendancy=None, stats=["Maximum Life is 1"])],
        "notables": [E("Heart of Ice", ascendancy=None, stats=[]),
                     E("Gift", ascendancy="Invoker", stats=["Grants Skill: Unbound"])],
    })


BASE = {
    "pob_sha": "abc1234", "class": "Witch", "ascendancy": "Infernalist", "level": 90,
    "main_skill": {"gem": "Fireball"}, "tiers": ["starter", "mid"],
}


def run(cat, **over):
    d = copy.deepcopy(BASE)
    d.update(over)
    return validate(parse_spec(d), cat)


def codes(rep, sev="error"):
    return {i.code for i in rep.issues if i.severity == sev}


def test_valid_spec_gets_metric_and_profile_hash(cat):
    rep = run(cat, axes={"ascendancy": ["Infernalist"], "weapon_base": ["staff", "wand+focus"]})
    assert rep.ok, rep.errors
    assert rep.metric == "FullDPS" and rep.profile_hash == data.profile_hash("pinnacle_boss")


def test_gem_id_accepted_and_unknown_name_suggests(cat):
    assert run(cat, main_skill={"gem": "G/Fireball"}).ok
    rep = run(cat, main_skill={"gem": "Fire ball"})
    (i,) = [i for i in rep.errors if i.code == "unresolved"]
    assert i.suggestions[0] == "Fireball"


def test_support_gem_as_main_skill(cat):
    assert "support_as_skill" in codes(run(cat, main_skill={"gem": "Fire Mastery"}))


def test_pin_class_ascendancy_level(cat):
    assert "pob_sha" in codes(run(cat, pob_sha="deadbee"))
    assert "pob_sha" in codes(run(cat, pob_sha="abc"))  # too short to pin
    assert "ascendancy_class" in codes(run(cat, ascendancy="Invoker"))
    assert "level" in codes(run(cat, level=0)) and "level" in codes(run(cat, level=101))


def test_support_type_rules_and_add_types(cat):
    assert "support_incompatible" in codes(run(cat, fixed={"supports": ["Needs Charge"]}))
    # Gives Charge adds ConsumesCharges, which Needs Charge requires: accepted in either order
    assert run(cat, fixed={"supports": ["Needs Charge", "Gives Charge"]}).ok
    assert run(cat, fixed={"supports": ["Gives Charge", "Needs Charge"]}).ok
    assert "support_incompatible" in codes(run(cat, main_skill={"gem": "Raise Zombie"}, fixed={"supports": ["Fire Mastery"]}))


def test_support_family_duplicate_and_socket_limit(cat):
    assert "support_family" in codes(run(cat, fixed={"supports": ["Fire Mastery", "Fire Mastery II"]}))
    assert "duplicate" in codes(run(cat, fixed={"supports": ["A", "A"]}))
    rep = run(cat, fixed={"supports": ["A", "B", "C", "D", "F", "Fire Mastery"]})
    assert "socket_limit" in codes(rep, "warning") and rep.ok  # unverified limit is a warning


def test_minion_support_on_non_minion_skill_warns(cat):
    rep = run(cat, fixed={"supports": ["Command"]})
    assert "minion_support" in codes(rep, "warning") and rep.ok


def test_fixed_names_resolve_and_ambiguity_reported(cat):
    assert "unresolved" in codes(run(cat, fixed={"keystones": ["Chaos Inocculation"]}))
    rep = run(cat, fixed={"uniques": ["Grand Spectrum"]})
    assert [i for i in rep.errors if i.code == "ambiguous"][0].suggestions
    assert "duplicate" in codes(run(cat, fixed={"uniques": ["Andvarius", "andvarius"]}))


def test_ascendancy_notable_must_match_class_ascendancy(cat):
    assert "notable_ascendancy" in codes(run(cat, fixed={"notables": ["Gift"]}))
    assert "notable_ascendancy" not in codes(run(cat, fixed={"notables": ["Gift"]}, ascendancy="Infernalist",
                                                 axes={"ascendancy": ["Infernalist", "Invoker"]}))


def test_axes(cat):
    assert "axis" in codes(run(cat, axes={"flask": ["x"]}))
    assert "ascendancy_class" in codes(run(cat, axes={"ascendancy": ["Invoker"]}))
    rep = run(cat, axes={"weapon_base": ["stafff"]})
    assert "unresolved" in codes(rep)
    assert "duplicate" in codes(run(cat, axes={"weapon_base": ["staff", "staff"]}))


def test_tiers_and_profile(cat):
    assert "tier" in codes(run(cat, tiers=["starter", "godly"]))
    assert "duplicate" in codes(run(cat, tiers=["mid", "mid"]))
    rep = run(cat, config_profile="nope")
    assert "config_profile" in codes(rep) and rep.profile_hash is None


def test_metric_mapping_and_unmapped_skills_fail_loudly(cat):
    assert run(cat, main_skill={"gem": "Mana Tempest"}).metric == "TotalDPS"
    assert run(cat, main_skill={"gem": "Fireball"}).metric == "FullDPS"
    assert "no_metric" in codes(run(cat, main_skill={"gem": "Raise Zombie"}))
    assert "no_metric" in codes(run(cat, main_skill={"gem": "Herald"}))
    rep = run(cat, main_skill={"gem": "Raise Zombie"}, objective={"maximise": "TotalEHP"})
    assert rep.ok and rep.metric == "TotalEHP"
    assert "metric" in codes(run(cat, objective={"maximise": "Vibes"}))


def test_floors(cat):
    assert run(cat, objective={"floors": {"resist_capped": True, "TotalEHP": "tier_default", "Life": 3000}}).ok
    assert "floor" in codes(run(cat, objective={"floors": {"nonsense": 1}}))
    assert "floor" in codes(run(cat, objective={"floors": {"resist_capped": 3}}))
    assert "floor" in codes(run(cat, objective={"floors": {"Life": "high"}}))


def test_limitations_are_warnings_with_confidence(cat):
    rep = run(cat, main_skill={"gem": "Mana Tempest"})
    lim = [i for i in rep.warnings if i.code == "limitation"]
    assert lim and lim[0].confidence == "verified" and "Mana Tempest" in lim[0].message
    sus = run(cat, main_skill={"gem": "Spiritual Cry"})
    assert [i.confidence for i in sus.warnings if i.code == "limitation"] == ["suspected"]
    grants = run(cat, ascendancy="Infernalist", axes={"ascendancy": ["Infernalist", "Invoker"]}, fixed={"notables": ["Gift"]})
    assert any(i.confidence == "suspected" and "grants a skill" in i.message for i in grants.warnings)
    assert not [i for i in run(cat).warnings if i.code == "limitation"]


@pytest.mark.parametrize("bad", [
    {"nope": 1}, {"level": "90"}, {"level": True}, {"main_skill": "Fireball"}, {"tiers": "mid"},
    {"fixed": {"gems": []}}, {"objective": {"x": 1}}, {"axes": []}, {"pob_sha": 601768},
])
def test_structural_errors_raise(bad):
    d = copy.deepcopy(BASE)
    d.update(bad)
    with pytest.raises(SpecError):
        parse_spec(d)


def test_missing_required_key():
    d = copy.deepcopy(BASE)
    del d["tiers"]
    with pytest.raises(SpecError):
        parse_spec(d)


def test_profile_hash_is_stable_and_distinguishes():
    assert data.profile_hash("boss") == data.profile_hash("boss")
    assert len({data.profile_hash(p) for p in data.profiles()}) == len(data.profiles())


def test_stat_keys_match_engine_wrapper():
    lua = (Path(__file__).resolve().parents[2] / "pos_engine" / "pob_headless.lua").read_text()
    block = re.search(r"DEFAULT_STATS = \{(.*?)\}", lua, re.S).group(1)
    assert set(re.findall(r'"(\w+)"', block)) == set(data.metrics()["stat_keys"])


def test_data_files_are_well_formed():
    for r in data.metrics()["rules"]:
        assert r["metric"] is None or r["metric"] in data.metrics()["stat_keys"]
    for lim in data.limitations():
        assert lim["confidence"] in ("verified", "suspected") and len(lim["match"]) == 1
    assert set(data.rules()["axes"]) >= {"ascendancy"}


def test_real_catalogue_smoke():
    try:
        real = Catalogue.load()
    except FileNotFoundError:
        pytest.skip("no catalogue")
    spec = parse_spec({**BASE, "pob_sha": real.pob_sha[:7], "ascendancy": "Infernalist",
                       "main_skill": {"gem": "Detonate Dead"}, "fixed": {"supports": ["Abiding Hex"]},
                       "axes": {"weapon_base": ["staff", "wand+focus"]}})
    rep = validate(spec, real)
    assert [i.code for i in rep.errors] == ["support_incompatible"]
    assert rep.metric == "TotalDPS"
