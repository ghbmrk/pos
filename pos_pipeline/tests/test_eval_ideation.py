"""I7 harness: gate re-run per saved round, contamination counts, diversity, engine summary (no engine needed)."""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import eval_ideation as ev  # noqa: E402

EX = ROOT / "examples" / "ideation_slate.yaml"


def _fixture(tmp_path: Path) -> Path:
    d = tmp_path / "p0"
    d.mkdir()
    bad = EX.read_text(encoding="utf-8").replace('"Dream Fragments"]', '"Dream Fragmentz"]') \
        .replace("Gain Power Charges instead", "Gain Endurance Charges instead")
    (d / "round1.yaml").write_text(bad, encoding="utf-8")
    shutil.copy(EX, d / "round2.yaml")
    (d / "run").mkdir()
    (d / "run" / "slate_run.json").write_text(json.dumps({"candidates": [
        {"name": "A", "source": "llm", "status": "screened", "screen_rank": 1, "ablations": [{"verdict": "confirmed"}]},
        {"name": "B", "source": "sweep:p/x", "status": "screened", "screen_rank": 2,
         "ablations": [{"verdict": "not_load_bearing"}, {"verdict": "not_testable"}]},
        {"name": "C", "source": "llm", "status": "failed", "error": "engine refused"}]}), encoding="utf-8")
    return tmp_path


def test_rounds_contamination_diversity_engine(tmp_path):
    rows = ev.evaluate(_fixture(tmp_path))
    assert len(rows) == 1
    r = rows[0]
    assert r["rounds_used"] == 2
    assert r["rounds"][0]["submitted"] == 3 and r["rounds"][0]["kept"] < 3
    assert r["contamination_caught_r1"] == {"unresolved": 1, "quote_mismatch": 1}
    assert r["unresolved_names_all"] == ["Dream Fragmentz"]
    assert r["final_kept"] == 3 and r["final_ok"]
    assert r["diversity"]["n"] == 3 and r["diversity"]["distinct"]["main_skill"] == 3
    e = r["engine"]
    assert e["confirmed_share"] == 0.5 and e["top"][0][0] == "A" and e["failed"][0][0] == "C"
    md = ev.render(rows)
    assert "Dream Fragmentz" in md and "| p0 |" in md


def test_unparseable_round_is_a_failed_round(tmp_path):
    d = tmp_path / "p1"
    d.mkdir()
    (d / "round1.yaml").write_text("slate: 1\ncandidates: nope\n", encoding="utf-8")
    shutil.copy(EX, d / "round2.yaml")
    r = ev.evaluate(tmp_path)[0]
    assert "parse_error" in r["rounds"][0] and r["first_pass_rate"] == 0.0 and r["final_ok"]
