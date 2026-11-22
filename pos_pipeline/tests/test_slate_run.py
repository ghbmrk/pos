"""Slate runner tests (I5): ranking, flow, report and best-rare ablation with fake runners (no engine); opt-in engine e2e."""
import copy
import json
import os
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_pipeline import data, parse_slate, validate_slate  # noqa: E402
from pos_pipeline.slate_run import (best_run, estimate_slate, make_rare_replacer, rank_by_benchmarks, render_slate_markdown,  # noqa: E402
                                    run_slate, screen_tier_for, unique_slot)
from pos_pipeline.sweep import Ablation, ablate  # noqa: E402
from pos_pipeline.tests.test_slate import cat, good_slate, spec  # noqa: E402,F401

BIDS = ["arbiter_ash", "breach_t15"]


def boss(ttk, survive=None):
    return {"id": "arbiter_ash", "ttk_s": ttk, "survive": survive, "gate_ttk": None, "flags": []}


def pack(clear):
    return {"id": "breach_t15", "clear_s": clear, "coverage": None, "hits_to_kill": {}, "flags": []}


# ---- ranking ----------------------------------------------------------------------------------------------
def test_ranking_complete_beats_incomplete_and_deaths_rank_last():
    cells = {"a": {"arbiter_ash": boss(100), "breach_t15": pack(50)},
             "b": {"arbiter_ash": boss(80), "breach_t15": pack(70)},
             "dead": {"arbiter_ash": boss(10, survive=False), "breach_t15": pack(1)},
             "partial": {"arbiter_ash": boss(1), "breach_t15": {"error": "x"}}}
    order = rank_by_benchmarks(cells, BIDS)
    assert [n for n, _ in order] == ["a", "b", "dead", "partial"]      # a: positions 2,1 ; b: 1,2 -> tie, name order
    notes = dict(order)
    assert "survival check FAILED" in notes["dead"] and "no value for breach_t15" in notes["partial"]


def test_ranking_with_nothing_available_is_deterministic():
    cells = {n: {"arbiter_ash": None, "breach_t15": pack(None)} for n in ("z", "m", "a")}
    assert [n for n, _ in rank_by_benchmarks(cells, BIDS)] == ["a", "m", "z"]


def test_bench_ranking_ignores_dps():
    # a high-DPS candidate with a worse time-to-kill must not outrank (DPS is not an input at all)
    cells = {"fast_ttk": {"arbiter_ash": boss(30), "breach_t15": pack(9)}, "slow_ttk": {"arbiter_ash": boss(300), "breach_t15": pack(9)}}
    assert rank_by_benchmarks(cells, BIDS)[0][0] == "fast_ttk"


def test_screen_tier_is_capped_by_brief():
    cfg = data.ideation()
    assert screen_tier_for({"tiers": ["budget", "mid", "high"]}, cfg) == "mid"
    assert screen_tier_for({"tiers": ["starter", "budget"]}, cfg) == "budget"
    assert screen_tier_for({"tiers": []}, cfg) == "mid"


# ---- flow with a fake runner ------------------------------------------------------------------------------
class FakeResult:
    def __init__(self, tiers, ttk, clear, err=None):
        self.seeds = [NS(error=err)]
        self._d = {"seeds": [{"variant": {}, "supports": ["S"], "ok": err is None, "error": err, "tiers": {
            t: {"ok": True, "value": 100.0, "price": "1 div", "floors_met": True, "stats": {"TotalEHP": 9000.0},
                "bench": {"arbiter_ash": boss(ttk), "breach_t15": pack(clear)}} for t in tiers} if err is None else {}}]}

    def to_dict(self):
        return self._d


class FakeRunner:
    def __init__(self, table, fail=()):
        self.table, self.fail, self.calls = table, set(fail), []

    def screen(self, c, tier):
        self.calls.append(("screen", c.name, tier))
        if c.name in self.fail:
            raise RuntimeError("engine died")
        ttk, clear = self.table[c.name]
        return FakeResult([tier], ttk, clear), [Ablation({"kind": "keystone", "id": "X"}, 100.0, 80.0, 0.2, "confirmed")]

    def deepen(self, c):
        self.calls.append(("deepen", c.name))
        ttk, clear = self.table[c.name]
        return FakeResult(["mid", "high"], ttk * 0.5, clear * 0.5)


def validated(cat, tiers=("mid", "high")):
    d = copy.deepcopy(good_slate())
    d["brief"]["tiers"] = list(tiers)
    d["brief"]["benchmarks"] = BIDS
    s = parse_slate(d)
    return s, validate_slate(s, cat)


