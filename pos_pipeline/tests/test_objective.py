"""L1 objective: pure lexicographic scoring on synthetic PoB stats, and agreement with the benchmark ranking path."""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_pipeline import benchmarks as B  # noqa: E402
from pos_pipeline.objective import Objective, _shortfall  # noqa: E402

# max hit taken per damage type; arbiter_ash hits: chasm_slam 1761.9 phys + 755.1 fire, basic_attack smaller
SAFE = {"PhysicalMaximumHitTaken": 5000, "FireMaximumHitTaken": 5000, "FireResist": 75}
DEADLY = {"PhysicalMaximumHitTaken": 900, "FireMaximumHitTaken": 5000, "FireResist": 75}


def st(dps, **kw):
    return {"TotalDPS": dps, **kw}


def test_shortfall_is_a_fraction():
    assert _shortfall(75, 75) == 0 and _shortfall(80, 75) == 0
    assert _shortfall(50, 100) == pytest.approx(0.5)
    assert _shortfall(-20, 75) == 1.0 and _shortfall(0, 75) == 1.0            # clamped (hit margins)
    assert _shortfall(-30, 75, clamp=False) == pytest.approx(1.4)              # floors keep the gradient below zero


def test_negative_resist_still_has_a_gradient():
    o = Objective("TotalDPS", ["arbiter_ash"], floors={"FireResist": 75})
    lo = o.score([st(1_000, **{**SAFE, "FireResist": -60})])
    mid = o.score([st(1_000, **{**SAFE, "FireResist": -30})])
    assert mid.key > lo.key


def test_survival_outranks_damage():
    o = Objective("TotalDPS", ["arbiter_ash"])
    glass = o.score([st(10_000, **DEADLY)])
    tank = o.score([st(1_000, **SAFE)])
    assert glass.deficit > 0 and tank.deficit == 0
    assert tank.key > glass.key                         # lexicographic: constraint before goal
    assert dict(glass.parts)["survive:arbiter_ash"] > 0


def test_goal_is_log_ttk_and_ranks_like_dps_when_constraints_equal():
    o = Objective("TotalDPS", ["arbiter_ash"])
    a, b = o.score([st(1_000, **SAFE)]), o.score([st(2_000, **SAFE)])
    assert b.goal - a.goal == pytest.approx(math.log(2))   # twice the damage = half the TTK = +ln 2
    assert b.key > a.key
    r = B.boss_metrics("arbiter_ash", st(1_000, **SAFE))
    assert a.goal == pytest.approx(-math.log(r.ttk_s))


def test_floors_are_a_constraint_and_hard_ttk_is_optional():
    f = Objective("TotalDPS", ["arbiter_ash"], floors={"FireResist": 75})
    assert f.score([st(1_000, **{**SAFE, "FireResist": 40})]).deficit == pytest.approx(1 - 40 / 75)
    soft, hard = Objective("TotalDPS", ["arbiter_ash"]), Objective("TotalDPS", ["arbiter_ash"], hard_ttk=True)
    slow = st(1_000, **SAFE)                              # TTK far above the 60 s gate
    assert soft.score([slow]).deficit == 0 and hard.score([slow]).deficit > 0
    fast = st(1e7, **SAFE)
    assert hard.score([fast]).deficit == 0


def test_pack_goal_and_unsourced_hits_are_no_constraint():
    o = Objective("TotalDPS", ["arbiter_ash_uber", "breach_t15"])    # uber has unsourced life / hits
    s = o.score([st(1_000, **DEADLY), {"TotalDPS": 1_000, "AverageHit": 500, "AreaOfEffectRadiusMetres": 3, "Speed": 2}])
    assert "survive:arbiter_ash_uber" not in dict(s.parts)           # never a guess
    assert math.isfinite(s.goal)


def test_unknown_benchmark_is_an_error():
    with pytest.raises(ValueError, match="unknown benchmark"):
        Objective("TotalDPS", ["nope"])


def test_fights_carry_the_benchmark_options():
    o = Objective("TotalDPS", ["arbiter_ash", "breach_t15"])
    assert dict(o.fights[0].options)["enemyIsBoss"] == "Pinnacle" and dict(o.fights[1].options)["enemyIsBoss"] == "None"
    assert set(B.BENCH_KEYS) <= set(o.keys)


# ---- real engine: the stage score and the ranking path must agree --------------------------------------------
def _seed(cat, eng):
    from pos_pipeline.assemble import assemble
    from pos_pipeline.spec import parse_spec
    spec = parse_spec({"pob_sha": cat.pob_sha[:7], "class": "Sorceress", "ascendancy": "Stormweaver", "level": 90,
                       "main_skill": {"gem": "Spark"}, "tiers": ["mid"]})
    a = assemble(spec, cat, eng)
    assert a.ok, a.issues
    return a.xml


def test_engine_objective_matches_benchmark_evaluate_and_searches_run():
    from pos_catalogue import Catalogue
    from pos_engine.engine import PobEngine
    from pos_pipeline.gear import GearSearcher
    from pos_pipeline.supports import search_supports
    from pos_pool.pool import EnginePool, Job
    cat = Catalogue.load()
    o = Objective("FullDPS", ["arbiter_ash", "breach_t15"], floors={"FireResist": 75})
    with PobEngine() as eng, EnginePool(workers=2) as pool:
        xml = _seed(cat, eng)
        # same stats as benchmarks.evaluate (set_config mutation) and as the baked-XML path the gear fast path uses
        rs = pool.map([Job(xml, mutations=o.mutations(f), stat_keys=o.keys) for f in o.fights])
        s = o.score([r.stats for r in rs])
        ev = B.evaluate(pool, xml, "arbiter_ash", "FullDPS")
        assert ev.ttk_s == pytest.approx(B.boss_metrics("arbiter_ash", rs[0].stats, "FullDPS").ttk_s)
        gs = GearSearcher(cat, pool, eng, metric="FullDPS", objective=o)
        assert gs.key_of(xml) == pytest.approx(s.key)
        # supports: objective mode runs, keeps the fixed set, never loses to the baseline on the objective key
        sk = cat.resolve("skill", "Spark").entry["id"]
        r = search_supports(cat, pool, xml, sk, [], "FullDPS", slots=2, top=4, beam=2, objective=o)
        assert r.best.key >= r.baseline.key and r.best.key is not None
        # gear: one slot, objective scored; key never below the unmodded base
        got = gs.best_item(xml, "weapon", "Acrid Wand", 20.0)
        base = gs.score(xml, "weapon", [gs.raw("Acrid Wand", [])])[0]
        assert got[1] >= base
