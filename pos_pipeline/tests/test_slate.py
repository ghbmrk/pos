import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_catalogue import Catalogue  # noqa: E402
from pos_pipeline import SlateError, parse_slate, validate_slate  # noqa: E402
from pos_pipeline.slate import _has_number  # noqa: E402
from pos_pipeline import data  # noqa: E402

E = lambda name, **kw: {"name": name, **kw}  # noqa: E731
FB = ["Spell", "Fire", "Projectile", "Damage"]


@pytest.fixture(scope="module")
def cat():
    return Catalogue({
        "pob_sha": "abc1234" + "0" * 33,
        "classes": [E("Witch", ascendancies=["Infernalist"]), E("Monk", ascendancies=["Invoker"]), E("Ranger", ascendancies=["Deadeye"])],
        "ascendancies": [E("Infernalist", **{"class": "Witch"}), E("Invoker", **{"class": "Monk"}), E("Deadeye", **{"class": "Ranger"})],
        "skills": [
            E("Fireball", id="FB", description="Launches a fiery projectile.", skill_types=FB),
            E("Frost Nova", id="FN", skill_types=["Spell", "Cold", "AreaSpell", "Nova", "Damage"]),
            E("Rolling Slam", id="RS", skill_types=["Attack", "Area", "Melee", "Physical", "Damage"]),
            E("Lightning Arrow", id="LA", skill_types=["Attack", "Lightning", "Projectile", "Damage"]),
            E("Raise Zombie", id="ZB", skill_types=["Minion", "CreatesMinion", "Spell"]),
        ],
        "supports": [
            E("Fire Mastery", id="SFM", family=["FM"], require_types=["Fire"], description="Supported skills deal more Fire damage."),
            E("Urgent Totems I", id="SUT", require_types=["SummonsTotem"], description="Totems are summoned faster."),
        ],
        "uniques": [E("Andvarius", base="Gold Ring", file="ring",
                      variants=["Current"], lines=[{"text": "Adds Fire damage to Spells"}, {"text": "Gain extra gold from monsters"}])],
        "bases": [E("Gold Ring", type="Ring")],
        "keystones": [E("Chaos Inoculation", ascendancy=None, stats=["Maximum Life is 1", "Immune to Chaos Damage"]),
                      E("Ancestral Bond", ascendancy=None, stats=["Your Totem Limit is doubled"]),
                      E("Resolute Technique", ascendancy=None, stats=["Your hits can't be Evaded", "Never deal Critical Hits"])],
        "notables": [E("Heart of Ice", ascendancy=None, stats=["Freeze buildup is increased"])],
    })


def spec(skill="Fireball", cls="Witch", asc="Infernalist", **fixed):
    return {"pob_sha": "abc1234", "class": cls, "ascendancy": asc, "level": 90, "main_skill": {"gem": skill},
            "tiers": ["mid"], "fixed": fixed}


def cand(name, sp, kp, **kw):
    c = {"name": name, "spec": sp, "key_pieces": kp,
         "claims": [{"text": "Immunity to chaos lets life stay low", "cites": [{"kind": "keystone", "id": "Chaos Inoculation", "quote": "Immune to Chaos Damage"}]}]}
    c.update(kw)
    return c


def good_slate():
    return {"slate": 1, "pob_sha": "abc1234", "prompt": "p", "brief": {"benchmarks": ["arbiter_ash"], "tiers": ["mid"]},
            "candidates": [
                cand("Fire Witch", spec(keystones=["Chaos Inoculation"]), [{"kind": "keystone", "id": "Chaos Inoculation"}]),
                cand("Frost Monk", spec("Frost Nova", "Monk", "Invoker", notables=["Heart of Ice"]), [{"kind": "notable", "id": "Heart of Ice"}],
                     claims=[{"text": "Freeze is easier to build", "cites": [{"kind": "notable", "id": "Heart of Ice", "quote": "Freeze buildup is increased"}]}]),
                cand("Slam Ranger", spec("Rolling Slam", "Ranger", "Deadeye", keystones=["Resolute Technique"]), [{"kind": "keystone", "id": "Resolute Technique"}],
                     claims=[{"text": "Hits are reliable but cannot crit", "cites": [{"kind": "keystone", "id": "Resolute Technique", "quote": "Never deal Critical Hits"}]}]),
            ]}


def run(cat, mutate=None):
    d = copy.deepcopy(good_slate())
    if mutate:
        mutate(d)
    return validate_slate(parse_slate(d), cat)


