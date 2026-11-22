"""Tool logic for the MCP server. No MCP import here, so it is unit-testable and reusable from scripts.

Every tool returns a JSON-able dict. Names reach the pipeline only through the catalogue: `run` refuses a spec that
does not validate, and `resolve` never guesses (exact match or ranked suggestions)."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import yaml

from pos_catalogue import KINDS, Catalogue
from pos_pipeline import SpecError, validate
from pos_pipeline.spec import parse_spec

ROOT = Path(__file__).resolve().parents[1]
MAX_REPORT_CHARS = 20000


def runs_dir() -> Path:
    p = Path(os.environ.get("POS_RUNS_DIR") or ROOT / "runs")
    p.mkdir(parents=True, exist_ok=True)
    return p


def _spec_from(spec: str | dict) -> Any:
    """Spec as a YAML/JSON string or an object -> BuildSpec. Raises SpecError on structure problems."""
    try:
        data = yaml.safe_load(spec) if isinstance(spec, str) else spec
    except yaml.YAMLError as e:
        raise SpecError(f"not valid YAML/JSON: {e}") from e
    return parse_spec(data)


def _issue(i) -> dict:
    d = {"severity": i.severity, "code": i.code, "path": i.path, "message": i.message}
    if i.confidence:
        d["confidence"] = i.confidence
    if i.suggestions:
        d["suggestions"] = list(i.suggestions)
    return d


def _entry(e: dict) -> dict:
    keep = ("id", "name", "kind", "level", "class", "base_type", "type", "tags")
    return {k: e[k] for k in keep if k in e} or {"name": e.get("name")}


def resolve(kind: str, names: list[str], pob_sha: str | None = None, limit: int = 5) -> dict:
    """Map free-text names to catalogue entries. Status per name: exact | ambiguous | unresolved (with suggestions)."""
    if kind not in KINDS:
        return {"error": f"kind must be one of {list(KINDS)}"}
    cat = Catalogue.load(pob_sha=pob_sha)
    out = []
    for n in names[:50]:
        r = cat.resolve(kind, n, limit=limit)
        out.append({"query": n, "status": r.status, "matches": [_entry(e) for e in r.matches],
                    "suggestions": [_entry(e) for e in r.suggestions]})
    return {"pob_sha": cat.pob_sha, "kind": kind, "results": out}


def validate_spec(spec: str | dict) -> dict:
    try:
        s = _spec_from(spec)
    except SpecError as e:
        return {"ok": False, "structure_error": str(e)}
    rep = validate(s, Catalogue.load(pob_sha=s.pob_sha))
    return {"ok": rep.ok, "metric": rep.metric, "metric_note": rep.metric_note, "issues": [_issue(i) for i in rep.issues]}


def import_pob(code: str) -> dict:
    """PoB share code or XML -> draft spec (YAML) plus warnings for everything dropped. Needs the engine (LuaJIT)."""
    from pos_engine.engine import PobEngine
    from pos_pipeline.assemble import import_pob as _imp

    cat = Catalogue.load()
    with PobEngine() as eng:
        s, issues = _imp(code.strip(), cat, eng)
    d = {"pob_sha": s.pob_sha, "class": s.class_, "ascendancy": s.ascendancy, "level": s.level,
         "main_skill": {"gem": s.main_skill},
         "fixed": {"supports": s.supports, "keystones": s.keystones, "notables": s.notables, "uniques": s.uniques},
         "tiers": s.tiers or ["mid"], "config_profile": s.config_profile}
    return {"spec_yaml": yaml.safe_dump(d, sort_keys=False), "issues": [_issue(i) for i in issues]}


def _bases(bases: dict[str, str]) -> tuple[dict[str, str], str | None]:
    from pos_pipeline.gear import SLOTS
    b = dict(bases)
    if "ring" in b:
        r = b.pop("ring")
        b.setdefault("ring_1", r); b.setdefault("ring_2", r)
    bad = [s for s in b if s not in SLOTS]
    return b, (f"unknown slot(s): {', '.join(bad)}; known: {', '.join(SLOTS)} (ring sets both rings)" if bad else None)


def preflight(spec: str | dict, bases: dict[str, str] | None = None, workers: int | None = None,
              realloc_rounds: int | None = None, max_minutes: float | None = None) -> dict:
    """Cost estimate without running. Also validates the spec."""
    from pos_pipeline.gear import SLOTS
    from pos_pipeline.orchestrate import DEFAULT_MAX_MINUTES, DEFAULT_REALLOC_ROUNDS, run

    v = validate_spec(spec)
    if not v["ok"]:
        return {"ok": False, "validation": v}
    s = _spec_from(spec)
    b, err = _bases(bases or {})
    if err:
        return {"ok": False, "error": err}
    r = run(s, None, skill_id="", dry_run=True, force=True, metric=v["metric"], slots=len(b) or len(SLOTS),  # type: ignore[arg-type]
            workers=workers or os.cpu_count() or 1, realloc_rounds=DEFAULT_REALLOC_ROUNDS if realloc_rounds is None else realloc_rounds,
            max_minutes=DEFAULT_MAX_MINUTES if max_minutes is None else max_minutes)
    e = r.estimate
    return {"ok": True, "summary": e.summary(), "over_cap": e.over_cap, "rate_sources": list(e.sources),
            "warnings": [i for i in v["issues"] if i["severity"] != "error"]}


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    try:  # zombie children count as dead
        return Path(f"/proc/{pid}/stat").read_text().split(")")[-1].split()[0] != "Z"
    except OSError:
        return True


def _active() -> list[str]:
    return [d.name for d in runs_dir().iterdir() if (d / "meta.json").exists() and _state(d.name)["state"] == "running"]


def start_run(spec: str | dict, bases: dict[str, str], *, workers: int | None = None, realloc_rounds: int | None = None,
              max_minutes: float | None = None, force: bool = False) -> dict:
    """Validate, check the cost cap, then start the run as a background process. Returns a run id at once."""
    pf = preflight(spec, bases, workers, realloc_rounds, max_minutes)
    if not pf["ok"]:
        return pf
    if not bases:
        return {"ok": False, "error": "no bases given: gear search needs one base per slot, e.g. {'weapon': 'Acrid Wand'}; resolve names with kind 'base'"}
    if pf["over_cap"] and not force:
        return {"ok": False, "refused": pf["summary"], "hint": "estimate is above the cap; tell the owner, then pass force=true or max_minutes"}
    live = _active()
    if live:
        return {"ok": False, "error": f"run {live[0]} is still running (one at a time, they share the CPUs); wait or cancel_run it"}
    rid = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]
    d = runs_dir() / rid
    d.mkdir()
    s = _spec_from(spec)
    (d / "spec.yaml").write_text(yaml.safe_dump(json.loads(json.dumps(spec if isinstance(spec, dict) else yaml.safe_load(spec))), sort_keys=False), encoding="utf-8")
    b, _ = _bases(bases)
    cmd = [sys.executable, "-m", "pos_pipeline", "run", str(d / "spec.yaml"), *[f"{k}={v}" for k, v in b.items()], "--out", str(d)]
    if workers:
        cmd += ["--workers", str(workers)]
    if realloc_rounds is not None:
        cmd += ["--realloc-rounds", str(realloc_rounds)]
    if max_minutes is not None:
        cmd += ["--max-minutes", str(max_minutes)]
    if force:
        cmd.append("--force")
    log = open(d / "log.txt", "w", encoding="utf-8")
    p = subprocess.Popen(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    (d / "meta.json").write_text(json.dumps({"pid": p.pid, "started": time.time(), "cmd": cmd[3:], "tiers": s.tiers,
                                              "estimate": pf["summary"]}), encoding="utf-8")
    return {"ok": True, "run_id": rid, "estimate": pf["summary"], "next": "poll run_status(run_id); then get_report(run_id)"}


def _state(run_id: str) -> dict:
    d = runs_dir() / Path(run_id).name        # no path traversal
    if not (d / "meta.json").exists():
        return {"state": "unknown", "error": f"no run {run_id!r}; known: {sorted(x.name for x in runs_dir().iterdir())[-10:]}"}
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    log = (d / "log.txt").read_text(encoding="utf-8", errors="replace").splitlines() if (d / "log.txt").exists() else []
    if (d / "cancelled").exists():
        state = "cancelled"
    elif (d / "report.md").exists():
        state = "done"
    elif _alive(meta["pid"]):
        state = "running"
    else:
        state = "failed"
    return {"state": state, "elapsed_s": round((time.time() - meta["started"]) if state == "running" else
                                                ((d / "log.txt").stat().st_mtime - meta["started"]) if log else 0),
            "estimate": meta["estimate"], "log_tail": log[-8:]}


def run_status(run_id: str) -> dict:
    return _state(run_id)


def cancel_run(run_id: str) -> dict:
    st = _state(run_id)
    if st["state"] != "running":
        return {"ok": False, "state": st["state"]}
    d = runs_dir() / Path(run_id).name
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    (d / "cancelled").write_text("1")
    try:
        os.killpg(meta["pid"], signal.SIGTERM)
    except OSError:
        pass
    return {"ok": True, "state": "cancelled"}


def get_report(run_id: str, max_chars: int = MAX_REPORT_CHARS) -> dict:
    """The deterministic report.md. Quote numbers only from it; truncated at max_chars (full file path returned)."""
    st = _state(run_id)
    if st["state"] != "done":
        return {"ok": False, **st}
    d = runs_dir() / Path(run_id).name
    text = (d / "report.md").read_text(encoding="utf-8")
    return {"ok": True, "report_md": text[:max_chars], "truncated": len(text) > max_chars, "chars": len(text),
            "files": {"report": str(d / "report.md"), "results_db": str(d / "results.sqlite"), "run_json": str(d / "run.json")}}


def _best(run_id: str) -> dict | str:
    d = runs_dir() / Path(run_id).name
    if not (d / "run.json").exists():
        return f"run {run_id!r} has no run.json (state: {_state(run_id)['state']})"
    j = json.loads((d / "run.json").read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for s in j["seeds"]:
        for t, tr in s["tiers"].items():
            if tr.get("ok") and tr.get("value") is not None and (t not in out or tr["value"] > out[t]["value"]):
                out[t] = {"value": tr["value"], "variant": s["variant"], "price": tr.get("price"), "floors_met": tr.get("floors_met")}
    return {"metric": j["metric"], "best": out}


def compare(run_a: str, run_b: str) -> dict:
    """Best result per tier in two runs, with the delta. Only comparable when both runs used the same metric."""
    a, b = _best(run_a), _best(run_b)
    for r in (a, b):
        if isinstance(r, str):
            return {"ok": False, "error": r}
    note = None if a["metric"] == b["metric"] else f"metrics differ ({a['metric']} vs {b['metric']}): values are not comparable"
    tiers = {}
    for t in sorted(set(a["best"]) | set(b["best"])):
        x, y = a["best"].get(t), b["best"].get(t)
        tiers[t] = {"a": x, "b": y, "delta_pct": round(100 * (y["value"] / x["value"] - 1), 1) if x and y and x["value"] and not note else None}
    return {"ok": True, "metric_a": a["metric"], "metric_b": b["metric"], "note": note, "tiers": tiers}


def list_runs(limit: int = 10) -> dict:
    ids = sorted(d.name for d in runs_dir().iterdir() if (d / "meta.json").exists())[-limit:]
    return {"runs": [{"run_id": i, "state": _state(i)["state"]} for i in ids]}
