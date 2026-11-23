"""L6 prompt-to-report loop: pure helpers and the outer-loop flow with a fake runner (no engine)."""
import copy
import json
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_pipeline import parse_slate, validate_slate  # noqa: E402
from pos_pipeline.play import MIN_GAIN, bench_gain, joint_effect, play, render_play_markdown  # noqa: E402
from pos_pipeline.tests.test_slate import cat, good_slate  # noqa: E402,F401
from pos_pipeline.tests.test_slate_run import BIDS, FakeResult, boss, pack  # noqa: E402


def cell(ttk, clear=50, survive=None):
    return {"arbiter_ash": boss(ttk, survive), "breach_t15": pack(clear)}


def test_bench_gain_mean_and_survival():
    g, _ = bench_gain(cell(100, 100), cell(80, 100), BIDS)
    assert abs(g - 0.10) < 1e-9                                   # mean of +20% and 0%
    g, note = bench_gain(cell(100), cell(10, survive=False), BIDS)
    assert g == -1.0 and "survival check lost" in note            # faster but dies: never better
    g, _ = bench_gain(cell(100, survive=False), cell(100), BIDS)
    assert g >= MIN_GAIN                                          # now survives: counts as a gain
    assert bench_gain({}, cell(1), BIDS)[0] is None


def test_joint_effect_verdicts():
    j = joint_effect(100.0, 25.0, [50.0, 50.0])                   # singles lose 50% each -> independent predicts 75%
    assert abs(j["independent_share"] - 0.75) < 1e-9 and j["verdict"] == "independent" and abs(j["core_ratio"] - 4.0) < 1e-9
    assert joint_effect(100.0, 10.0, [50.0, 50.0])["verdict"] == "compounds"   # joint 90% > 75%
    assert joint_effect(100.0, 60.0, [50.0, 50.0])["verdict"] == "overlaps"    # joint 40% < 75%


class PlayFake:
    """Screens from a table; each parent has one child whose result comes from `child_table` (None = no proposal)."""
    def __init__(self, table, child_table):
        self.table, self.child_table, self.calls, self.last = table, child_table, [], {}

    def screen(self, c, tier):
        self.calls.append(("screen", c.name))
        ttk, clear = self.table[c.name]
        return FakeResult([tier], ttk, clear), []

    def propose(self, c, n):
        self.calls.append(("propose", c.name))
        ch = self.child_table.get(c.name)
        if not ch:
            return []
        child = replace(c, name=c.name + " + Keystone Z", source="sweep:keystone")
        return [(child, {"kind": "keystone", "id": "Z", "name": "Z", "sweep_rel": 0.2, "points": 3})]

    def screen_light(self, c, tier):
        self.calls.append(("screen_light", c.name))
        ttk, clear = self.child_table[c.name.replace(" + Keystone Z", "")]
        return {"bench": cell(ttk, clear), "tier_run": {"bench": cell(ttk, clear), "value": 1.0}}

    def deepen(self, c):
        self.calls.append(("deepen", c.name))
        base = c.name.replace(" + Keystone Z", "")
        ttk, clear = self.child_table.get(base) if " + Keystone Z" in c.name else self.table[base]
        tr = lambda: NS(ok=True, value=1.0, xml="<x/>", bench=cell(ttk / 2, clear / 2), price="1 div")  # noqa: E731
        return NS(seeds=[NS(variant={}, supports=["S"], tiers={"mid": tr()})])

    def core_check(self, c, xml, variant, supports, tier):
        return {"ablations": [], "joint": {"verdict": "n/a", "note": "fake"}}

    def diagnose_text(self, xml, c):
        return "fake diagnosis"


def validated(cat):
    d = copy.deepcopy(good_slate())
    d["brief"]["tiers"] = ["mid"]
    d["brief"]["benchmarks"] = BIDS
    s = parse_slate(d)
    return s, validate_slate(s, cat)


def test_outer_loop_keeps_only_sim_verified_changes_and_stops_on_no_gain(cat, tmp_path):
    s, rep = validated(cat)
    runner = PlayFake({"Fire Witch": (200, 20), "Frost Monk": (100, 30), "Slam Ranger": (300, 10)},
                      {"Frost Monk": (60, 30), "Fire Witch": (199, 20)})    # Frost Monk +40% (kept); Fire Witch +0.5% (rejected)
    out = play(s, rep, runner, k=2, outer_rounds=3, children=1, out_dir=tmp_path, log=lambda m: None)
    kept = [x for x in out["steps"] if x.get("kept")]
    assert [x["child"] for x in kept] == ["Frost Monk + Keystone Z"]
    rej = [x for x in out["steps"] if x.get("child") and not x["kept"]]
    assert rej and rej[0]["parent"] == "Fire Witch" and rej[0]["gain"] < MIN_GAIN
    parent = next(x for x in out["screened"] if x["name"] == "Frost Monk")
    assert parent["superseded_by"] == "Frost Monk + Keystone Z"
    assert out["stop"] == "no_gain"                                          # round 2: the child's own proposal finds nothing
    assert "Frost Monk + Keystone Z" in {f["name"] for f in out["finalists"]} and "Frost Monk" not in {f["name"] for f in out["finalists"]}
    assert all(f["rank"]["mid"] for f in out["finalists"] if f["deep"])
    md = (tmp_path / "report.md").read_text()
    for needle in ("# Build report", "## Results", "## Improvement rounds", "KEPT", "rejected", "superseded by Frost Monk + Keystone Z", "fake diagnosis"):
        assert needle in md, needle
    assert json.loads((tmp_path / "play.json").read_text())["finalists"]
    assert "xml" not in json.dumps(out["finalists"])


def test_assumed_banner_and_empty_screen(cat):
    s, rep = validated(cat)
    runner = PlayFake({"Fire Witch": (200, 20), "Frost Monk": (100, 30), "Slam Ranger": (300, 10)}, {})
    out = play(s, rep, runner, k=1, outer_rounds=1, log=lambda m: None)
    assert out["stop"] == "no_gain" and out["steps"][0]["note"].startswith("no sweep pick")
    assert "> **ASSUMED:** Squire gear is a stand-in" in render_play_markdown(out, ["Squire gear is a stand-in"])


def test_assumed_squire_slate_needs_the_brief_opt_in_and_no_mixing():
    from pos_catalogue import Catalogue
    from pos_pipeline import load_slate
    path = Path(__file__).resolve().parents[2] / "examples" / "play" / "squire_cyclone_slate.yaml"
    catalogue = Catalogue.load(pob_sha="601768b")
    s = load_slate(path)
    assert validate_slate(s, catalogue).ok
    s.brief["assumed_ok"] = False
    rep = validate_slate(s, catalogue)
    assert not rep.ok and all(any(i.code == "assumed_in_slate" for i in r.errors) for r in rep.candidates)
    s.brief["assumed_ok"] = True
    s.candidates[0].spec.companion = None                                 # one non-assumed candidate: the opt-in no longer applies
    rep = validate_slate(s, catalogue)
    assert any(i.code == "assumed_in_slate" for r in rep.candidates for i in r.errors)