def codes(r):
    return {i.code for i in r.errors}


def test_good_slate_keeps_all(cat):
    r = run(cat)
    assert r.ok, [(c.name, [i.code for i in c.errors]) for c in r.candidates] + [i.code for i in r.issues]
    assert len(r.kept) == 3
    assert {c.vector["delivery"] for c in r.kept} == {"projectile", "area_spell", "melee"}
    assert {c.vector["damage"] for c in r.kept} == {"Fire", "Cold", "Physical"}


def test_unresolved_name_in_spec_and_cite_and_key_piece(cat):
    def m(d):
        d["candidates"][0]["spec"]["fixed"]["keystones"] = ["Eldritch Battery"]
        d["candidates"][0]["key_pieces"] = [{"kind": "keystone", "id": "Eldritch Battery"}]
        d["candidates"][0]["claims"][0]["cites"][0]["id"] = "Eldritch Battery"
    r = run(cat, m)
    c = r.candidates[0]
    assert not c.kept and {"unresolved"} <= codes(c)
    assert sum(i.code == "unresolved" for i in c.errors) == 3


def test_quote_must_be_poe2_text_substring_case_and_space_insensitive(cat):
    def good(d):
        d["candidates"][0]["claims"][0]["cites"][0]["quote"] = "immune  to   CHAOS damage"
    assert run(cat, good).candidates[0].kept

    def bad(d):
        d["candidates"][0]["claims"][0]["cites"][0]["quote"] = "Cannot be Stunned while at full life"
    c = run(cat, bad).candidates[0]
    assert not c.kept and "quote_mismatch" in codes(c)


def test_short_quote_rejected(cat):
    def m(d):
        d["candidates"][0]["claims"][0]["cites"][0]["quote"] = "Chaos"
    assert "quote_short" in codes(run(cat, m).candidates[0])


def test_claim_without_cite_rejected(cat):
    def m(d):
        d["candidates"][0]["claims"][0]["cites"] = []
    assert "claim_uncited" in codes(run(cat, m).candidates[0])


def test_claim_with_no_catalogue_text_rejected(cat):
    def m(d):
        d["candidates"][0]["claims"][0]["cites"] = [{"kind": "skill", "id": "Frost Nova", "quote": "creates a freezing nova"}]
    assert "claim_no_text" in codes(run(cat, m).candidates[0])


@pytest.mark.parametrize("text", ["Deals 40% more damage", "Doubles after 3 seconds", "Two totems share the boss", "Hits twice"])
def test_numbers_in_claims_rejected(cat, text):
    def m(d):
        d["candidates"][0]["claims"][0]["text"] = text
    assert "claim_number" in codes(run(cat, m).candidates[0])


def test_number_words_do_not_false_positive(cat):
    assert _has_number("Totem limit is doubled and cold gets stronger", data.ideation()["number_words"]) is None
    assert _has_number("Done in one hit", data.ideation()["number_words"]) == "one"


def test_quote_may_contain_numbers_from_catalogue(cat):
    def m(d):
        d["candidates"][0]["claims"][0]["cites"][0].update(kind="keystone", id="Chaos Inoculation", quote="Maximum Life is 1")
    assert run(cat, m).candidates[0].kept


def test_key_pieces_count_and_in_spec(cat):
    def none(d):
        d["candidates"][0]["key_pieces"] = []
    assert "key_pieces" in codes(run(cat, none).candidates[0])

    def many(d):
        d["candidates"][0]["key_pieces"] = [{"kind": "keystone", "id": "Chaos Inoculation"}, {"kind": "keystone", "id": "Ancestral Bond"},
                                            {"kind": "notable", "id": "Heart of Ice"}, {"kind": "unique", "id": "Andvarius"}]
    assert "key_pieces" in codes(run(cat, many).candidates[0])

    def absent(d):
        d["candidates"][0]["key_pieces"] = [{"kind": "keystone", "id": "Ancestral Bond"}]
    assert "key_piece_not_in_spec" in codes(run(cat, absent).candidates[0])

    def bad_kind(d):
        d["candidates"][0]["key_pieces"] = [{"kind": "skill", "id": "Fireball"}]
    assert "kind" in codes(run(cat, bad_kind).candidates[0])


def test_support_key_piece_matches_spec(cat):
    def m(d):
        d["candidates"][0]["spec"]["fixed"]["supports"] = ["Fire Mastery"]
        d["candidates"][0]["key_pieces"] = [{"kind": "support", "id": "Fire Mastery"}]
    assert run(cat, m).candidates[0].kept


