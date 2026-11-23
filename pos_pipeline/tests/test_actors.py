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
                      "gear_slots": ["weapon"], "min_skills": 1, "max_skills": 1, "model": "separate_build",
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


@pytest.mark.parametrize("skills", [[], [{"gem": "Fireball"}, {"gem": "Fireball"}]])
def test_companion_takes_exactly_one_skill_group(cat, fake_registry, skills):  # noqa: F811
    rep = validate(spec(companion={**COMP, "skills": skills}), cat)
    msg = [i.message for i in rep.errors if i.code == "companion_skills"]
    assert msg and "exactly 1" in msg[0] and f"spec lists {len(skills)}" in msg[0]


def test_real_squire_skill_count_is_one_and_sourced():
    sq = data.actors()["squire"]
    assert sq["min_skills"] == sq["max_skills"] == 1
    assert "cmsg_01RxGYnd78N9kMbbAJ5pWDhUBsXA8kfFPvTNvep5sCDPmY" in sq["skills_source"]


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
    fake_registry["squire"]["model"] = "native_pob"
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
        used = set().union(*(actors.placeholders(v) for v in e["options"].values()))
        assert used == set(e.get("params") or []), k


# ---- against the pinned PoB --------------------------------------------------------------------------------
def test_effect_option_keys_exist_in_pinned_pob():
    eng_mod = pytest.importorskip("pos_engine.engine")
    try:
        eng = eng_mod.PobEngine()
    except Exception as ex:  # noqa: BLE001
        pytest.skip(f"engine unavailable: {ex}")
    with eng:
        eng.new_build()
        keys = {k for e in data.actor_effects().values() for k in e["options"]} - {actors.CUSTOM_MODS}   # a config input, not an option
        found = set()
        for k in keys:
            r = eng.list_config_options(query=k, limit=200)
            found |= {o.get("var") for o in r.get("options", [])}
        assert keys <= found, f"not PoB config keys: {sorted(keys - found)}"


# ---- K2: separate_build model, orchestrator wiring, report -------------------------------------------------------
from types import SimpleNamespace as NS  # noqa: E402


def _eff(*specs):
    return [actors.make_effect(i, p, u, "test") for i, p, u in specs]


def _metric(xml, opts):
    """Fake player: 100 base, +50 with shocked ground, +20 per power charge."""
    return 100 + (50 if opts.get("conditionEnemyOnShockedGround") else 0) + 20 * (opts.get("overridePowerCharges") or 0)


def test_separate_build_on_off_and_blend():
    m = actors.SeparateBuildModel("squire", _metric, lambda x: 7.0)
    c = m.evaluate("m", "c", _eff(("enemy_on_shocked_ground", None, 1.0)))
    assert (c.main, c.without_companion, c.companion, c.total, c.blended) == (150, 100, 7.0, 157.0, False)
    c = m.evaluate("m", "c", _eff(("power_charges", {"count": 3}, 0.5), ("enemy_on_shocked_ground", None, 1.0)))
    assert c.main == pytest.approx(0.5 * 210 + 0.5 * 150) and c.blended
    c = m.evaluate("m", None, _eff(("power_charges", {"count": 3}, 0.25), ("enemy_on_shocked_ground", None, 0.5)))
    exp = sum(wp * ws * (100 + 60 * p + 50 * sh) for p, wp in ((1, .25), (0, .75)) for sh, ws in ((1, .5), (0, .5)))
    assert c.main == pytest.approx(exp) and c.companion == 0.0


def test_separate_build_conflict_with_profile_is_error_and_too_many_partial():
    m = actors.SeparateBuildModel("squire", _metric, None, base={"conditionEnemyOnShockedGround": False})
    with pytest.raises(actors.EffectConflict):
        m.evaluate("m", None, _eff(("enemy_on_shocked_ground", None, 1.0)))
    many = _eff(*[(e, None, 0.5) for e in ("enemy_on_shocked_ground", "enemy_on_chilled_ground", "enemy_on_scorched_ground",
                                           "enemy_on_brittle_ground", "enemy_on_sapped_ground")])
    with pytest.raises(ValueError, match="at most"):
        actors.SeparateBuildModel("squire", _metric).evaluate("m", None, many)


def test_reset_options_goes_back_to_profile_or_off():
    e = _eff(("power_charges", {"count": 3}, 1.0), ("banner_planted", None, 1.0))
    assert actors.reset_options({"bannerPlanted": True}, e) == {"usePowerCharges": False, "overridePowerCharges": 0, "bannerPlanted": True}


