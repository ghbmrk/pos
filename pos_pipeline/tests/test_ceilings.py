"""L5b uptime ceilings (docs/ceilings.md). Real engine; builds are made in-engine."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_catalogue.catalogue import Catalogue  # noqa: E402
from pos_engine.engine import PobEngine  # noqa: E402
from pos_pipeline import ceilings as C  # noqa: E402
from pos_pipeline.sweep import equip_probe_weapon  # noqa: E402

# the 15 unparsed census lines of the five families (census/spark_golden, pin 601768b) and the entry each must reach
CENSUS = {
    "If you would gain a Charge, Allies in your Presence gain that Charge instead": "charges_to_allies",
    "Gain Power Charges instead of Frenzy Charges": "power_charges_max",
    "Gain Frenzy Charges instead of Endurance Charges": "frenzy_charges_max",
    "Gain Endurance Charges instead of Power Charges": "endurance_charges_max",
    "10% chance when you gain a Frenzy Charge to gain an additional Frenzy Charge": "frenzy_charges_max",
    "Skills have 10% chance to not remove Charges but still count as consuming them": "charges_kept",
    "You can have two Companions of different types": "second_companion",
    "Allies in your Presence have 30% increased Glory generation": "companion_side",
    "Culling Strike against Beasts while your Companion is in your Presence": "companion_side",
    "Minions Revive 35% faster if all your Minions are Companions": "companion_side",
    "Life Recovery from your Flasks also applies to your Companions": "companion_side",
    "Leeching Life from your Hits causes your Companion to also Leech the same amount of Life": "companion_side",
    "Remnants can be collected from 50% further away": "remnant_rate",
    "10% chance to create an additional Remnant": "remnant_rate",
    "Remnants you create reappear once, 3 seconds after being collected": "remnant_rate",
    "Sealed Skills have 25% increased Seal gain frequency": "seal_frequency",
    "When collecting an Elemental Infusion, gain another different Elemental Infusion": "infusion_consumed",
}


def test_registry_is_well_formed():
    assert C.validate_registry() == []


@pytest.mark.parametrize("line,eid", CENSUS.items())
def test_every_census_line_reaches_its_entry(line, eid):
    assert eid in [e["id"] for e in C.match(line)], line


def test_break_even_algebra():
    assert C.break_even(100, 300, 200) == {"uptime": 0.5, "verdict": "reachable"}
    assert C.break_even(100, 300, 90) == {"uptime": 0.0, "verdict": "already_met"}
    assert C.break_even(100, 300, 400)["verdict"] == "never"
    assert C.break_even(100, 100, 120) == {"uptime": None, "verdict": "never"}


def test_assumption_zero_reproduces_the_pure_number_and_one_the_ceiling():
    assert C.at_uptime(100.0, 250.0, 0.0) == 100.0
    assert C.at_uptime(100.0, 250.0, 1.0) == 250.0
    with pytest.raises(ValueError):
        C.at_uptime(100.0, 250.0, 1.2)


def test_spender_data_reads_pobs_skill_data_once_per_stat():
    sd = C.spender_data("Falling Thunder")
    assert sd["types"] == ["Power"]
    assert C._damage_stats(sd["stats"], "Power") == (50.0, 100.0, ["lightning_strike_damage_+%_final_when_charged", "lightning_strike_damage_+%_final_per_power_charge"])
    assert C.spender_data("Spiral Volley")["types"] == ["Frenzy"]
    assert C.spender_data("No Such Skill")["found"] is False


# ---- engine -----------------------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def builds():
    cat = Catalogue.load()
    out = {}
    with PobEngine() as e:
        for name, cls, base, skill in (("spiral", "Monk", "Adherent Bow", "Spiral Volley 20/0 1"),
                                       ("thunder", "Monk", "Aegis Quarterstaff", "Falling Thunder 20/0 1")):
            e.new_build(); e.set_class(cls); e.set_level(90)
            xml = equip_probe_weapon(cat, e, e.get_xml(), base)
            e.load_build_xml(xml); e.paste_skill(skill)
            out[name] = e.get_xml()
        e.new_build(); e.set_class("Witch"); e.set_level(90); e.paste_skill("Fireball 20/0 1")
        e.set_config(custom_mods="20% more Damage per Frenzy Charge\n15% more Damage if you have consumed an Elemental Infusion recently")
        out["state"] = e.get_xml()
        e.new_build(); e.set_class("Witch"); e.set_level(90); e.paste_skill("Fireball 20/0 1")
        out["plain"] = e.get_xml()
    return out


def test_derivation_reproduces_pobs_native_figure_for_spiral_volley(builds):
    """The method is calibrated on the one spender PoB computes itself: derived lines on a no-charge build = PoB with charges set."""
    with PobEngine() as e:
        sd = C.spender_data("Spiral Volley")
        lines, used = C.derived_lines(e, builds["spiral"], "TotalDPS", sd)
        assert used and len(lines) == 2
        native, _ = C._apply(e, builds["spiral"], "TotalDPS", {"useFrenzyCharges": True}, None, None)
        derived, cnt = C._apply(e, builds["spiral"], "TotalDPS", None, "\n".join(lines), None)
        assert cnt == 2
        assert derived == pytest.approx(native, rel=1e-9)


def test_native_spender_is_modelled_confirmed_not_a_gap(builds):
    r = C.evaluate(builds["spiral"], ["charge_spenders"], metric="TotalDPS")[0]
    assert r.status == "native" and r.ceiling > r.floor * 4 and r.compounding


def test_unmoved_spender_gets_a_derived_ceiling_and_a_label(builds):
    r = C.evaluate(builds["thunder"], ["charge_spenders"], metric="TotalDPS")[0]
    assert r.status == "derived" and r.ceiling > r.floor and "upper bound" in r.note
    assert r.applied["from_stats"]


def test_state_entries_move_only_where_the_build_reads_the_state(builds):
    rs = {r.id: r for r in C.evaluate(builds["state"], ["frenzy_charges_max", "power_charges_max", "infusion_consumed", "charges_kept"], metric="TotalDPS")}
    assert rs["frenzy_charges_max"].ceiling == pytest.approx(rs["frenzy_charges_max"].floor * 1.6, rel=1e-6)
    assert rs["power_charges_max"].status == "inert" and rs["power_charges_max"].ceiling == rs["power_charges_max"].floor
    assert rs["infusion_consumed"].headroom == pytest.approx(1.15, rel=1e-6) and not rs["infusion_consumed"].compounding
    assert rs["charges_kept"].ceiling == rs["frenzy_charges_max"].ceiling


def test_assumption_zero_ceiling_free_entries_reproduce_the_floor(builds):
    rs = C.evaluate(builds["plain"], ["companion_side", "remnant_rate", "charges_to_allies", "second_companion"], metric="TotalDPS")
    assert [r.status for r in rs] == ["no_own_damage", "no_own_damage", "no_own_damage", "needs_data"]
    assert all(r.ceiling == r.floor for r in rs[:3]) and rs[3].ceiling is None


def test_seal_line_is_rewritten_to_the_wording_pob_parses(builds):
    r = C.evaluate(builds["plain"], ["seal_frequency"], metric="TotalDPS", lines={"seal_frequency": "Sealed Skills have 40% increased Seal gain frequency"})[0]
    assert r.status == "inert"   # parsed (not "dropped"), but no Unleash-supported skill in this build reads it
    assert "40%" in r.applied["custom_mods"]


def test_joint_ceiling_counts_overlapping_states_once(builds):
    rs = C.evaluate(builds["state"], ["frenzy_charges_max", "charges_kept", "infusion_consumed"], metric="TotalDPS")
    j = C.interaction(rs, builds["state"], metric="TotalDPS")
    assert j["skipped_overlapping"] == ["charges_kept"]
    assert j["joint"] == pytest.approx(rs[0].floor * 1.6 * 1.15, rel=2e-3) and j["synergy"] > 0   # multiplicative: more than the sum


def test_unknown_id_is_an_error(builds):
    with pytest.raises(ValueError):
        C.evaluate(builds["plain"], ["nope"])