def test_near_duplicate_rejected_later_one_only(cat):
    def m(d):
        twin = copy.deepcopy(d["candidates"][0])
        twin["name"] = "Fire Witch Again"
        d["candidates"].insert(1, twin)
    r = run(cat, m)
    assert [c.kept for c in r.candidates] == [True, False, True, True]
    assert "near_duplicate" in codes(r.candidates[1])


def test_differing_on_two_fields_passes(cat):
    def m(d):  # same class/skill/delivery/damage, different defence and key piece
        twin = copy.deepcopy(d["candidates"][0])
        twin["name"] = "Fire Witch CI"
        twin["spec"]["fixed"]["keystones"] = ["Ancestral Bond"]
        twin["key_pieces"] = [{"kind": "keystone", "id": "Ancestral Bond"}]
        twin["claims"] = [{"text": "More totems at once", "cites": [{"kind": "keystone", "id": "Ancestral Bond", "quote": "Totem Limit is doubled"}]}]
        twin["archetype"] = {"defence": "life"}
        d["candidates"].append(twin)
    r = run(cat, m)
    assert r.candidates[-1].kept


def test_one_field_difference_is_duplicate(cat):
    def m(d):
        twin = copy.deepcopy(d["candidates"][0])
        twin["name"] = "Fire Witch alt"
        twin["archetype"] = {"defence": "evasion"}
        d["candidates"].append(twin)
    assert not run(cat, m).candidates[-1].kept


def test_totem_support_changes_delivery(cat):
    def m(d):
        d["candidates"][0]["spec"]["fixed"]["supports"] = ["Urgent Totems I"]
    # Fireball cannot be supported by a totem support here (no SummonsTotem type), so the spec errors; delivery derivation is unit-level
    from pos_pipeline.slate import _derive_delivery
    cfg = data.ideation()
    assert _derive_delivery(cfg, {"skill_types": FB}, [{"require_types": ["SummonsTotem"]}]) == "totem"
    assert _derive_delivery(cfg, {"skill_types": FB}, []) == "projectile"


def test_coverage_needs_distinct_values_when_open(cat):
    def m(d):
        d["candidates"] = [d["candidates"][0],
                           cand("Fire Monk", spec(cls="Monk", asc="Invoker", keystones=["Chaos Inoculation"]), [{"kind": "keystone", "id": "Chaos Inoculation"}], archetype={"defence": "es"}),
                           cand("Fire Ranger", spec(cls="Ranger", asc="Deadeye", keystones=["Chaos Inoculation"]), [{"kind": "keystone", "id": "Chaos Inoculation"}], archetype={"defence": "evasion"})]
    r = run(cat, m)
    assert len(r.kept) == 3 and "coverage" in {i.code for i in r.issues} and not r.ok

    def fixed(d):
        m(d)
        d["brief"]["constraints"] = {"delivery": "projectile", "damage": "Fire"}
    assert run(cat, fixed).ok


def test_max_kept_cap(cat, monkeypatch):
    cfg = copy.deepcopy(data.ideation())
    cfg["slate"]["max_kept"] = 2
    monkeypatch.setattr(data, "ideation", lambda: cfg)
    r = run(cat)
    assert [c.kept for c in r.candidates] == [True, True, False]
    assert "over_cap" in codes(r.candidates[2])


def test_minion_skill_not_rankable(cat):
    def m(d):
        d["candidates"][0]["spec"]["main_skill"] = {"gem": "Raise Zombie"}
    c = run(cat, m).candidates[0]
    assert not c.kept and "no_metric" in codes(c)


def test_explicit_maximise_does_not_make_minion_rankable(cat):
    def m(d):
        d["candidates"][0]["spec"]["main_skill"] = {"gem": "Raise Zombie"}
        d["candidates"][0]["spec"]["objective"] = {"maximise": "TotalEHP"}
    assert "no_metric" in codes(run(cat, m).candidates[0])


def test_bad_spec_errors_are_prefixed_and_reject(cat):
    def m(d):
        d["candidates"][0]["spec"]["fixed"]["keystones"] = ["Chaos Inoculatoin"]
        d["candidates"][0]["key_pieces"] = [{"kind": "keystone", "id": "Chaos Inoculation"}]
    c = run(cat, m).candidates[0]
    assert not c.kept
    bad = next(i for i in c.errors if i.code == "unresolved")
    assert bad.path.startswith("candidates[0].spec.") and "Chaos Inoculation" in bad.suggestions