def test_text_templates_custom_mods_and_enemy_res_reset():
    a = actors.make_effect("ally_increased_damage", {"pct": 50})
    s = actors.make_effect("companion_takes_hit_damage", {"pct": 15, "life": 4050})
    assert a.options == {"customMods": "50% increased Damage"} and s.options["TotalCompanionLife"] == 4050
    m = actors.merge_options({}, [a, s, a])
    assert m["customMods"].split("\n") == ["50% increased Damage", "15% of Damage from Hits is taken from your Damageable Companion's Life before you"]
    r = actors.make_effect("enemy_lightning_res", {"value": -45})
    assert r.options == {"enemyLightningResist": -45}
    assert actors.reset_options({"enemyIsBoss": "Boss"}, [r, a]) == {"enemyIsBoss": "Boss", "customMods": ""}
    assert actors.reset_options({}, [r]) == {"enemyIsBoss": "Pinnacle"}
    assert actors.reset_options({"enemyLightningResist": 10}, [r]) == {"enemyLightningResist": 10}


def test_model_for_pending_stub_and_available(fake_registry):
    assert isinstance(actors.model_for("squire", player_metric=_metric), actors.SeparateBuildModel)
    with pytest.raises(ValueError):
        actors.model_for("squire")


def test_pending_squire_stays_loud_in_run():
    from pos_pipeline.orchestrate import run
    s = spec(companion=COMP)
    with pytest.raises(actors.ActorUnavailable, match="pending"):
        run(s, NS(actor=None), metric="FullDPS", slots=1, workers=1, skill_id="x", dry_run=True)
    with pytest.raises(actors.ActorUnavailable):
        actors.model_for("squire").evaluate("m", None, [])


def test_run_wires_actor_stage_and_report(fake_registry, tmp_path):
    from pos_pipeline.orchestrate import Stages, run
    from pos_pipeline.report import render_markdown
    s = spec(companion=COMP, tiers=["mid"])
    s.companion.kind = "squire"
    eff = _eff(("power_charges", {"count": 3}, 0.5), ("enemy_on_shocked_ground", None, 1.0))
    m = actors.SeparateBuildModel("squire", _metric, lambda x: 7.0)
    item = NS(unique=None, affixes=[], base="B")
    st = Stages(lambda v: NS(ok=True, xml="<x>", issues=[], deferred_axes={}),
                lambda xml, sk: NS(best=NS(supports=[]), gain=0.0, notes=[]), lambda xml, sk, ids: xml,
                lambda xmls: [NS(ok=True, xml=x, error="", gain=0.0, points_used=0, notes=[]) for x in xmls],
                lambda xml, tier, v: NS(value=100.0, baseline=1.0, xml=xml, items={"weapon": item}, price=NS(label="p"),
                                        floors_met=True, evals=1, notes=[]),
                actor=lambda xml, v: m.evaluate(xml, "<c>", eff))
    r = run(s, st, metric="FullDPS", slots=1, workers=1, skill_id="x", out_dir=tmp_path)
    ac = r.seeds[0].tiers["mid"].actor
    assert ac["main"] == pytest.approx(180) and ac["companion"] == 7.0 and ac["without_companion"] == 100 and ac["blended"]
    md = (tmp_path / "report.md").read_text()
    assert "with effects" in md and "without companion" in md and "power_charges x0.5" in md and "separate_build" in md
    # no actor stage while a companion is declared: loud
    with pytest.raises(actors.ActorUnavailable):
        run(s, Stages(st.assemble, st.supports, st.apply_supports, st.trees, st.gear),
            metric="FullDPS", slots=1, workers=1, skill_id="x")


def test_custom_mods_replace_and_clear_on_a_saved_build():
    """A build saved while custom mods were set carries them as a PoB custom-mod block; set_config must replace and
    clear that block, or an effect's 'off' state silently keeps it (found in the channel runs, 2026-11-23)."""
    eng_mod = pytest.importorskip("pos_engine.engine")
    from pos_catalogue import Catalogue
    from pos_pipeline.assemble import assemble
    from pos_pipeline.gear import GearSearcher
    from pos_pipeline.spec import load_spec
    from pathlib import Path
    sp = load_spec(Path(__file__).resolve().parents[2] / "examples" / "squire_assumed_ground.yaml")
    try:
        eng = eng_mod.PobEngine()
    except Exception as ex:  # noqa: BLE001
        pytest.skip(f"engine unavailable: {ex}")
    with eng:
        c = Catalogue.load(pob_sha=sp.pob_sha)
        a = assemble(sp, c, eng, {})
        eng.load_build_xml(a.xml)
        eng.add_item(GearSearcher(c, None, eng, metric="TotalDPS").raw("Akoyan Spear", []), slot="Weapon 1")

        def dps(xml, opts):
            eng.load_build_xml(xml)
            eng.set_config(options=opts)
            return float(eng.get_stats(["TotalDPS"])["stats"]["TotalDPS"])

        plain = eng.get_xml()
        eng.set_config(options={"customMods": "50% increased Damage"})
        baked = eng.get_xml()
        off, on = dps(plain, {"customMods": ""}), dps(plain, {"customMods": "50% increased Damage"})
        assert on > off
        assert dps(baked, {"customMods": ""}) == pytest.approx(off)
        assert dps(baked, {"customMods": "50% increased Damage"}) == pytest.approx(on)
