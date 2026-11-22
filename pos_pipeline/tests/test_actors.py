"""Second-actor tests (K1, docs/second-actor.md). Pure tests use a fake registry; the PoB key check needs LuaJIT."""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_pipeline import SpecError, actors, data, validate  # noqa: E402
from pos_pipeline.spec import parse_spec  # noqa: E402
from pos_pipeline.tests.test_spec import BASE, cat  # noqa: E402,F401  (fixture reuse)

COMP = {"kind": "squire", "skills": [{"gem": "Fireball", "supports": ["Fire Mastery"]}], "gear": {"weapon": "Oak Staff"}}


def spec(**over):
    d = copy.deepcopy(BASE)
    d.update(over)
    return parse_spec(d)


def codes(rep):
    return {i.code for i in rep.errors}


@pytest.fixture
def fake_registry(monkeypatch):
    reg = {"squire": {"status": "available", "requires": {"class": "Witch", "ascendancy": "Infernalist"},
                      "gear_slots": ["weapon"], "max_skills": 1, "model": "separate_build",
                      "skill_effects": {"FireballPlayer": [
                          {"effect": "power_charges", "params": {"count": 3}, "uptime": 0.5, "source": "test"},
                          {"effect": "enemy_on_shocked_ground", "source": "test"}]}}}
    monkeypatch.setattr(data, "actors", lambda: reg)
    return reg


# ---- schema ------------------------------------------------------------------------------------------------
def test_companion_parses():
    s = spec(companion=COMP)
    assert s.companion.kind == "squire" and s.companion.skills[0].supports == ["Fire Mastery"]
    assert s.companion.gear == {"weapon": "Oak Staff"}
    assert spec().companion is None


@pytest.mark.parametrize("bad", [
    {"kind": ""}, {"kind": "squire", "extra": 1}, {"kind": "squire", "skills": "Fireball"},
    {"kind": "squire", "skills": [{"supports": []}]}, {"kind": "squire", "gear": ["weapon"]},
    {"kind": "squire", "skills": [{"gem": "x", "level": 3}]},
])
def test_companion_structural_errors(bad):
    with pytest.raises(SpecError):
        spec(companion=bad)


# ---- validator ---------------------------------------------------------------------------------------------
def test_real_squire_is_pending_and_fails_loudly(cat):  # noqa: F811
    rep = validate(spec(companion=COMP), cat)
    msg = [i.message for i in rep.errors if i.code == "actor_unavailable"]
    assert msg and "Squire gear slots" in msg[0]
    assert "actor_requires" in codes(rep)          # real squire needs Duelist/Knight


def test_unknown_kind(cat):  # noqa: F811
    assert "actor_kind" in codes(validate(spec(companion={**COMP, "kind": "golem"}), cat))


def test_available_actor_checks(cat, fake_registry):  # noqa: F811
    assert codes(validate(spec(companion=COMP), cat)) == set()
    bad = {"kind": "squire", "gear": {"helmet": "Oak Staff", "weapon": "Nope"},
           "skills": [{"gem": "Fireball", "supports": ["Fire Mastery", "Fire Mastery II", "Needs Charge"]},
                      {"gem": "Firebal"}]}
    rep = validate(spec(companion=bad), cat)
    assert {"companion_slot", "unresolved", "support_family", "support_incompatible", "companion_skills"} <= codes(rep)
    paths = {i.path for i in rep.errors}
    assert "companion.skills[0].supports[1]" in paths and "companion.skills[1].gem" in paths


def test_actor_requires_every_variant(cat, fake_registry):  # noqa: F811
    s = spec(companion=COMP, axes={"ascendancy": ["Infernalist"]})
    assert "actor_requires" not in codes(validate(s, cat))
    fake_registry["squire"]["requires"]["ascendancy"] = "Lich"
    assert "actor_requires" in codes(validate(s, cat))


# ---- effects -----------------------------------------------------------------------------------------------
def test_pending_actor_raises_everywhere():
    comp = spec(companion=COMP).companion
    with pytest.raises(actors.ActorUnavailable, match="Squire gear slots"):
        actors.effects_for(comp, ["FireballPlayer"])
    m = actors.model_for("squire")
    assert isinstance(m, actors.PendingActorModel)
    with pytest.raises(actors.ActorUnavailable):
        m.evaluate("<x/>", None, [])


def test_effects_from_registry_only(fake_registry):
    comp = spec(companion=COMP).companion
    eff = actors.effects_for(comp, ["FireballPlayer", "Unlisted"])
    assert [e.id for e in eff] == ["power_charges", "enemy_on_shocked_ground"]
    assert eff[0].options == {"usePowerCharges": True, "overridePowerCharges": 3} and eff[0].uptime == 0.5
    with pytest.raises(NotImplementedError):
        actors.model_for("squire")


def test_make_effect_validation():
    with pytest.raises(KeyError):
        actors.make_effect("cyclone_storm")
    with pytest.raises(ValueError):
        actors.make_effect("power_charges")             # missing count
    with pytest.raises(ValueError):
        actors.make_effect("banner_planted", {"count": 1})
    with pytest.raises(ValueError):
        actors.make_effect("banner_planted", uptime=0)


def test_merge_and_conflicts():
    a = actors.make_effect("power_charges", {"count": 2})
    b = actors.make_effect("enemy_on_shocked_ground")
    assert actors.merge_options({"enemyIsBoss": "Pinnacle"}, [a, b]) == {
        "enemyIsBoss": "Pinnacle", "usePowerCharges": True, "overridePowerCharges": 2, "conditionEnemyOnShockedGround": True}
    assert "overridePowerCharges" not in actors.merge_options({}, [a, b], include=["enemy_on_shocked_ground"])
    with pytest.raises(actors.EffectConflict):
        actors.merge_options({}, [a, actors.make_effect("power_charges", {"count": 3})])
    with pytest.raises(actors.EffectConflict):
        actors.merge_options({"conditionEnemyOnShockedGround": False}, [b])
    assert actors.merge_options({}, [a, a]) == actors.merge_options({}, [a])


def test_blend():
    assert actors.blend(200.0, 100.0, 0.25) == 125.0
    with pytest.raises(ValueError):
        actors.blend(1, 0, 1.5)


def test_registry_well_formed():
    eff = data.actor_effects()
    for k, a in data.actors().items():
        assert a["status"] in ("pending", "available")
        if a["status"] == "pending":
            assert a.get("unknowns"), f"{k}: a pending actor must list what blocks it"
        for sid, lst in (a.get("skill_effects") or {}).items():
            for e in lst:
                assert e["effect"] in eff and e.get("source"), f"{k}/{sid}: effect must exist and be sourced"
    for k, e in eff.items():
        placeholders = {v[1:-1] for v in e["options"].values() if isinstance(v, str) and v.startswith("{")}
        assert placeholders == set(e.get("params") or []), k


# ---- against the pinned PoB --------------------------------------------------------------------------------
def test_effect_option_keys_exist_in_pinned_pob():
    eng_mod = pytest.importorskip("pos_engine.engine")
    try:
        eng = eng_mod.PobEngine()
    except Exception as ex:  # noqa: BLE001
        pytest.skip(f"engine unavailable: {ex}")
    with eng:
        eng.new_build()
        keys = {k for e in data.actor_effects().values() for k in e["options"]}
        found = set()
        for k in keys:
            r = eng.list_config_options(query=k, limit=200)
            found |= {o.get("var") for o in r.get("options", [])}
        assert keys <= found, f"not PoB config keys: {sorted(keys - found)}"