def test_brief_checks(cat):
    def m(d):
        d["brief"] = {"benchmarks": ["nope"], "tiers": ["nope"]}
    r = run(cat, m)
    assert {"benchmark", "tier"} <= {i.code for i in r.issues} and not r.ok


def test_pob_sha_mismatch_and_too_few_and_duplicate_names(cat):
    def m(d):
        d["pob_sha"] = "deadbee"
        d["candidates"] = d["candidates"][:1] + [copy.deepcopy(d["candidates"][0])]
    r = run(cat, m)
    assert {"pob_sha", "too_few", "duplicate"} <= {i.code for i in r.issues}


def test_declared_archetype_mismatch_is_warning_and_derived_wins(cat):
    def m(d):
        d["candidates"][0]["archetype"] = {"delivery": "totem", "damage": "cold", "engine": "shock"}
    c = run(cat, m).candidates[0]
    assert c.kept and c.vector["delivery"] == "projectile"
    assert {i.code for i in c.issues if i.severity == "warning"} >= {"archetype_derived"}


def test_source_format(cat):
    def ok(d):
        d["candidates"][0]["source"] = "sweep:probe1/keystone:Ancestral Bond"
    assert run(cat, ok).candidates[0].kept

    def bad(d):
        d["candidates"][0]["source"] = "gut feeling"
    assert "source" in codes(run(cat, bad).candidates[0])


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(slate=2),
    lambda d: d.pop("brief"),
    lambda d: d["candidates"][0].update(extra=1),
    lambda d: d["candidates"][0]["claims"][0].update(cites="x"),
    lambda d: d["candidates"][0]["archetype"].update(speed="fast") if "archetype" in d["candidates"][0] else d["candidates"][0].update(archetype={"speed": "f"}),
])
def test_structural_errors(mutate):
    d = copy.deepcopy(good_slate())
    mutate(d)
    with pytest.raises(SlateError):
        parse_slate(d)


def test_bad_spec_block_is_candidate_error_not_exception(cat):
    def m(d):
        d["candidates"][0]["spec"] = {"nonsense": 1}
    c = run(cat, m).candidates[0]
    assert not c.kept and "spec_structure" in codes(c)


def test_real_catalogue_poe1_name_and_true_quote():
    cat = Catalogue.load()
    d = {"slate": 1, "pob_sha": cat.pob_sha[:7], "prompt": "p", "brief": {"benchmarks": ["arbiter_ash"], "tiers": ["mid"]},
         "candidates": [{"name": "Totems", "spec": {"pob_sha": cat.pob_sha[:7], "class": "Sorceress", "ascendancy": "Stormweaver", "level": 90,
                                                   "main_skill": {"gem": "Spark"}, "tiers": ["mid"], "fixed": {"keystones": ["Ancestral Bond"]}},
                         "key_pieces": [{"kind": "keystone", "id": "Ancestral Bond"}],
                         "claims": [{"text": "More totems", "cites": [{"kind": "keystone", "id": "Ancestral Bond", "quote": "Your Totem Limit is doubled"}]},
                                    {"text": "PoE1 thing", "cites": [{"kind": "keystone", "id": "Mind Over Matter", "quote": "30% of damage is taken from mana first"}]}]}]}
    c = validate_slate(parse_slate(d), cat).candidates[0]
    assert not c.kept
    assert not any(i.path.endswith("claims[0].cites[0].quote") for i in c.errors)


def test_archetype_patterns_unknown_is_error_and_too_few_is_warning(cat):
    def unknown(d):
        d["candidates"][0]["archetype"] = {"patterns": "stat_stacking+cast_on_crit_strike"}
    c = run(cat, unknown).candidates[0]
    assert not c.kept and "unknown_pattern" in {i.code for i in c.errors}

    def one(d):
        d["candidates"][0]["archetype"] = {"patterns": "stat_stacking"}
    c = run(cat, one).candidates[0]
    assert c.kept and "engine_not_compounding" in {i.code for i in c.issues if i.severity == "warning"}

    def two(d):
        d["candidates"][0]["archetype"] = {"patterns": "conversion_funnel + resistance_removal"}
    c = run(cat, two).candidates[0]
    assert c.kept and not {i.code for i in c.issues} & {"unknown_pattern", "engine_not_compounding"}
