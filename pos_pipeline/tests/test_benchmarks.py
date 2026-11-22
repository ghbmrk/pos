"""Benchmark tests: YAML shape and sourcing, pure metric maths on synthetic stats, and one real-engine round trip."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pos_pipeline import benchmarks as B  # noqa: E402
from pos_pipeline import data  # noqa: E402


def test_benchmarks_are_well_formed_and_labelled():
    for bid, b in B.benchmarks().items():
        errors, _ = B.validate_benchmark(bid)
        assert errors == [], errors
        assert b["patch"]


def test_unknown_benchmark_reported():
    errors, _ = B.validate_benchmark("nope")
    assert errors and "known:" in errors[0]


def test_every_number_has_a_source_and_nulls_are_listed():
    _, un = B.validate_benchmark("arbiter_ash_uber")
    assert "arbiter_ash_uber.life" in un
    _, un = B.validate_benchmark("breach_t15")
    assert un == []                                                         # B3b sourced Magic/Rare life mults
    # a cell without a source is a structural error
    b = B.benchmarks()["arbiter_ash"]
    old = b["life"]
    b["life"] = {"value": 1}
    try:
        assert any("life" in e for e in B.validate_benchmark("arbiter_ash")[0])
    finally:
        b["life"] = old


def test_bench_keys_are_engine_stat_keys():
    assert set(B.BENCH_KEYS) <= set(data.metrics()["stat_keys"])


def test_benchmark_hash_stable_and_distinct():
    assert B.benchmark_hash("arbiter_ash") == B.benchmark_hash("arbiter_ash")
    assert len({B.benchmark_hash(i) for i in B.benchmarks()}) == len(B.benchmarks())


def test_breach_base_life_matches_pinned_pob():
    misc = ROOT / "third_party/PathOfBuilding-PoE2/src/Data/Misc.lua"
    if not misc.exists():
        pytest.skip("PoB submodule not checked out")
    txt = misc.read_text()
    row = re.search(r"monsterLifeTable\s*=\s*\{(.*?)\}", txt, re.S).group(1)
    vals = [int(x) for x in re.findall(r"\d+", row)]
    assert vals[83 - 1] == B._v(B.benchmarks()["breach_t15"]["base_life"])


def test_boss_ttk_and_gate():
    st = {"TotalDPS": 100_000, "TotalNumberOfHits": 6, "TotalEHP": 9000}
    r = B.boss_metrics("arbiter_ash", st)
    assert r.ttk_s == pytest.approx(4_274_058 / (100_000 * 0.75))
    assert r.gate_ttk is True                      # 57 s <= 60
    assert B.boss_metrics("arbiter_ash", {"TotalDPS": 90_000}).gate_ttk is False   # 63 s
    assert r.survive is None and r.survive_basis == "generic" and r.passed is None  # hits unsourced
    assert r.generic_hits_to_die == 6
    assert any("named hits unsourced" in f for f in r.flags)


def test_boss_unsourced_life_gives_none_not_a_guess():
    r = B.boss_metrics("arbiter_ash_uber", {"TotalDPS": 1e6})
    assert r.ttk_s is None and r.gate_ttk is None
    assert any("incomplete" in f for f in r.flags)


def test_boss_named_hits_survival(monkeypatch):
    b = B.benchmarks()["arbiter_ash"]
    old = b["hits"]
    st = {"TotalDPS": 1e5, "PhysicalMaximumHitTaken": 8000, "FireMaximumHitTaken": 4000}
    try:
        b["hits"] = [{"name": "combo", "physical": 4000, "fire": 2000, "source": "test"}]
        r = B.boss_metrics("arbiter_ash", st)
        assert r.hit_margins["combo"] == pytest.approx(2.0) and r.survive is True and r.survive_basis == "named"
        b["hits"] = [{"name": "combo", "physical": 4000, "fire": 5000, "source": "test"}]
        r = B.boss_metrics("arbiter_ash", st)
        assert r.hit_margins["combo"] == pytest.approx(0.8) and r.survive is False and r.passed is False
        b["hits"] = [{"name": "combo", "physical": 4000, "fire": None, "source": "test"}]
        assert B.boss_metrics("arbiter_ash", st).survive is None
    finally:
        b["hits"] = old


def test_pack_complete_with_sourced_life_mults():
    st = {"AverageHit": 5000, "AreaOfEffectRadiusMetres": 3.0, "Speed": 2.0}
    r = B.pack_metrics("breach_t15", st)
    assert r.hits_to_kill == {"normal": 7, "magic": 17, "rare": 55}         # ceil(33945*{1,2.48,8}/5000)
    assert r.coverage == pytest.approx(0.25) and r.clear_s == pytest.approx(55 / 0.25 / 2.0) and r.complete


def test_pack_clear_proxy_when_complete():
    b = B.benchmarks()["breach_t15"]
    saved = [m["life_mult"] for m in b["monsters"]]
    try:
        b["monsters"][1]["life_mult"] = {"value": 2.0, "source": "test"}
        b["monsters"][2]["life_mult"] = {"value": 4.0, "source": "test"}
        r = B.pack_metrics("breach_t15", {"AverageHit": 10_000, "AreaOfEffectRadiusMetres": 3.0, "Speed": 2.0})
        assert r.hits_to_kill["rare"] == 14                                 # ceil(33945*4/10000)
        assert r.clear_s == pytest.approx(14 / 0.25 / 2.0) and r.gate_clear is False   # 28 s > 20
        big = B.pack_metrics("breach_t15", {"AverageHit": 10_000, "AreaOfEffectRadiusMetres": 9.0, "Speed": 2.0})
        assert big.coverage == 1.0 and big.gate_clear is True
        proj = B.pack_metrics("breach_t15", {"AverageHit": 10_000, "ProjectileCount": 5, "Speed": 2.0}, projectile=True)
        assert proj.coverage == pytest.approx(5 / 55) and any("single-target" in f for f in proj.flags)
    finally:
        for m, v in zip(b["monsters"], saved):
            m["life_mult"] = v


@pytest.fixture(scope="module")
def pool_and_xml():
    from pos_catalogue import Catalogue
    from pos_engine.engine import PobEngine
    from pos_pipeline.assemble import assemble
    from pos_pipeline.spec import parse_spec
    from pos_pool.pool import EnginePool

    cat = Catalogue.load()
    spec = parse_spec({"pob_sha": cat.pob_sha[:7], "class": "Sorceress", "ascendancy": "Stormweaver", "level": 90,
                       "main_skill": {"gem": "Spark"}, "tiers": ["mid"]})
    with PobEngine() as eng:
        a = assemble(spec, cat, eng)
    assert a.ok, a.issues
    with EnginePool(workers=1) as pool:
        yield pool, a.xml


def test_engine_round_trip(pool_and_xml):
    pool, xml = pool_and_xml
    boss = B.evaluate(pool, xml, "arbiter_ash", "TotalDPS")
    assert boss.dps and boss.dps > 0 and boss.ttk_s and boss.ehp
    pack = B.evaluate(pool, xml, "breach_t15", "FullDPS", projectile=True)
    assert pack.hits_to_kill["normal"] and pack.coverage
    # engine returns the new keys
    [res] = pool.map([__import__("pos_pool.pool", fromlist=["Job"]).Job(
        xml, mutations=(("set_config", {"options": {"enemyIsBoss": "None"}}),), stat_keys=B.BENCH_KEYS)])
    assert res.stats.get("PhysicalMaximumHitTaken") and res.stats.get("AverageHit")