def test_run_slate_screens_ranks_deepens_top_k(cat, tmp_path):
    s, rep = validated(cat)
    runner = FakeRunner({"Fire Witch": (200, 20), "Frost Monk": (100, 30), "Slam Ranger": (300, 10)}, fail=())
    out = run_slate(s, rep, runner, k=2, out_dir=tmp_path, estimate_text="est", log=lambda m: None)
    ranks = {c.name: c.screen_rank for c in out.candidates}
    assert sorted(ranks.values()) == [1, 2, 3]
    assert [c for c in runner.calls if c[0] == "screen"] and all(c[2] == "mid" for c in runner.calls if c[0] == "screen")
    deepened = {c[1] for c in runner.calls if c[0] == "deepen"}
    assert len(deepened) == 2 and "Frost Monk" in deepened
    deep = [c for c in out.candidates if c.deep]
    assert len(deep) == 2 and all(set(c.deep) == {"mid", "high"} and set(c.deep_rank) == {"mid", "high"} for c in deep)
    assert out.screen_tier == "mid" and out.estimate == "est"
    md = (tmp_path / "slate_report.md").read_text()
    for needle in ("# Slate report", "## Screen ranking", "## Full run, tier `mid`", "## Full run, tier `high`", "Immune to Chaos Damage",
                   "| keystone: X | confirmed | +20.0% |", "## Across the slate"):
        assert needle in md, needle
    db = sqlite3.connect(tmp_path / "slate_results.sqlite")
    assert db.execute("select count(*) from candidates").fetchone()[0] == 3
    assert db.execute("select count(*) from ablations").fetchone()[0] == 3
    assert json.loads((tmp_path / "slate_run.json").read_text())["deepen_k"] == 2


def test_failed_screen_is_recorded_and_slate_continues(cat):
    s, rep = validated(cat)
    runner = FakeRunner({"Fire Witch": (200, 20), "Frost Monk": (100, 30), "Slam Ranger": (300, 10)}, fail={"Frost Monk"})
    out = run_slate(s, rep, runner, k=3)
    f = next(c for c in out.candidates if c.name == "Frost Monk")
    assert f.status == "failed" and "engine died" in f.error and f.screen_rank is None
    assert sorted(c.screen_rank for c in out.candidates if c.screen_rank) == [1, 2]
    assert "Screen FAILED" in render_slate_markdown(out.to_dict())


def test_refuses_empty_benchmarks_and_invalid_slate(cat):
    s = parse_slate(copy.deepcopy(good_slate()))
    rep = validate_slate(s, cat)
    s.brief["benchmarks"] = []                       # the gate checks brief ids; the runner still refuses an empty list
    with pytest.raises(ValueError, match="benchmark"):
        run_slate(s, rep, FakeRunner({}))
    d = copy.deepcopy(good_slate())
    d["candidates"] = d["candidates"][:1]
    s = parse_slate(d)
    with pytest.raises(ValueError, match="did not validate"):
        run_slate(s, validate_slate(s, cat), FakeRunner({}))


def test_best_run_picks_highest_objective_across_seeds():
    res = {"seeds": [{"variant": {"a": "1"}, "supports": [], "tiers": {"mid": {"ok": True, "value": 5.0}}},
                     {"variant": {"a": "2"}, "supports": [], "tiers": {"mid": {"ok": True, "value": 9.0}}},
                     {"variant": {"a": "3"}, "supports": [], "tiers": {"mid": {"ok": False, "value": 99.0}}}]}
    assert best_run(res, "mid")["variant"] == {"a": "2"} and best_run(res, "high") is None


def test_estimate_slate_scales_and_caps(cat):
    s, rep = validated(cat)
    cands = [c for c in s.candidates]
    slots = {c.name: 2 for c in cands}
    e = estimate_slate(cands, s.brief, slots, 4, max_minutes=45, k=3)
    e1 = estimate_slate(cands[:1], s.brief, slots, 4, max_minutes=45, k=3)
    assert e.wall_seconds > e1.wall_seconds > 0 and set(e.by_stage) == {"screen", "ablation", "deepen"}
    assert estimate_slate(cands, s.brief, slots, 4, max_minutes=1, k=3).over_cap and "EXCEEDED" in estimate_slate(cands, s.brief, slots, 4, max_minutes=1).summary()
    assert estimate_slate(cands, s.brief, slots, 4, max_minutes=45, k=0).by_stage["deepen"] == 0


