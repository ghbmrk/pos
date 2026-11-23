"""Inner loop v1 (L3): control flow with fake moves, no engine."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_pipeline.loop import Move, better, gain, improve  # noqa: E402
from pos_pipeline.orchestrate import Stages, run  # noqa: E402
from pos_pipeline.tests.test_orchestrate import fake, spec  # noqa: E402


def keyof(xml):    # xml is a string of "d<deficit>g<goal>"
    d, g = xml[1:].split("g")
    return (-float(d), float(g))


def mk(d, g):
    return f"d{d}g{g}"


def test_better_is_lexicographic():
    assert better((-0.1, 0.0), (-0.5, 9.0))          # lower deficit wins even with a worse goal
    assert not better((-0.5, 9.0), (-0.1, 0.0))
    assert better((0.0, 2.0), (0.0, 1.0)) and not better((0.0, 1.0), (0.0, 1.0))
    assert gain((-0.5, 1.0), (-0.25, 1.5)) == 0.75


def test_keeps_only_improvements_and_converges(tmp_path):
    seq = {"a": [mk(0, 1), mk(0, 1.5), mk(0, 1.505)], "b": [mk(0, 0.5), mk(0, 1.6), mk(0, 1.5)]}   # per round
    n = {"a": 0, "b": 0}

    def mv(name):
        def f(x):
            r = seq[name][n[name]]; n[name] += 1
            return r
        return f
    kept = []
    tr = tmp_path / "t.jsonl"
    r = improve(mk(0, 0), [Move("a", mv("a"), on_accept=kept.append), Move("b", mv("b"))], keyof, trace=tr)
    # round 1: a -> g1.0 kept, b -> 0.5 worse, discarded (+1.0). round 2: a -> 1.5 kept, b -> 1.6 kept (+0.6).
    # round 3: a -> 1.505 and b -> 1.5 are both worse than 1.6 (gain 0): converged
    assert r.stop == "converged" and r.best == (0.0, 1.6) and len(r.rounds) == 3
    assert [m.accepted for m in r.moves if m.round == 1] == [True, False]
    assert kept == [mk(0, 1), mk(0, 1.5)]
    assert r.xml == mk(0, 1.6) and r.gain == 1.6
    lines = [json.loads(x) for x in tr.read_text().splitlines()]
    assert lines[0]["event"] == "start" and lines[-1]["event"] == "stop" and lines[-1]["reason"] == "converged"
    assert sum(1 for x in lines if x["event"] == "round") == 3


def test_never_regresses_and_survives_failures():
    def boom(x):
        raise RuntimeError("engine died")
    r = improve(mk(0, 1), [Move("boom", boom), Move("worse", lambda x: mk(1, 5)), Move("same", lambda x: x)], keyof)
    assert r.xml == mk(0, 1) and r.best == r.start and r.stop == "converged" and len(r.rounds) == 1
    notes = {m.move: m.note for m in r.moves}
    assert "engine died" in notes["boom"] and notes["worse"] == "no gain; discarded" and notes["same"] == "unchanged"


def test_max_rounds_and_budget():
    ctr = iter(range(1000))
    steps = {"g": 0}

    def up(x):
        steps["g"] += 1
        return mk(0, steps["g"])
    r = improve(mk(0, 0), [Move("up", up)], keyof, max_rounds=3)
    assert r.stop == "max_rounds" and len(r.rounds) == 3 and r.best == (0.0, 3.0)
    t = {"now": 0.0}

    def slow(x):
        t["now"] += 10
        return mk(0, t["now"])
    r = improve(mk(0, 0), [Move("slow", slow)], keyof, budget_s=25, max_rounds=9, clock=lambda: t["now"])
    assert r.stop == "budget" and len(r.moves) == 3           # checked between moves; a started move finishes


def test_deficit_traded_before_goal():
    r = improve(mk(0.5, 5), [Move("m", lambda x: mk(0.1, 1))], keyof, max_rounds=1)
    assert r.best == (-0.1, 1.0)


def test_orchestrator_uses_loop_result(tmp_path):
    st, calls = fake()
    seen = {}

    def improve_stage(xml, tier, variant, rounds, budget_s, trace):
        seen.update(xml=xml, rounds=rounds, trace=trace)
        lr = improve(xml, [Move("g", lambda x: x + "+L")], lambda x: (0.0, float(len(x))), max_rounds=rounds, trace=trace)
        return NS(loop=lr, gear=None)
    st.improve = improve_stage
    st.stats = lambda xml, v: {"FullDPS": 1000.0 if xml.endswith("+L") else 10.0}
    r = run(spec(tiers=("mid",)), st, metric="FullDPS", slots=3, workers=1, skill_id="sk", rounds=2, out_dir=tmp_path)
    tr = r.seeds[0].tiers["mid"]
    assert seen["rounds"] == 2 and tr.loop["rounds"] and tr.xml.endswith("+L") and tr.value == 1000.0
    assert any("loop:" in n for n in tr.notes)
    assert (tmp_path / "trace.jsonl").exists() and "improvement loop" in (tmp_path / "report.md").read_text()


def test_loop_failure_keeps_single_pass_result():
    st, _ = fake()
    st.improve = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("nope"))
    r = run(spec(tiers=("mid",)), st, metric="FullDPS", slots=3, workers=1, skill_id="sk", rounds=3)
    tr = r.seeds[0].tiers["mid"]
    assert tr.ok and tr.value == 100.0 and any("loop failed" in n for n in tr.notes)


def test_rounds_1_does_not_call_loop():
    st, _ = fake()
    st.improve = lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not run"))
    assert run(spec(tiers=("mid",)), st, metric="FullDPS", slots=3, workers=1, skill_id="sk").seeds[0].ok
