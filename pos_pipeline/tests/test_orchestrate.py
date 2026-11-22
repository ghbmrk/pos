"""Orchestrator tests with fake stages (no engine needed) plus preflight arithmetic."""
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_pipeline.orchestrate import RunRefused, Stages, estimate, load_rates, run  # noqa: E402
from pos_pipeline.spec import parse_spec  # noqa: E402


def spec(axes=None, tiers=("starter", "mid")):
    d = {"pob_sha": "601768b", "class": "Sorceress", "ascendancy": "Stormweaver", "level": 90,
         "main_skill": {"gem": "Spark"}, "tiers": list(tiers)}
    if axes:
        d["axes"] = axes
    return parse_spec(d)


def fake(fail_tree=(), fail_asm=(), fail_gear=()):
    calls = []

    def asm(v):
        calls.append(("asm", v))
        if v.get("ascendancy") in fail_asm:
            return NS(ok=False, xml="", issues=[NS(severity="error", message="boom")])
        return NS(ok=True, xml=f"<x {v.get('ascendancy')}>", issues=[], deferred_axes={})

    def gear(xml, tier, v):
        calls.append(("gear", xml, tier))
        if tier in fail_gear:
            raise RuntimeError("engine died")
        val = {"starter": 10.0, "mid": 100.0}[tier] * (2 if "Chrono" in xml else 1)
        item = NS(unique=None, affixes=[NS(group="g", rank=1)], base="B")
        return NS(value=val, baseline=1.0, xml=xml + "+g", items={"weapon": item}, price=NS(label="pts"),
                  floors_met=True, evals=7, notes=[])

    def trees(xmls):
        calls.append(("trees", list(xmls)))
        return [NS(ok="Bad" not in x or False, xml=x + "+t", error="tree x", gain=0.5, points_used=100, notes=[]) for x in xmls]

    st = Stages(asm, lambda xml, sk: NS(best=NS(supports=["s1"]), gain=0.2, notes=[]),
                lambda xml, sk, ids: xml + "+s", trees, gear)
    return st, calls


def test_loop_runs_supports_and_tree_once_per_seed_gear_per_tier():
    st, calls = fake()
    r = run(spec({"ascendancy": ["Stormweaver", "Chronomancer"]}), st, metric="FullDPS", slots=9, workers=4, skill_id="sk")
    assert [c[0] for c in calls].count("asm") == 2
    assert sum(1 for c in calls if c[0] == "trees") == 1          # one batched call, seeds in parallel
    assert sum(1 for c in calls if c[0] == "gear") == 4           # 2 seeds x 2 tiers
    assert all(s.ok and set(s.tiers) == {"starter", "mid"} for s in r.seeds)
    assert r.seeds[0].supports == ["s1"] and r.seeds[0].tree_points == 100
    best = r.best_per_tier()
    assert best["mid"][0] == {"ascendancy": "Chronomancer"} and best["mid"][1] == 200.0
    assert "boots/belt" in r.notes[0]
    assert r.seeds[0].tiers["mid"].items["weapon"] == "g r1 [B]"


def test_failed_seed_and_failed_tier_do_not_sink_the_run():
    st, _ = fake(fail_asm=("Chronomancer",), fail_gear=("mid",))
    r = run(spec({"ascendancy": ["Stormweaver", "Chronomancer"]}), st, metric="m", slots=9, workers=4, skill_id="sk")
    bad, good = [s for s in r.seeds if not s.ok], [s for s in r.seeds if s.ok]
    assert len(bad) == 1 and "boom" in bad[0].error
    assert good[0].tiers["starter"].ok and not good[0].tiers["mid"].ok and "engine died" in good[0].tiers["mid"].error


def test_cap_refuses_unless_forced_and_dry_run_runs_nothing():
    st, calls = fake()
    s = spec({"ascendancy": ["a", "b", "c", "d"]}, tiers=("starter", "budget", "mid", "high"))
    with pytest.raises(RunRefused) as e:
        run(s, st, metric="m", slots=9, workers=4, skill_id="sk", max_minutes=10)
    assert "EXCEEDED" in str(e.value) and not calls
    r = run(s, st, metric="m", slots=9, workers=4, skill_id="sk", max_minutes=10, force=True, dry_run=True)
    assert r.seeds == [] and not calls


def test_run_json_written(tmp_path):
    st, _ = fake()
    run(spec(), st, metric="m", slots=9, workers=4, skill_id="sk", out_dir=tmp_path)
    import json
    d = json.loads((tmp_path / "run.json").read_text())
    assert d["metric"] == "m" and "xml" not in d["seeds"][0]["tiers"]["mid"]


def test_estimate_matches_measured_rates():
    r = load_rates()
    # one seed, one tier, 9 slots, 4 workers: gear realloc 4 = 9 x 71 core-s / 4 = 160 s (measured 159 s)
    e = estimate(1, 1, 9, 4, realloc_rounds=4, rates=r)
    assert e.by_stage["gear"] == pytest.approx(9 * 71 / 4)
    assert e.by_stage["tree"] == 75                      # one seed = one core, not divided by workers
    e0 = estimate(1, 1, 9, 4, realloc_rounds=0, rates=r)
    assert e0.by_stage["gear"] == pytest.approx(9 * 32 / 4) and e0.wall_seconds < e.wall_seconds
    assert estimate(8, 1, 9, 4, rates=r).by_stage["tree"] == 150   # 8 seeds on 4 cores = 2 waves
    assert estimate(4, 4, 9, 4, rates=r).over_cap and not estimate(1, 1, 9, 4, rates=r).over_cap


def test_rates_have_sources():
    r = load_rates()
    assert all("source" in r[k] for k in ("assemble", "supports", "tree")) and all("source" in v for v in r["gear_per_slot"].values())


def test_real_engine_end_to_end(tmp_path):
    """One seed x one tier, two gear slots, cheap settings: every real stage runs and the output is sane."""
    pytest.importorskip("pos_engine")
    from pos_catalogue import Catalogue
    from pos_pipeline.orchestrate import engine_stages
    from pos_pipeline.validate import validate
    try:
        from pos_engine.engine import PobEngine
        PobEngine().close()
    except Exception as ex:  # no LuaJIT in this environment
        pytest.skip(f"engine unavailable: {ex}")
    cat = Catalogue.load()
    s = spec(tiers=("starter",))
    s.pob_sha = cat.pob_sha[:7]
    rep = validate(s, cat)
    assert rep.ok, rep.issues
    bases = {"weapon": "Acrid Wand", "amulet": "Absent Amulet"}
    with engine_stages(s, cat, rep, bases, workers=2, cache=tmp_path / "c.sqlite", realloc_rounds=0, floors={},
                       tree_caps=(25,)) as (st, skill_of):
        r = run(s, st, metric=rep.metric, slots=2, workers=2, skill_id=skill_of, out_dir=tmp_path)
    seed = r.seeds[0]
    assert seed.ok, seed.error
    t = seed.tiers["starter"]
    assert t.ok and t.value and t.value > t.baseline and set(t.items) == {"weapon", "amulet"}
    assert seed.tree_points and (tmp_path / "run.json").exists()


def test_few_slot_rate_matches_measured_run():
    e = estimate(1, 1, 2, 4, realloc_rounds=0)
    assert e.by_stage["gear"] == pytest.approx(35, abs=1) and e.by_stage["supports"] == pytest.approx(29, abs=1)
