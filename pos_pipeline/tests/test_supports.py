"""Support search tests: pure eligibility logic, plus the real engine and committed catalogue (need LuaJIT)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_catalogue import Catalogue  # noqa: E402
from pos_engine.engine import PobEngine  # noqa: E402
from pos_pipeline.assemble import assemble  # noqa: E402
from pos_pipeline.spec import parse_spec  # noqa: E402
from pos_pipeline.supports import compatible, effective_types, eligible, search_supports  # noqa: E402
from pos_pool.pool import EnginePool  # noqa: E402


@pytest.fixture(scope="module")
def cat():
    return Catalogue.load()


def sup(cat, name):
    return cat.resolve("support", name).entry


def test_eligibility_rules():
    skill = {"skill_types": ["Spell", "Lightning"]}
    a = {"id": "a", "require_types": ["Spell"], "family": ["F"]}
    b = {"id": "b", "family": ["F"]}
    c = {"id": "c", "require_types": ["Attack"]}
    d = {"id": "d", "require_types": ["Chaos"]}
    e = {"id": "e", "add_types": ["Chaos"]}
    assert compatible(skill, [a])
    assert not compatible(skill, [a, a])          # duplicate
    assert not compatible(skill, [a, b])          # shared family
    assert not compatible(skill, [c])             # type requirement unmet
    assert effective_types(skill, [d, e]) >= {"Chaos"}  # add_types applies regardless of order
    assert not compatible(skill, [d])


@pytest.fixture(scope="module")
def seed(cat):
    spec = parse_spec({"pob_sha": cat.pob_sha[:7], "class": "Sorceress", "ascendancy": "Stormweaver", "level": 90,
                       "main_skill": {"gem": "Spark"}, "tiers": ["mid"]})
    with PobEngine() as eng:
        a = assemble(spec, cat, eng)
    assert a.ok, a.issues
    return a.xml


def test_search_beats_baseline_and_respects_rules(cat, seed):
    skill = cat.resolve("skill", "Spark").entry
    fixed = [sup(cat, "Controlled Destruction")["id"]]
    with EnginePool(workers=2) as pool:
        r = search_supports(cat, pool, seed, skill["id"], fixed, "TotalDPS", slots=3, top=6, beam=3)
        again = search_supports(cat, pool, seed, skill["id"], fixed, "TotalDPS", slots=3, top=6, beam=3)
    assert r.best.value > r.baseline.value and r.gain > 0
    assert r.best.supports[0] == fixed[0] and len(r.best.supports) <= 3
    assert compatible(skill, [cat.get("support", i) for i in r.best.supports])
    assert r.singles[0][1] >= r.singles[-1][1] or r.singles[-1][1] is None
    # no eligible candidate is one already fixed or family-clashing with it
    ids = {s["id"] for s in eligible(cat, skill, [sup(cat, "Controlled Destruction")])}
    assert fixed[0] not in ids and all(i in ids for i, _ in r.singles)
    assert again.best.supports == r.best.supports and again.cached == again.evals


def test_pob_ignores_duplicates_so_search_must_exclude_them(cat, seed):
    """Documents the PoB behaviour in docs/supports.md: a duplicate support counts as socketed but adds nothing."""
    from pos_pool.pool import Job
    from pos_pipeline.assemble import _gem_line
    cd = sup(cat, "Controlled Destruction")["name"]
    mk = lambda n: Job(seed, (("paste_skill", {"text": "\n".join([_gem_line("Spark")] + [_gem_line(cd)] * n)}),), ("TotalDPS",))
    with EnginePool(workers=1) as pool:
        one, two = pool.map([mk(1), mk(2)])
    assert one.stats["TotalDPS"] == two.stats["TotalDPS"]


def test_no_free_slots_returns_baseline(cat, seed):
    skill = cat.resolve("skill", "Spark").entry
    with EnginePool(workers=1) as pool:
        r = search_supports(cat, pool, seed, skill["id"], [], "TotalDPS", slots=0)
    assert r.best is r.baseline and r.evals == 1
