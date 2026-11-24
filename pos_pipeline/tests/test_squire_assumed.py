"""ASSUMED Squire what-if tests (K5, docs/squire-assumed.md). Pure tests need no engine; the probe test needs LuaJIT."""
import copy
import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_pipeline import SpecError, actors, data, validate  # noqa: E402
from pos_pipeline.gear import SLOTS  # noqa: E402
from pos_pipeline.spec import parse_spec  # noqa: E402
from pos_pipeline.tests.test_spec import BASE, cat  # noqa: E402,F401  (fixture reuse)

COMP = {"kind": "squire", "assumed": {"scenario": "charge_provider"}, "skills": [{"gem": "Fireball"}], "gear": {"weapon": "Oak Staff"}}


def spec(comp=COMP, **over):
    d = copy.deepcopy(BASE)
    d.update(over)
    d["companion"] = comp
    return parse_spec(d)


def codes(rep, sev="error"):
    return {i.code for i in (rep.errors if sev == "error" else rep.issues if sev == "all" else [])}


# ---- schema and validator ------------------------------------------------------------------------------------
def test_assumed_parses_and_defaults_off():
    assert spec().companion.assumed == {"scenario": "charge_provider"}
    plain = dict(COMP); plain.pop("assumed")
    assert spec(plain).companion.assumed is None


@pytest.mark.parametrize("bad", [{"scenario": ""}, {"scenario": "x", "uptime": 0}, {"scenario": "x", "uptime": 1.5},
                                 {"scenario": "x", "other": 1}, {"uptime": 0.5}, "ground_painter"])
def test_assumed_structural_errors(bad):
    with pytest.raises(SpecError):
        spec({**COMP, "assumed": bad})


def test_without_opt_in_squire_stays_pending(cat):  # noqa: F811
    plain = dict(COMP); plain.pop("assumed")
    assert "actor_unavailable" in codes(validate(spec(plain), cat))


def test_with_opt_in_validator_passes_with_banner_warning(cat):  # noqa: F811
    rep = validate(spec(), cat)
    assert not {"actor_unavailable", "actor_requires", "actor_kind"} & codes(rep), [i.message for i in rep.errors]
    w = [i for i in rep.issues if i.code == "actor_assumed"]
    assert w and w[0].severity == "warning" and "ASSUMED SQUIRE WHAT-IF" in w[0].message


def test_unknown_scenario_and_slot_errors(cat):  # noqa: F811
    assert "assumed_scenario" in codes(validate(spec({**COMP, "assumed": {"scenario": "nope"}}), cat))
    assert "companion_slot" in codes(validate(spec({**COMP, "gear": {"ring_1": "Oak Staff"}}), cat))


def test_assumed_squire_needs_a_skill_but_takes_several(cat):  # noqa: F811
    """The overlay keeps the registry's count: at least one skill, several allowed (owner, 2026-11-24)."""
    assert "companion_skills" in codes(validate(spec({**COMP, "skills": []}), cat))
    two = [{"gem": "Fireball"}, {"gem": "Fireball"}]
    assert "companion_skills" not in codes(validate(spec({**COMP, "skills": two}), cat))
    assert actors.actor("squire", {"scenario": "debuff_bot"})["max_skills"] is None


def test_assumed_only_for_the_squire():
    with pytest.raises(KeyError, match="unknown actor kind"):
        actors.actor("other", {"scenario": "ground_painter"})
    with pytest.raises(KeyError, match="only for 'squire'"):
        actors.assumed_scenario("other", {"scenario": "ground_painter"})


# ---- the data file -----------------------------------------------------------------------------------------------
def test_assumed_profile_is_labelled_and_well_formed():
    prof, eff = data.squire_assumed(), data.actor_effects()
    assert "ASSUMED" in prof["banner"] and prof["assumptions"] and prof["standins"]
    assert all(x["id"] and x["text"] and x["check"] for x in prof["assumptions"])
    a = prof["actor"]
    assert set(a["gear_slots"]) <= set(SLOTS) and 0 < a["budget_share"] < 1 and a["status"] == "available"
    assert data.actors()["squire"]["status"] == "pending", "the real registry must stay pending"
    for sid, sc in prof["scenarios"].items():
        assert sc["idea"] and isinstance(sc["effects"], list)
        for e in sc["effects"]:
            assert e["effect"] in eff, (sid, e)
            assert e["source"].startswith("ASSUMED"), f"{sid}/{e['effect']}: every assumed effect is labelled"
            assert e["probe"] in ("moves", "needs_consumer"), (sid, e["effect"])
            actors.make_effect(e["effect"], e.get("params"), e.get("uptime", 1.0))   # params and uptime valid


