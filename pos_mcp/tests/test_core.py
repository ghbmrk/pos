"""MCP core tests: no engine needed (catalogue, validator, run-state files). Server test goes over real stdio."""
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_mcp import core  # noqa: E402

SPEC = {"pob_sha": "601768b", "class": "Sorceress", "ascendancy": "Stormweaver", "level": 90,
        "main_skill": {"gem": "Spark"}, "tiers": ["mid"]}


@pytest.fixture(autouse=True)
def runs(tmp_path, monkeypatch):
    monkeypatch.setenv("POS_RUNS_DIR", str(tmp_path))
    return tmp_path


def test_resolve_exact_and_suggestions_never_guess():
    r = core.resolve("skill", ["spark", "Sparkk", "zzzzqq"])["results"]
    assert r[0]["status"] == "exact" and r[0]["matches"][0]["name"] == "Spark"
    assert r[1]["status"] == "unresolved" and r[1]["suggestions"] and not r[1]["matches"]
    assert r[2]["status"] == "unresolved" and not r[2]["suggestions"]
    assert "error" in core.resolve("nonsense", ["x"])


def test_validate_accepts_dict_and_yaml_and_reports_structure_errors():
    assert core.validate_spec(SPEC)["ok"]
    assert core.validate_spec(json.dumps(SPEC))["ok"]
    assert "structure_error" in core.validate_spec({**SPEC, "bogus": 1})
    bad = core.validate_spec({**SPEC, "main_skill": {"gem": "Sparkk"}})
    assert not bad["ok"] and any(i["suggestions"] for i in bad["issues"] if i["severity"] == "error")


def test_run_refuses_invalid_spec_missing_bases_bad_slot_and_over_cap():
    assert not core.start_run({**SPEC, "main_skill": {"gem": "Nope Nope"}}, {"weapon": "Acrid Wand"})["ok"]
    assert "no bases" in core.start_run(SPEC, {})["error"]
    assert "unknown slot" in core.start_run(SPEC, {"hat": "x"})["error"]
    r = core.start_run(SPEC, {"weapon": "Acrid Wand"}, max_minutes=0.01)
    assert not r["ok"] and "refused" in r and not list(Path(os.environ["POS_RUNS_DIR"]).iterdir())


def test_preflight_reports_estimate():
    p = core.preflight(SPEC, {"weapon": "Acrid Wand"}, workers=4)
    assert p["ok"] and "min" in p["summary"].lower() and isinstance(p["over_cap"], bool)


def _fake_run(root: Path, rid: str, *, pid: int, report: bool, values: dict | None = None, metric="FullDPS"):
    d = root / rid
    d.mkdir()
    (d / "meta.json").write_text(json.dumps({"pid": pid, "started": time.time() - 5, "cmd": [], "tiers": ["mid"], "estimate": "est"}))
    (d / "log.txt").write_text("a\nb\n")
    if report:
        (d / "report.md").write_text("# R\n" + "x" * 100)
    if values is not None:
        (d / "run.json").write_text(json.dumps({"metric": metric, "seeds": [
            {"variant": {"k": str(i)}, "tiers": {t: {"ok": True, "value": v} for t, v in vs.items()}} for i, vs in enumerate(values)]}))
    return d


def test_state_machine_and_report(runs):
    _fake_run(runs, "done1", pid=2**22 - 1, report=True)
    _fake_run(runs, "dead1", pid=2**22 - 1, report=False)
    _fake_run(runs, "live1", pid=os.getpid(), report=False)
    assert core.run_status("done1")["state"] == "done"
    assert core.run_status("dead1")["state"] == "failed"
    assert core.run_status("live1")["state"] == "running"
    assert core.run_status("../../etc")["state"] == "unknown"
    g = core.get_report("done1", max_chars=10)
    assert g["ok"] and g["truncated"] and len(g["report_md"]) == 10
    assert not core.get_report("live1")["ok"]
    assert "still running" in core.start_run(SPEC, {"weapon": "Acrid Wand"})["error"]


def test_cancel_kills_process_group(runs):
    import subprocess
    p = subprocess.Popen(["sleep", "60"], start_new_session=True)
    _fake_run(runs, "live2", pid=p.pid, report=False)
    assert core.run_status("live2")["state"] == "running"
    assert core.cancel_run("live2")["ok"]
    p.wait(timeout=5)
    assert core.run_status("live2")["state"] == "cancelled"
    assert not core.cancel_run("live2")["ok"]


def test_compare(runs):
    _fake_run(runs, "a", pid=1, report=True, values=[{"mid": 100.0}, {"mid": 150.0}])
    _fake_run(runs, "b", pid=1, report=True, values=[{"mid": 300.0, "high": 5.0}])
    c = core.compare("a", "b")
    assert c["ok"] and c["tiers"]["mid"]["delta_pct"] == 100.0 and c["tiers"]["high"]["a"] is None
    _fake_run(runs, "c", pid=1, report=True, values=[{"mid": 1.0}], metric="TotalEHP")
    assert core.compare("a", "c")["note"] and core.compare("a", "c")["tiers"]["mid"]["delta_pct"] is None
    assert not core.compare("a", "nope")["ok"]


def test_server_over_stdio():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def go():
        params = StdioServerParameters(command=sys.executable, args=["-m", "pos_mcp"], cwd=str(Path(__file__).resolve().parents[2]),
                                       env={**os.environ})
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                names = {t.name for t in (await s.list_tools()).tools}
                res = await s.call_tool("resolve", {"kind": "skill", "names": ["Spark"]})
                return names, res

    names, res = asyncio.run(asyncio.wait_for(go(), 60))
    assert {"resolve", "validate_spec", "import_pob", "preflight", "run", "run_status", "get_report", "compare", "cancel_run"} <= names
    assert "Spark" in json.dumps(res.structured_content or [c.text for c in res.content])
