"""Report tests: golden markdown from fake stages (no engine), sqlite contents, benchmark wiring and incomplete flags."""
import json
import os
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_pipeline.benchmarks import boss_metrics, pack_metrics  # noqa: E402
from pos_pipeline.orchestrate import Stages, run  # noqa: E402
from pos_pipeline.report import load_run, render_markdown, write_report  # noqa: E402
from pos_pipeline.spec import parse_spec  # noqa: E402

GOLDEN = Path(__file__).parent / "golden" / "report.md"


def spec(benchmarks=("arbiter_ash", "breach_t15", "arbiter_ash_uber")):
    return parse_spec({"pob_sha": "601768b", "class": "Sorceress", "ascendancy": "Stormweaver", "level": 90,
                       "main_skill": {"gem": "Spark"}, "tiers": ["starter", "mid"], "benchmarks": list(benchmarks),
                       "axes": {"ascendancy": ["Stormweaver", "Chronomancer"]}})


def stages(fail_bench=False):
    def asm(v):
        return NS(ok=True, xml=f"<{v['ascendancy']}>", issues=[], deferred_axes={})

    def gear(xml, tier, v):
        val = {"starter": 1000.0, "mid": 50000.0}[tier] * (1.5 if "Chrono" in xml else 1)
        item = NS(unique=None, affixes=[NS(group="Added Lightning", rank=2)], base="Acrid Wand")
        return NS(value=val, baseline=10.0, xml=xml, items={"weapon": item}, price=NS(label="1.5 div, 12 samples, 2026-11-20"),
                  floors_met=tier == "mid", evals=700, notes=["floors not met (deficit 30)"] if tier == "starter" else [],
                  rejected_unparsed=["SomeUnparsedMod1"])

    def st(xml, v):
        dps = 1000.0 if "Chrono" not in xml else 1500.0
        return {"FullDPS": dps, "TotalEHP": 9000.0, "Life": 1200.0, "EnergyShield": 3000.0,
                "FireResist": 75, "ColdResist": 75, "LightningResist": 60, "AverageHit": 500.0}

    def bench(xml, bid, v):
        if fail_bench:
            raise RuntimeError("engine died")
        s = {**st(xml, v), "Speed": 2.0, "AreaOfEffectRadiusMetres": 3.0, "ProjectileCount": 5}
        return boss_metrics(bid, s, "FullDPS") if bid.startswith("arbiter") else pack_metrics(bid, s, projectile=True)

    return Stages(asm, lambda xml, sk: NS(best=NS(supports=["Chain", "Fork"]), gain=0.2, notes=[]),
                  lambda xml, sk, ids: xml, lambda xmls: [NS(ok=True, xml=x, error=None, gain=0.5, points_used=100, notes=[]) for x in xmls],
                  gear, bench=bench, stats=st)


def do_run(**kw):
    r = run(spec(), stages(**kw), metric="FullDPS", slots=2, workers=4, skill_id="sk",
            meta={"metric_note": "FullDPS: upper bound", "limitations": ["[suspected] example limitation"]})
    d = r.to_dict()
    for s in d["seeds"]:           # timings are the only non-deterministic fields
        s["seconds"] = {}
        for tr in s["tiers"].values():
            tr["seconds"] = 0.0
    return d


def test_golden_report():
    md = render_markdown(do_run())
    if os.environ.get("UPDATE_GOLDEN"):
        GOLDEN.write_text(md, encoding="utf-8")
    assert md == GOLDEN.read_text(encoding="utf-8")


def test_ranking_flags_and_labels():
    md = render_markdown(do_run())
    mid = md.split("## Tier `mid`")[1].split("## Tier")[0]
    assert mid.index("Chronomancer") < mid.index("Stormweaver")                 # best first
    assert "-33.3%" in mid and "best" in mid
    assert "incomplete" in md and "unsourced inputs" in md and "ASSUMPTION" in md   # null benchmark inputs are flagged
    assert "SomeUnparsedMod1" in md and "floors not met" in md and "NOT met" in md
    assert "~1.5 div, 12 samples" in md and "proxy" in md and "FullDPS: upper bound" in md
    assert "60% (<75 uncapped)" in md


def test_benchmark_failure_marks_cell_not_tier():
    d = do_run(fail_bench=True)
    tr = d["seeds"][0]["tiers"]["mid"]
    assert tr["ok"] and tr["bench"]["arbiter_ash"]["error"].startswith("RuntimeError")
    assert "error: RuntimeError" in render_markdown(d)


def test_unknown_benchmark_rejected():
    with pytest.raises(ValueError, match="unknown benchmark"):
        run(spec(("nope",)), stages(), metric="m", slots=2, workers=4, skill_id="sk")


def test_files_written_and_rerenderable(tmp_path):
    r = run(spec(), stages(), metric="FullDPS", slots=2, workers=4, skill_id="sk", out_dir=tmp_path)
    assert (tmp_path / "report.md").read_text() == render_markdown(load_run(tmp_path))
    c = sqlite3.connect(tmp_path / "results.sqlite")
    assert c.execute("select count(*) from tier_runs").fetchone()[0] == 4
    assert c.execute("select count(*) from bench").fetchone()[0] == 12
    assert c.execute("select seed from tier_runs where tier='mid' and rank=1").fetchone()[0] == 1   # Chronomancer seed
    assert json.loads(c.execute("select result from bench where benchmark='arbiter_ash' limit 1").fetchone()[0])["patch"]
    assert r.seeds[0].tiers["mid"].bench["breach_t15"]["complete"] is True
    assert r.seeds[0].tiers["mid"].bench["arbiter_ash_uber"]["ttk_s"] is None


def test_no_benchmarks_still_reports():
    r = run(spec(()), stages(), metric="FullDPS", slots=2, workers=4, skill_id="sk")
    assert "None requested" in render_markdown(r.to_dict())


@pytest.mark.skipif(not os.environ.get("POS_E2E"), reason="engine run of about 2.5 min; set POS_E2E=1")
def test_end_to_end_on_engine(tmp_path):
    import subprocess
    root = Path(__file__).resolve().parents[2]
    p = subprocess.run([sys.executable, "-m", "pos_pipeline", "run", str(root / "examples" / "spark_golden.yaml"),
                        "weapon=Acrid Wand", "amulet=Lapis Amulet", "--realloc-rounds", "0", "--out", str(tmp_path)],
                       capture_output=True, text=True, cwd=root)
    assert p.returncode == 0, p.stdout[-800:] + p.stderr[-800:]
    md = (tmp_path / "report.md").read_text()
    assert "## Tier `mid`" in md and "arbiter_ash" in md and "breach_t15" in md and "unsourced inputs" in md
    c = sqlite3.connect(tmp_path / "results.sqlite")
    assert c.execute("select count(*) from bench").fetchone()[0] == 3
