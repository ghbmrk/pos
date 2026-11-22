"""Tree stage tests (real engine + committed catalogue; need LuaJIT)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_catalogue import Catalogue  # noqa: E402
from pos_engine.engine import PobEngine  # noqa: E402
from pos_pipeline.assemble import assemble  # noqa: E402
from pos_pipeline.spec import parse_spec  # noqa: E402
from pos_pipeline.tree import TreeSearch, search_tree, search_trees  # noqa: E402


@pytest.fixture(scope="module")
def seed():
    cat = Catalogue.load()
    spec = parse_spec({"pob_sha": cat.pob_sha[:7], "class": "Sorceress", "ascendancy": "Stormweaver", "level": 90,
                       "main_skill": {"gem": "Spark"}, "tiers": ["mid"]})
    with PobEngine() as eng:
        a = assemble(spec, cat, eng)
    assert a.ok, a.issues
    return a.xml


def test_search_improves_and_xml_round_trips(seed):
    with PobEngine() as eng:
        r = search_tree(eng, seed, "TotalDPS", points=8, candidates=50)
        assert r.ok and r.points_used <= 8 and r.allocated and r.seconds > 0
        assert r.final > r.start and r.gain > 0
        # the returned XML reproduces the stats when reloaded on a fresh engine
        eng.load_build_xml(r.xml)
        again = eng.get_stats(["TotalDPS"])["stats"]["TotalDPS"]
    assert again == pytest.approx(r.stats["TotalDPS"])


def test_require_forces_node_on_reset_tree(seed):
    with PobEngine() as eng:
        r = search_tree(eng, seed, "TotalDPS", points=20, candidates=50, require=["Eldritch Battery"])
    assert r.ok
    assert any(a.get("name") == "Eldritch Battery" and a.get("required") for a in r.allocated)


def test_parallel_seeds_and_failure_reporting(seed):
    out = search_trees([seed, seed], "TotalDPS", workers=2, points=4, candidates=25)
    assert [o.ok for o in out] == [True, True]
    assert out[0].points_used == out[1].points_used  # deterministic
    bad = search_trees(["<not xml"], "TotalDPS", workers=1)
    assert not bad[0].ok and bad[0].error and isinstance(bad[0], TreeSearch)


def test_best_of_caps_keeps_highest_final(seed):
    from pos_pipeline.tree import search_tree_caps
    with PobEngine() as eng:
        singles = {c: search_tree(eng, seed, "TotalDPS", points=12, candidates=c) for c in (10, 50)}
        best = search_tree_caps(eng, seed, "TotalDPS", caps=(10, 50, 10), points=12)
    assert best.ok
    assert best.final == pytest.approx(max(r.final for r in singles.values()))
    assert any(n.startswith("candidate caps: 10=") and "50=" in n for n in best.notes)  # duplicate cap run once
    out = search_trees([seed], "TotalDPS", workers=1, caps=(10, 50), points=12)
    assert out[0].final == pytest.approx(best.final)
