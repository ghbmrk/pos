"""Probes, calibration and diagnose (L2). Real engine; the fixture is the golden Spark pass-1 build (docs/loop.md 1.1)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_engine.engine import PobEngine  # noqa: E402
from pos_pipeline import diagnose as D  # noqa: E402
from pos_pipeline.sweep import Ablation, _verdict  # noqa: E402

GOLDEN = (Path(__file__).parent / "fixtures" / "spark_golden_pass1.xml").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def cal():
    return D.calibrate()


def test_every_probe_passes_calibration(cal):
    """A probe that fails (unparsed line, wrong sign, outside tolerance) is a lying lever: fix or drop it in data/probes.yaml."""
    assert {p["id"] for p in D.probes()} == set(cal)
    bad = {k: c.reason for k, c in cal.items() if not c.ok}
    assert not bad, bad


def test_probe_ids_unique_and_every_probe_has_a_calibration_case():
    ids = [p["id"] for p in D.probes()]
    assert len(ids) == len(set(ids))
    assert all(p.get("expect") for p in D.probes())


def test_costs_resolve_against_tiers_and_the_pinned_mod_index():
    from pos_tiers.resolver import default_index
    groups = default_index().groups
    for p in D.probes():
        if p.get("cost"):
            assert p["cost"]["group"] in groups, f"{p['id']}: affix group {p['cost']['group']!r} not in the pinned ModItem.lua"
            assert D.probe_cost(p) > 0
        else:
            assert D.probe_cost(p) is None


def test_the_unparsed_audit_line_is_dropped_by_pob_and_the_engine_says_so():
    """L0 audit lie 1: PoB drops 'Enemies have -10% to Lightning Resistance' silently; the engine now reports 0 parsed mods."""
    with PobEngine() as e:
        e.new_build(); e.paste_skill("Spark 20/0  1")
        assert e.set_config(custom_mods="Enemies have -10% to Lightning Resistance", keys=["FullDPS"])["customMods"]["count"] == 0
        assert e.set_config(custom_mods="10% more Damage", keys=["FullDPS"])["customMods"]["count"] == 1
    assert any(r["line"] == "Enemies have -10% to Lightning Resistance" for r in D.rejected())


def test_golden_diagnosis(cal):
    """The audit's golden build: TTK binds (4.7x the gate), crit and added damage lead, Rakiata's Flow flips enemy-resistance levers."""
    d = D.diagnose(GOLDEN, "FullDPS", ["arbiter_ash"], cal=cal)
    assert d.binding == "ttk@arbiter_ash" and d.constraints[0].pressure > 4
    assert not d.failed
    top = [p.id for p in d.top(4)]
    assert "crit_chance" in top
    by = {p.id: p for p in d.probes}
    assert by["crit_chance"].gains["dps"] == pytest.approx(0.218, abs=0.02)   # the audit's +10% crit = +43.6% is two of these steps
    assert by["enemy_res_all"].gains["dps"] < -0.05 and any("REVERSED" in n for n in by["enemy_res_all"].notes)   # audit lie 3: true, not a lie
    assert by["pen_lightning"].status == "inert"                                                                      # audit lie 2: inverted resistances negate penetration
    assert by["life"].gains["survive@arbiter_ash"] > 0 and by["life"].gains["ttk@arbiter_ash"] == 0


def test_a_failed_probe_is_excluded_never_zero(cal):
    bad = dict(cal)
    bad["crit_chance"] = D.Calibration("crit_chance", "x", parsed=True, ok=False, reason="forced")
    d = D.diagnose(GOLDEN, "FullDPS", [], cal=bad, only=["crit_chance", "more_damage"])
    assert [p.id for p in d.failed] == ["crit_chance"] and [p.id for p in d.probes] == ["more_damage"]
    assert d.failed[0].gains == {} and d.binding == "objective"


def test_diagnose_refuses_a_build_with_no_damage():
    with PobEngine() as e:
        e.new_build()
        xml = e.get_xml()
    with pytest.raises(ValueError):
        D.diagnose(xml, "FullDPS", [], cal={})


def _abl(base, v, ehp_base, ehp_v):
    a = Ablation({"kind": "notable", "id": "x"}, base, v, (base - v) / base, "not_testable", ehp_baseline=ehp_base, ehp_without=ehp_v)
    a.ehp_delta_rel = (ehp_base - ehp_v) / ehp_base
    return a


def test_ablation_verdict_uses_ehp_before_calling_a_piece_unmodelled():
    """L2 fix: removing Harmony Within raised EHP 17% with no damage change and was labelled possibly_unmodelled."""
    a = _abl(100.0, 100.0, 1000.0, 1170.0)
    _verdict(a, 100.0, 100.0, True, 0.10)
    assert a.verdict == "not_load_bearing" and "EHP" in a.note and "+17" in a.note
    b = _abl(100.0, 100.0, 1000.0, 1000.0)
    _verdict(b, 100.0, 100.0, True, 0.10)
    assert b.verdict == "possibly_unmodelled"
    c = _abl(100.0, 100.0, 1000.0, 700.0)
    _verdict(c, 100.0, 100.0, True, 0.10)
    assert c.verdict == "confirmed" and "survivability" in c.note
    d = _abl(100.0, 100.0, 1000.0, 1000.0)
    _verdict(d, 100.0, 100.0, False, 0.10)
    assert d.verdict == "not_load_bearing"            # no text and no change: a dud, not an engine gap
