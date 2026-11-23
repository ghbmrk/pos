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
                prompts = {p.name: p for p in (await s.list_prompts()).prompts}
                got = await s.get_prompt("ideate", {"idea": "a tanky lightning build"})
                return names, res, prompts, got

    names, res, prompts, got = asyncio.run(asyncio.wait_for(go(), 60))
    assert "ideate" in prompts and any(a.name == "idea" and a.required for a in prompts["ideate"].arguments)
    assert "a tanky lightning build" in got.messages[0].content.text
    assert {"resolve", "validate_spec", "import_pob", "preflight", "run", "run_status", "get_report", "compare", "cancel_run",
            "ideation_guide", "search", "bridges", "enablers", "explain", "sweep", "validate_slate", "preflight_slate", "run_slate"} <= names
    assert "Spark" in json.dumps(res.structured_content or [c.text for c in res.content])


# ---- ideation (I6) ----------------------------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
SLATE = (ROOT / "examples" / "ideation_slate.yaml").read_text()


def test_catalogue_queries_are_compact_and_quotable():
    r = core.search("keystone", text="mana")
    assert {"Eldritch Battery", "Mind Over Matter"} <= {x["name"] for x in r["results"]} and all("text" in x for x in r["results"])
    assert core.search("support", skill_types=["SummonsTotem"])["count"] > 0
    assert core.search("keystone", limit=2)["truncated"]
    assert "error" in core.search("class", text="x") and "error" in core.search("bogus")
    b = core.bridges("Armour", "Lightning", limit=2)
    assert sum(b["counts"].values()) > 0 and all(len(v) <= 2 for k, v in b.items() if isinstance(v, list))
    e = core.enablers("GeneratesCharges")
    assert e["supports_adding"] and "note" not in e
    assert "note" in core.enablers("generatescharges")          # case-sensitive type names get a hint, not silence
    x = core.explain("keystone", "eldritch battery")
    assert x["ok"] and "Convert 100% of maximum Energy Shield to maximum Mana" in x["text"]
    u = core.explain("unique", "Dream Fragments")
    assert "You cannot be Chilled or Frozen" in u["text"] and "all_lines" not in u
    assert core.explain("skill", "Cyclone")["status"] == "unresolved"   # PoE1-only name on the pinned data


def test_slate_validate_preflight_and_refusals():
    v = core.validate_slate(SLATE)
    assert v["ok"] and v["kept"] == 3 and all(c["kept"] and c["vector"] for c in v["candidates"])
    assert "structure_error" in core.validate_slate({"slate": 1, "bogus": 1})
    import yaml
    bad = yaml.safe_load(SLATE)
    bad["candidates"][0]["claims"][0]["cites"][0]["quote"] = "You cannot be Shocked or Frozen"
    r = core.validate_slate(bad)
    assert not r["candidates"][0]["kept"] and any(i["code"] == "quote_mismatch" for i in r["candidates"][0]["issues"])
    p = core.preflight_slate(SLATE, {"weapon": "Acrid Wand"}, workers=4)
    assert p["ok"] and "min" in p["summary"] and not p["rejected"] and "missing_bases" not in p
    assert core.preflight_slate(SLATE)["missing_bases"]
    assert "no gear bases" in core.start_slate(SLATE)["error"]
    assert "refused" in core.start_slate(SLATE, {"weapon": "Acrid Wand"}, max_minutes=0.01)
    assert "unknown slot" in core.start_slate(SLATE, {"hat": "x"})["error"]
    assert not list(Path(os.environ["POS_RUNS_DIR"]).iterdir())


def test_sweep_refuses_bad_kind_and_invalid_spec():
    assert "kind must be" in core.start_sweep(SPEC, "jewel")["error"]
    assert "kind must be" in core.start_sweep(SPEC, "unique:hat")["error"]
    assert not core.start_sweep({**SPEC, "main_skill": {"gem": "Sparkk"}}, "keystone")["ok"]


def test_job_kinds_share_state_and_report_files(runs):
    d = _fake_run(runs, "slate1", pid=2**22 - 1, report=False)
    m = json.loads((d / "meta.json").read_text()); m.update(job="slate", report="slate_report.md")
    (d / "meta.json").write_text(json.dumps(m))
    assert core.run_status("slate1")["state"] == "failed"           # report.md is not the slate's report
    (d / "slate_report.md").write_text("# Slate\n")
    (d / "slate_run.json").write_text("{}")
    st = core.run_status("slate1")
    assert st["state"] == "done" and st["job"] == "slate"
    g = core.get_report("slate1")
    assert g["ok"] and g["job"] == "slate" and g["report_md"].startswith("# Slate") and "slate_json" in g["files"]
    assert core.list_runs()["runs"][0]["job"] == "slate"


