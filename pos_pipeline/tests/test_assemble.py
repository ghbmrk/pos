"""Assembler tests against the real engine and the committed catalogue (need LuaJIT: tools/build_luajit.sh)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_catalogue import Catalogue  # noqa: E402
from pos_engine.engine import PobEngine  # noqa: E402
from pos_pipeline.assemble import assemble, import_pob, unparsed_lines, variants  # noqa: E402
from pos_pipeline.spec import parse_spec  # noqa: E402

FIX = Path(__file__).resolve().parents[2] / "pos_engine/tests/fixtures/witchhunter_detonate.pobcode"


@pytest.fixture(scope="module")
def cat():
    return Catalogue.load()


@pytest.fixture(scope="module")
def eng():
    with PobEngine() as e:
        yield e


def spec_for(cat, **over):
    d = {"pob_sha": cat.pob_sha[:7], "class": "Sorceress", "ascendancy": "Stormweaver", "level": 90,
         "main_skill": {"gem": "Spark"}, "tiers": ["mid"]}
    d.update(over)
    return parse_spec(d)


def codes(a, sev=None):
    return {i.code for i in a.issues if sev is None or i.severity == sev}


def test_variants_cartesian():
    s = parse_spec({"pob_sha": "abcdef1", "class": "X", "level": 1, "main_skill": {"gem": "g"}, "tiers": ["a"],
                    "axes": {"ascendancy": ["A", "B"], "weapon_base": ["staff", "wand+focus"]}})
    v = variants(s)
    assert len(v) == 4 and {"ascendancy": "B", "weapon_base": "staff"} in v
    s.axes = {}
    assert variants(s) == [{}]


def test_assembles_skill_supports_passives_and_config(cat, eng):
    s = spec_for(cat, fixed={"supports": ["Controlled Destruction"], "keystones": ["Chaos Inoculation"]})
    a = assemble(s, cat, eng)
    assert a.ok, a.issues
    assert a.main_skill == "Spark" and a.xml.startswith("<")
    assert a.stats["TotalDPS"] > 0
    # config profile applied: Pinnacle enemy resists (50%) cut lightning DPS versus the Boss profile (30%)
    none = assemble(spec_for(cat, config_profile="boss", fixed={"supports": ["Controlled Destruction"], "keystones": ["Chaos Inoculation"]}), cat, eng)
    assert none.stats["TotalDPS"] > a.stats["TotalDPS"]


def test_variant_overrides_ascendancy_and_defers_weapon(cat, eng):
    s = spec_for(cat, axes={"ascendancy": ["Stormweaver", "Chronomancer"], "weapon_base": ["staff"]})
    a = assemble(s, cat, eng, {"ascendancy": "Chronomancer", "weapon_base": "staff"})
    assert a.ok and 'ascendClassName="Chronomancer"' in a.xml
    assert a.deferred_axes == {"weapon_base": "staff"}


def test_too_many_supports_is_an_error_from_pob_itself(cat, eng):
    ok = ["Arcane Surge", "Lifetap", "Blazing Critical", "Biting Frost I", "Admixture", "Arms Length"]
    assert all(cat.resolve("support", x).entry for x in ok)
    assert "pob_warning" not in codes(assemble(spec_for(cat, fixed={"supports": ok[:5]}), cat, eng))
    a = assemble(spec_for(cat, fixed={"supports": ok}), cat, eng)
    assert "pob_warning" in codes(a, "error")  # PoB's socketLimitWarning, so the 5 limit is PoB's own rule


def test_unknown_names_fail_with_suggestions_not_repairs(cat, eng):
    a = assemble(spec_for(cat, fixed={"keystones": ["Chaos Inoculatoin"]}), cat, eng)
    assert not a.ok and "unresolved" in codes(a) and a.xml == ""
    assert any("Chaos Inoculation" in i.suggestions for i in a.issues)


def test_unique_equipped_with_real_mods_and_unparsed_lines_surface(cat, eng):
    a = assemble(spec_for(cat, fixed={"uniques": ["Andvarius", "Ab Aeterno"]}), cat, eng)
    assert a.ok, a.issues
    assert 'Andvarius' in a.xml and 'Ab Aeterno' in a.xml
    unparsed = [i for i in a.issues if i.code == "unparsed_mod"]
    assert unparsed and all(i.severity == "warning" for i in unparsed)
    assert any("Dodge Roll" in i.message for i in unparsed)


def test_unparsed_line_detection_on_raw_items(eng):
    good = "Rarity: RARE\nHoof\nAshen Staff\n+50 to maximum Life\n"
    bad = good + "+10 to flibberty gibbet\n"
    assert unparsed_lines(eng, good) == []
    assert [u["line"] for u in unparsed_lines(eng, bad)] == ["+10 to flibberty gibbet"]
    with pytest.raises(ValueError):
        unparsed_lines(eng, "Rarity: RARE\nNope\nNot A Base\n+1 to life\n")
    # check_item must not leave the item equipped or in the build
    eng.new_build()
    unparsed_lines(eng, bad)
    assert eng.call("check_build")["items"] == []


def test_import_pob_roundtrips_to_a_spec_that_assembles(cat, eng):
    spec, issues = import_pob(FIX.read_text().strip(), cat, eng)
    assert spec.class_ == "Mercenary" and spec.ascendancy == "Witchhunter" and spec.level == 90
    assert cat.get("skill", spec.main_skill)["name"] == "Detonate Living"
    assert not [i for i in issues if i.severity == "error"]
    spec.tiers = ["mid"]
    a = assemble(spec, cat, eng)
    assert a.ok, a.issues
    assert a.main_skill == "Detonate Living"