def test_candidate_bases_parse_and_validate(cat):
    d = copy.deepcopy(good_slate())
    d["candidates"][0]["bases"] = {"ring_1": "Gold Ring"}
    assert parse_slate(d).candidates[0].bases == {"ring_1": "Gold Ring"}
    assert validate_slate(parse_slate(d), cat).ok
    for bad in ({"hat": "Gold Ring"}, {"ring_1": "Nope Ring"}):
        d["candidates"][0]["bases"] = bad
        r = validate_slate(parse_slate(d), cat)
        assert "Fire Witch" not in [c.name for c in r.kept]


# ---- best-rare replacement for unique ablation -----------------------------------------------------------
XML = ('<PathOfBuilding2><Items><Item id="1">Rarity: UNIQUE\nSome Ring\nGold Ring</Item><Item id="2">Rarity: RARE\nx\nGold Ring</Item>'
       '<ItemSet id="1"><Slot name="Ring 1" itemId="2"/><Slot name="Ring 2" itemId="1"/></ItemSet></Items></PathOfBuilding2>')


def test_unique_slot_finds_equipped_unique():
    assert unique_slot(XML, "some  ring") == "ring_2" and unique_slot(XML, "Other") is None


class FakePool:
    """Value = number of 'BEST' markers minus 'EMPTY' markers in the xml, plus 10."""
    def map(self, jobs):
        return [NS(ok=True, stats={"TotalDPS": 10.0 + j.xml.count("BEST") * 5 - j.xml.count("EMPTY") * 4 + j.xml.count("UNIQ") * 10}) for j in jobs]


class FakeSearcher:
    uniques = {"Other Unique": "cheap"}

    def __init__(self, fail=False):
        self.fail, self.eng = fail, NS(load_build_xml=lambda x: None, unequip_item=lambda s: {"ok": True}, get_xml=lambda: "UNIQ EMPTY")

    def slot_budget(self, tier, slot):
        return 12.0

    def best_item(self, xml, slot, base, budget, exclude_uniques=()):
        assert slot == "ring_2" and base == "Gold Ring" and "Some Ring" in exclude_uniques and budget == 12.0
        if self.fail:
            raise ValueError("no mods for base")
        return NS(affixes=(NS(group="Life", rank=1),), raw="r"), (0, 1)

    def equip(self, xml, slot, raw):
        return "UNIQ BEST"


class UCat:
    def resolve(self, kind, text):
        return NS(entry={"name": "Some Ring", "base": "Gold Ring"} if text == "Some Ring" else None)


def test_ablate_unique_uses_best_rare_replacement():
    rep = make_rare_replacer(UCat(), FakeSearcher(), "mid")
    new, label = rep(XML, {"kind": "unique", "id": "Some Ring"})
    assert new == "UNIQ BEST" and "best rare at mid [Gold Ring]: Life r1" in label


def test_unique_verdict_with_replacement_vs_unequip_bound():
    base_xml = "UNIQ"                                        # 10 + 10 = 20
    [with_rare] = ablate(None, FakePool(), base_xml, [{"kind": "unique", "id": "U"}], "TotalDPS", replace_unique=lambda x, p: ("BEST", "rare"))
    assert with_rare.replacement == "rare" and with_rare.without == 15.0 and with_rare.verdict == "confirmed" and with_rare.delta_rel == pytest.approx(0.25)
    [removed] = ablate(None, FakePool(), "UNIQ", [{"kind": "unique", "id": "U"}], "TotalDPS", replace_unique=lambda x, p: ("", "empty"))
    assert removed.without == 10.0 and removed.delta_rel == pytest.approx(0.5)


def test_unique_not_in_build_is_not_testable_and_fallback_is_labelled():
    rep = make_rare_replacer(UCat(), FakeSearcher(), "mid")
    [a] = ablate(None, FakePool(), XML, [{"kind": "unique", "id": "Gone"}], "TotalDPS", replace_unique=rep)
    assert a.verdict == "not_testable" and "not in catalogue" in a.note
    class C2(UCat):
        def resolve(self, kind, text):
            return NS(entry={"name": "Absent Ring", "base": "Gold Ring"})
    [b] = ablate(None, FakePool(), XML, [{"kind": "unique", "id": "Absent Ring"}], "TotalDPS", replace_unique=make_rare_replacer(C2(), FakeSearcher(), "mid"))
    assert b.verdict == "not_testable" and "not equipped" in b.note
    new, label = make_rare_replacer(UCat(), FakeSearcher(fail=True), "mid")(XML, {"id": "Some Ring"})
    assert new == "UNIQ EMPTY" and "upper bound" in label