def test_ideate_prompt_carries_live_vocabulary_and_rules():
    from pos_catalogue import Catalogue
    from pos_mcp import ideate
    from pos_pipeline import data
    t = ideate.render("tanky lightning build that kills Arbiter on a budget", "no minions")
    cfg = data.ideation()
    assert "tanky lightning build" in t and "User constraints: no minions" in t
    assert Catalogue.load().pob_sha[:7] in t and "`arbiter_ash` boss" in t and "`mid`" in t
    assert "incomplete" in t                                          # unsourced benchmark is labelled
    assert f"at most {cfg['slate']['max_kept']}" in t and f"at least {cfg['diversity']['min_differing_fields']} of" in t
    for rule in ("PoE1", "verbatim", "No numbers", "no_metric", "key_pieces", "validate_slate", "preflight_slate", "run_slate",
                 "get_report", "not_load_bearing", "possibly_unmodelled"):
        assert rule in t, rule
    for rule in ("not in this PoE2 data", "Quotes are exempt", "ascendancy=", "weapon=<catalogue weapon base>", "weapon-only screen"):   # I7 fixes
        assert rule in t, rule
    import re
    assert not re.search(r"\{[a-z_0-9]+\}", t)                       # no unfilled placeholders
    assert "(no idea given" in ideate.render("  ")
    # meta lessons (cmsg_01RxGYnd78N9kMbbAJ5pWDhUX2GMWf6TSLPYKzmKmpb39v): patterns rendered as priors, ids citable
    assert "Priors from past metas" in t and "`stat_stacking`" in t and "archetype.patterns" in t
    assert "Defence (layers):" in t and "`max_resistance_push`" in t and "independent defence layers" in t
    assert "Righteous Fire" not in t and "Cast On Critical Strike" not in t


def test_meta_lessons_tool():
    r = core.meta_lessons()
    assert r["ok"] and {p["id"] for p in r["patterns"]} >= {"stat_stacking", "trigger_automation", "layered_mitigation"}
    assert all("examples" not in e for p in r["patterns"] for e in p["eras"])
    assert core.meta_lessons("stat_stacking")["patterns"][0]["id"] == "stat_stacking"
    assert not core.meta_lessons("nope")["ok"]


def test_sweep_weapon_and_unarmed_flags_reach_the_job(monkeypatch):
    seen = {}
    monkeypatch.setattr(core, "_launch", lambda kind, fn, text, argv, est, meta: seen.update(argv=argv(Path("/x")), meta=meta) or {"ok": True})
    core.start_sweep(SPEC, "keystone", weapon="Crude Bow")
    assert seen["argv"][-2:] == ["--weapon", "Crude Bow"] and seen["meta"]["weapon"] == "Crude Bow"
    core.start_sweep(SPEC, "keystone")
    assert "--weapon" not in seen["argv"]
    # a gearless candidate is refused unless the caller says it is deliberate (I12)
    assert "unarmed_ok" in core.start_slate(SLATE)["error"]
    assert "no gear bases" not in str(core.start_slate(SLATE, max_minutes=0.01, unarmed_ok=True))


def test_sweep_job_attack_skill_needs_a_weapon(tmp_path):
    """Real engine (I12): Boneshatter has no damage on the gearless seed; a plain mace base makes it evaluate."""
    import yaml
    from pos_mcp import jobs
    (tmp_path / "spec.yaml").write_text(yaml.safe_dump({"pob_sha": "601768b", "class": "Warrior", "ascendancy": "Titan", "level": 90,
                                                      "main_skill": {"gem": "Boneshatter"}, "tiers": ["mid"]}))
    assert jobs.sweep_job(str(tmp_path / "spec.yaml"), "keystone", str(tmp_path), top=3, workers=2, search=False) == 1
    assert not (tmp_path / "sweep.json").exists()
    assert jobs.sweep_job(str(tmp_path / "spec.yaml"), "keystone", str(tmp_path), top=3, workers=2, search=False, weapon="Aberrant Sledge") == 0
    j = json.loads((tmp_path / "sweep.json").read_text())
    assert j["baseline"] > 0 and "plain Aberrant Sledge" in j["seed"]
    assert jobs.sweep_job(str(tmp_path / "spec.yaml"), "keystone", str(tmp_path), top=3, workers=2, search=False, weapon="Spark") == 1


def test_sweep_job_end_to_end(tmp_path):
    """Real engine: ascendancy sweep on the unsearched Spark seed through the job entry point (about 30 s)."""
    import yaml
    from pos_mcp import jobs
    (tmp_path / "spec.yaml").write_text(yaml.safe_dump({**SPEC, "benchmarks": ["arbiter_ash"]}))
    assert jobs.sweep_job(str(tmp_path / "spec.yaml"), "ascendancy", str(tmp_path), top=5, workers=2, search=False) == 0
    j = json.loads((tmp_path / "sweep.json").read_text())
    assert j["kind"] == "ascendancy" and j["benchmark_options"] == "arbiter_ash" and j["entries"] and j["baseline"] > 0
    md = (tmp_path / "report.md").read_text()
    assert md.startswith("# Sweep: ascendancy") and "no support or tree search" in md