def test_effects_for_assumed_scenario_and_uptime_override():
    c = spec().companion
    eff = actors.effects_for(c, [])
    assert {e.id for e in eff} == {"frenzy_charges", "power_charges"} and all(e.source.startswith("ASSUMED") for e in eff)
    assert {e.uptime for e in eff} == {0.6}
    c.assumed = {"scenario": "charge_provider", "uptime": 0.25}
    assert {e.uptime for e in actors.effects_for(c, [])} == {0.25}


# ---- run gating, labelling, quarantine ------------------------------------------------------------------------------
def _stages(sp):
    from pos_pipeline.orchestrate import Stages
    eff = actors.effects_for(sp.companion, [])
    m = actors.SeparateBuildModel("squire", lambda x, o: 100.0 + 10 * len(o), lambda x: 7.0, assumed=sp.companion.assumed["scenario"])
    item = NS(unique=None, affixes=[], base="B")
    return Stages(lambda v: NS(ok=True, xml="<x>", issues=[], deferred_axes={}),
                  lambda xml, sk: NS(best=NS(supports=[]), gain=0.0, notes=[]), lambda xml, sk, ids: xml,
                  lambda xmls: [NS(ok=True, xml=x, error="", gain=0.0, points_used=0, notes=[]) for x in xmls],
                  lambda xml, tier, v: NS(value=100.0, baseline=1.0, xml=xml, items={"weapon": item}, price=NS(label="p"),
                                          floors_met=True, evals=1, notes=[]),
                  actor=lambda xml, v: m.evaluate(xml, "<c>", eff))


def test_run_needs_explicit_opt_in_and_labels_every_output(tmp_path):
    from pos_pipeline.orchestrate import AssumedNotAllowed, run
    sp = spec(tiers=["mid"])
    with pytest.raises(AssumedNotAllowed, match="allow_assumed"):
        run(sp, _stages(sp), metric="FullDPS", slots=1, workers=1, skill_id="x")
    run(sp, None, metric="FullDPS", slots=1, workers=1, skill_id="x", dry_run=True)       # preflight needs no opt-in
    r = run(sp, _stages(sp), metric="FullDPS", slots=1, workers=1, skill_id="x", allow_assumed=True, out_dir=tmp_path)
    assert r.seeds[0].tiers["mid"].actor["assumed"] == "charge_provider"
    md = (tmp_path / "report.md").read_text()
    assert md.startswith("# ASSUMED SQUIRE WHAT-IF") and "ASSUMED SQUIRE WHAT-IF: the Squire's gear slots" in md
    assert "Assumptions" in md and "Stand-ins" in md and "combined (ASSUMED)" in md and "(ASSUMED Squire what-if)" in md
    assert "ASSUMED companion squire" in md
    j = json.loads((tmp_path / "run.json").read_text())
    assert j["meta"]["assumed"]["scenario"] == "charge_provider"
    db = sqlite3.connect(tmp_path / "results.sqlite")
    assert db.execute("select assumed from tier_runs").fetchall() == [("charge_provider",)]
    assert "ASSUMED SQUIRE" in db.execute("select value from meta where key='ASSUMED'").fetchone()[0]


def test_normal_run_rows_are_not_flagged(tmp_path):
    from pos_pipeline.orchestrate import run
    sp = parse_spec(copy.deepcopy(BASE) | {"tiers": ["mid"]})
    st = _stages(spec(tiers=["mid"]))
    st.actor = None
    run(sp, st, metric="FullDPS", slots=1, workers=1, skill_id="x", out_dir=tmp_path)
    assert sqlite3.connect(tmp_path / "results.sqlite").execute("select assumed from tier_runs").fetchall() == [(None,)]
    assert "ASSUMED" not in (tmp_path / "report.md").read_text()


def test_slate_rejects_assumed_candidates():
    from pos_pipeline.tests import test_slate as ts
    d = ts.good_slate()
    d["candidates"][0]["spec"]["companion"] = COMP
    r = ts.validate_slate(ts.parse_slate(d), ts.cat.__wrapped__() if hasattr(ts.cat, "__wrapped__") else ts.cat)
    assert "assumed_in_slate" in {i.code for c in r.candidates for i in c.errors}


def test_mcp_hides_refuses_and_flags_assumed_runs(tmp_path, monkeypatch):
    from pos_mcp import core
    monkeypatch.setenv("POS_RUNS_DIR", str(tmp_path))
    for name, meta in (("r1", {}), ("r2", {"assumed": "ground_painter"})):
        d = tmp_path / name
        d.mkdir()
        (d / "meta.json").write_text(json.dumps({"pid": 0, "started": 0, "job": "run", "report": "report.md", "estimate": "", **meta}))
        (d / "report.md").write_text("x")
        (d / "run.json").write_text(json.dumps({"metric": "FullDPS", "seeds": []}))
    shown = core.list_runs(10)
    assert [r["run_id"] for r in shown["runs"]] == ["r1"] and shown["hidden_assumed"] == 1
    allr = core.list_runs(10, include_assumed=True)
    assert [r.get("ASSUMED") for r in allr["runs"]] == [None, "ground_painter"]
    assert not core.compare("r1", "r2")["ok"] and "ASSUMED" in core.compare("r1", "r2")["error"]
    ok = core.compare("r1", "r2", include_assumed=True)
    assert ok["ok"] and "ASSUMED" in ok
    refused = core.start_run({"pob_sha": "601768b", "class": "Huntress", "level": 90, "main_skill": {"gem": "Whirling Slash"}, "tiers": ["mid"],
                              "companion": {"kind": "squire", "assumed": {"scenario": "ground_painter"}, "skills": [{"gem": "Whirling Slash"}],
                                            "gear": {"weapon": "Akoyan Spear"}}}, {"weapon": "Akoyan Spear"})
    assert not refused["ok"] and "allow_assumed" in refused["hint"]


# ---- K3 wiring: the assumed overlay reaches the two-gear-set search ---------------------------------------------------------
def test_two_actor_search_runs_only_with_the_overlay():
    from pos_pipeline.tests.test_gear_actors import BASE as BASES, FakeSearcher
    from pos_pipeline.gear_actors import search_two_actors
    with pytest.raises(actors.ActorUnavailable):
        search_two_actors(FakeSearcher(1.0), FakeSearcher(1.0), "", "", "mid", BASES, {"weapon": "wbase", "body_armour": "bbase"},
                          slots=("weapon", "amulet"))
    r = search_two_actors(FakeSearcher(1.0), FakeSearcher(1.0), "", "", "mid", BASES, {"weapon": "wbase", "body_armour": "bbase"},
                          slots=("weapon", "amulet"), comp_slots=("weapon", "body_armour"), assumed={"scenario": "ground_painter"})
    assert r.share == data.squire_assumed()["actor"]["budget_share"] and any(k.startswith("squire.") for k in r.items)


# ---- PoB gate check (docs/theorycraft-squire.md section 6): effects must move a probe build that has no source of them ----------
def test_assumed_effects_move_a_probe_build():
    eng_mod = pytest.importorskip("pos_engine.engine")
    from pos_catalogue import Catalogue
    from pos_pipeline.assemble import assemble
    from pos_pipeline.gear import GearSearcher
    from pos_pipeline.spec import load_spec
    sp = load_spec(Path(__file__).resolve().parents[2] / "examples" / "squire_assumed_ground.yaml")
    try:
        eng = eng_mod.PobEngine()
    except Exception as ex:  # noqa: BLE001
        pytest.skip(f"engine unavailable: {ex}")
    with eng:
        c = Catalogue.load(pob_sha=sp.pob_sha)
        a = assemble(sp, c, eng, {})
        assert a.ok
        eng.load_build_xml(a.xml)
        eng.add_item(GearSearcher(c, None, eng, metric="TotalDPS").raw("Akoyan Spear", []), slot="Weapon 1")
        xml = eng.get_xml()
        base = data.profiles()[sp.config_profile].get("options") or {}

        def dps(opts):
            eng.load_build_xml(xml)
            eng.set_config(options=opts or None)
            return float(eng.get_stats(["TotalDPS"])["stats"]["TotalDPS"])

        assert dps({}) > 0
        for sid, sc in data.squire_assumed()["scenarios"].items():
            for e in sc["effects"]:
                ef = actors.make_effect(e["effect"], e.get("params"), 1.0)
                off, on = dps(actors.reset_options(base, [ef])), dps(ef.options)
                if e["probe"] == "moves":
                    assert on > off, f"{sid}/{e['effect']} does not move a probe build: PoB gates it behind a player-side source"
                else:
                    assert on == off, f"{sid}/{e['effect']} now moves the probe: relabel it `moves`"
