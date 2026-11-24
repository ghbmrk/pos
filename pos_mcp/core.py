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
              realloc_rounds: int | None = None, max_minutes: float | None = None, rounds: int = 1) -> dict:
    """Cost estimate without running. Also validates the spec."""
    from pos_pipeline.orchestrate import DEFAULT_MAX_MINUTES, DEFAULT_REALLOC_ROUNDS, gear_slot_count, run

    v = validate_spec(spec)
    if not v["ok"]:
        return {"ok": False, "validation": v}
    s = _spec_from(spec)
    b, err = _bases(bases or {})
    if err:
        return {"ok": False, "error": err}
    r = run(s, None, skill_id="", dry_run=True, force=True, metric=v["metric"], slots=gear_slot_count(s, b),  # type: ignore[arg-type]
            workers=workers or os.cpu_count() or 1, realloc_rounds=DEFAULT_REALLOC_ROUNDS if realloc_rounds is None else realloc_rounds,
            max_minutes=DEFAULT_MAX_MINUTES if max_minutes is None else max_minutes, rounds=rounds)
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
              max_minutes: float | None = None, force: bool = False, allow_assumed: bool = False, rounds: int = 1) -> dict:
    """Validate, check the cost cap, then start the run as a background process. Returns a run id at once.
    A spec with `companion.assumed` (ASSUMED Squire what-if) runs only with allow_assumed=True."""
    pf = preflight(spec, bases, workers, realloc_rounds, max_minutes, rounds)
    if not pf["ok"]:
        return pf
    sc = ((_spec_from(spec).companion.assumed if _spec_from(spec).companion else None) or {}).get("scenario")
    if sc and not allow_assumed:
        return {"ok": False, "refused": "spec uses the ASSUMED Squire what-if (companion.assumed): its numbers rest on assumptions, not game data",
                "hint": "pass allow_assumed=true only when the owner asked for an assumed what-if; see docs/squire-assumed.md"}
    if not bases:
        return {"ok": False, "error": "no bases given: gear search needs one base per slot, e.g. {'weapon': 'Acrid Wand'}; resolve names with kind 'base'"}
    if pf["over_cap"] and not force:
        return {"ok": False, "refused": pf["summary"], "hint": "estimate is above the cap; tell the owner, then pass force=true or max_minutes"}
    s = _spec_from(spec)
    b, _ = _bases(bases)
    extra = (["--workers", str(workers)] if workers else []) + (["--realloc-rounds", str(realloc_rounds)] if realloc_rounds is not None else []) \
        + (["--max-minutes", str(max_minutes)] if max_minutes is not None else []) + (["--force"] if force else []) \
        + (["--assumed"] if sc else []) + (["--rounds", str(rounds)] if rounds > 1 else [])
    return _launch("run", "spec.yaml", _plain(spec), lambda d: ["-m", "pos_pipeline", "run", str(d / "spec.yaml"),
                   *[f"{k}={v}" for k, v in b.items()], "--out", str(d), *extra], pf["summary"], {"tiers": s.tiers, **({"assumed": sc} if sc else {})})


def _plain(doc: str | dict) -> Any:
    """YAML text or object -> plain JSON-able object (what gets written to the job directory)."""
    return json.loads(json.dumps(doc if isinstance(doc, dict) else yaml.safe_load(doc)))


REPORTS = {"run": "report.md", "slate": "slate_report.md", "sweep": "report.md", "play": "report.md"}


def _launch(job: str, input_name: str, doc: Any, argv, estimate: str, extra_meta: dict | None = None) -> dict:
    """Start `python <argv(dir)>` in a new job directory, detached. One job at a time: all jobs share the CPUs."""
    live = _active()
    if live:
        return {"ok": False, "error": f"job {live[0]} is still running (one at a time, they share the CPUs); wait or cancel_run it"}
    rid = time.strftime("%Y%m%d-%H%M%S-") + job[:2] + uuid.uuid4().hex[:4]
    d = runs_dir() / rid
    d.mkdir()
    (d / input_name).write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    cmd = [sys.executable, *argv(d)]
    log = open(d / "log.txt", "w", encoding="utf-8")
    p = subprocess.Popen(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    (d / "meta.json").write_text(json.dumps({"pid": p.pid, "started": time.time(), "job": job, "report": REPORTS[job],
                                              "cmd": cmd[1:], "estimate": estimate, **(extra_meta or {})}), encoding="utf-8")
    return {"ok": True, "run_id": rid, "job": job, "estimate": estimate, "next": "poll run_status(run_id) about once a minute; then get_report(run_id)"}


def _state(run_id: str) -> dict:
    d = runs_dir() / Path(run_id).name        # no path traversal
    if not (d / "meta.json").exists():
        return {"state": "unknown", "error": f"no run {run_id!r}; known: {sorted(x.name for x in runs_dir().iterdir())[-10:]}"}
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    log = (d / "log.txt").read_text(encoding="utf-8", errors="replace").splitlines() if (d / "log.txt").exists() else []
    if (d / "cancelled").exists():
        state = "cancelled"
    elif (d / meta.get("report", "report.md")).exists():
        state = "done"
    elif _alive(meta["pid"]):
        state = "running"
    else:
        state = "failed"
    return {"state": state, "job": meta.get("job", "run"), "assumed": meta.get("assumed"), "elapsed_s": round((time.time() - meta["started"]) if state == "running" else
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
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    rp = d / meta.get("report", "report.md")
    text = rp.read_text(encoding="utf-8")
    files = {"report": str(rp), **{k: str(d / f) for k, f in (("results_db", "results.sqlite"), ("run_json", "run.json"),
             ("slate_db", "slate_results.sqlite"), ("slate_json", "slate_run.json"), ("sweep_json", "sweep.json")) if (d / f).exists()}}
    return {"ok": True, "job": meta.get("job", "run"), "report_md": text[:max_chars], "truncated": len(text) > max_chars,
            "chars": len(text), "files": files}


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


def compare(run_a: str, run_b: str, include_assumed: bool = False) -> dict:
    """Best result per tier in two runs, with the delta. Only comparable when both runs used the same metric.
    Runs of the ASSUMED Squire what-if are refused unless include_assumed=True, and the result then carries the banner."""
    ass = [r for r in (run_a, run_b) if _state(r).get("assumed")]
    if ass and not include_assumed:
        return {"ok": False, "error": f"run(s) {ass} are ASSUMED Squire what-ifs; pass include_assumed=true to compare them (numbers rest on assumptions)"}
    a, b = _best(run_a), _best(run_b)
    for r in (a, b):
        if isinstance(r, str):
            return {"ok": False, "error": r}
    note = None if a["metric"] == b["metric"] else f"metrics differ ({a['metric']} vs {b['metric']}): values are not comparable"
    tiers = {}
    for t in sorted(set(a["best"]) | set(b["best"])):
        x, y = a["best"].get(t), b["best"].get(t)
        tiers[t] = {"a": x, "b": y, "delta_pct": round(100 * (y["value"] / x["value"] - 1), 1) if x and y and x["value"] and not note else None}
    return {"ok": True, "metric_a": a["metric"], "metric_b": b["metric"], "note": note, "tiers": tiers,
            **({"ASSUMED": "includes ASSUMED Squire what-if runs: numbers rest on assumptions, not game data"} if ass else {})}


def list_runs(limit: int = 10, include_assumed: bool = False) -> dict:
    """Recent jobs. ASSUMED Squire what-if runs are hidden unless include_assumed=True (then each is flagged)."""
    all_ids = sorted(d.name for d in runs_dir().iterdir() if (d / "meta.json").exists())
    rows = [(i, _state(i)) for i in all_ids]
    hidden = sum(1 for _, st in rows if st.get("assumed"))
    rows = [(i, st) for i, st in rows if include_assumed or not st.get("assumed")][-limit:]
    out = {"runs": [{"run_id": i, "job": st["job"], "state": st["state"], **({"ASSUMED": st["assumed"]} if st.get("assumed") else {})} for i, st in rows]}
    if hidden and not include_assumed:
        out["hidden_assumed"] = hidden
    return out


# ---- ideation (I6, docs/ideation.md): catalogue queries, slate gate, sweeps, slate runs -------------------------
SEARCH_LIMIT = 25
TEXT_CHARS = 240


def _card(kind: str, e: dict, lines: int = 4) -> dict:
    """Compact entry for query results: name, quotable text (trimmed; `explain` gives it in full) and the fields that matter for ideas."""
    from pos_catalogue.query import TEXT_KINDS, texts
    d: dict[str, Any] = {"kind": kind, "name": e.get("name")}
    if kind in TEXT_KINDS:
        t = texts(kind, e)
        d["text"] = [x if len(x) <= TEXT_CHARS else x[:TEXT_CHARS] + "..." for x in t[:lines]]
        if len(t) > lines:
            d["more_lines"] = len(t) - lines
    for k in ("skill_types", "require_types", "add_types", "ascendancy", "class", "base", "file", "type", "tags"):
        if e.get(k):
            d["slot" if k == "file" else k] = e[k]
    return d


def search(kind: str, text: str | None = None, skill_types: list[str] | None = None, tags: list[str] | None = None,
           ascendancy: str | None = None, class_: str | None = None, limit: int = SEARCH_LIMIT) -> dict:
    from pos_catalogue import query
    if kind not in KINDS:
        return {"error": f"kind must be one of {list(KINDS)}"}
    if text and kind not in query.TEXT_KINDS:
        return {"error": f"text search needs a kind with game text: {list(query.TEXT_KINDS)}"}
    cat = Catalogue.load()
    hits = query.search(cat, kind, text=text, skill_types=skill_types, tags=tags, ascendancy=ascendancy, class_=class_)
    lim = max(1, min(limit, 100))
    return {"pob_sha": cat.pob_sha, "count": len(hits), "results": [_card(kind, e) for e in hits[:lim]],
            **({"truncated": True} if len(hits) > lim else {})}


def enablers(skill_type: str, limit: int = 15) -> dict:
    from pos_catalogue import query
    cat = Catalogue.load()
    r = query.enablers(cat, skill_type)
    kind_of = {"supports_adding": "support", "keystones": "keystone", "notables": "notable", "uniques": "unique"}
    out = {k: [_card(kind_of[k], e, 2) for e in v[:limit]] for k, v in r.items()}
    counts = {k: len(v) for k, v in r.items()}
    note = None if any(counts.values()) else "nothing found: skill types are exact catalogue names (case-sensitive), e.g. from explain(kind='skill').skill_types"
    return {"pob_sha": cat.pob_sha, "skill_type": skill_type, "counts": counts, **out, **({"note": note} if note else {})}


def bridges(term_a: str, term_b: str, limit: int = 10) -> dict:
    from pos_catalogue import query
    cat = Catalogue.load()
    r = query.bridges(cat, term_a, term_b)
    return {"pob_sha": cat.pob_sha, "terms": [term_a, term_b], "counts": {k: len(v) for k, v in r.items()},
            **{k: [_card(k[:-1], e, 3) for e in v[:limit]] for k, v in r.items()}}


def meta_lessons(pattern: str | None = None) -> dict:
    """Abstract scaling patterns from past metas (data/meta_lessons.yaml), without past-meta names."""
    from pos_pipeline import meta_lessons as ml
    if pattern and pattern not in ml.ids():
        return {"ok": False, "error": f"unknown pattern {pattern!r}", "patterns": ml.ids()}
    return {"ok": True, "rules": ml.load()["rules"], "patterns": ml.public(pattern)}


def explain(kind: str, name: str) -> dict:
    """Full quotable text of one entry, resolved exactly by name (or catalogue id)."""
    from pos_catalogue import query
    from pos_catalogue.catalogue import _KINDS
    if kind not in query.TEXT_KINDS:
        return {"error": f"kind must be one of {list(query.TEXT_KINDS)}"}
    cat = Catalogue.load()
    r = cat.resolve(kind, name)
    if r.status == "unresolved":
        return {"ok": False, "status": "unresolved", "query": name, "suggestions": [_entry(e) for e in r.suggestions]}
    e = r.matches[0]
    out = {"ok": True, "pob_sha": cat.pob_sha, **query.explain(cat, kind, e[_KINDS[kind][1]])}
    if r.status == "ambiguous":
        out["note"] = f"{len(r.matches)} entries share this name; showing the first"
    if kind == "unique":
        out.pop("all_lines", None)           # older-variant lines are not quotable; `text` is the newest variant
    out["quote_rule"] = "a slate cite's quote must be a substring of one `text` line (case/whitespace-insensitive) and at least 12 characters"
    return out


def _slate_from(slate: str | dict):
    from pos_pipeline.slate import parse_slate
    try:
        data = yaml.safe_load(slate) if isinstance(slate, str) else slate
    except yaml.YAMLError as e:
        raise SpecError(f"not valid YAML/JSON: {e}") from e
    return parse_slate(data)


def validate_slate(slate: str | dict) -> dict:
    from pos_pipeline.slate import validate_slate as _vs
    try:
        s = _slate_from(slate)
    except SpecError as e:
        return {"ok": False, "structure_error": str(e)}
    rep = _vs(s, Catalogue.load(pob_sha=s.pob_sha))
    return {"ok": rep.ok, "kept": len(rep.kept), "submitted": len(rep.candidates), "slate_issues": [_issue(i) for i in rep.issues],
            "candidates": [{"name": r.name, "kept": r.kept, "vector": r.vector, "metric": r.metric,
                            "issues": [_issue(i) for i in r.issues]} for r in rep.candidates]}


def preflight_slate(slate: str | dict, bases: dict[str, str] | None = None, workers: int | None = None,
                    deepen_k: int | None = None, max_minutes: float | None = None) -> dict:
    """Validate the slate and estimate screen + ablation + deepen time without running."""
    from pos_pipeline.gear import SLOTS
    from pos_pipeline.orchestrate import DEFAULT_MAX_MINUTES
    from pos_pipeline.slate_run import estimate_slate

    v = validate_slate(slate)
    if not v["ok"]:
        return {"ok": False, "validation": v}
    s = _slate_from(slate)
    b, err = _bases(bases or {})
    if err:
        return {"ok": False, "error": err}
    kept = {r["name"] for r in v["candidates"] if r["kept"]}
    cands = [c for c in s.candidates if c.name in kept]
    no_bases = [c.name for c in cands if not {**b, **c.bases}]
    est = estimate_slate(cands, s.brief, {c.name: len({**b, **c.bases}) or len(SLOTS) for c in cands}, workers or os.cpu_count() or 1,
                         max_minutes=DEFAULT_MAX_MINUTES if max_minutes is None else max_minutes, k=deepen_k)
    out = {"ok": True, "summary": est.summary(), "over_cap": est.over_cap, "kept": sorted(kept), "rate_sources": list(est.sources),
           "rejected": [{"name": r["name"], "errors": [i for i in r["issues"] if i["severity"] == "error"]} for r in v["candidates"] if not r["kept"]]}
    if no_bases:
        out["missing_bases"] = no_bases
    return out


def start_slate(slate: str | dict, bases: dict[str, str] | None = None, *, workers: int | None = None, deepen_k: int | None = None,
                max_minutes: float | None = None, force: bool = False, unarmed_ok: bool = False) -> dict:
    pf = preflight_slate(slate, bases, workers, deepen_k, max_minutes)
    if not pf["ok"]:
        return pf
    if pf.get("missing_bases") and not unarmed_ok:
        return {"ok": False, "error": f"no gear bases for {pf['missing_bases']}: pass bases (slot -> base) or give the candidate `bases:`; resolve names with kind 'base'. A deliberately unarmed / gearless candidate: unarmed_ok=true (its numbers are the bare build)"}
    if pf["over_cap"] and not force:
        return {"ok": False, "refused": pf["summary"], "hint": "estimate is above the cap; tell the user, then pass force=true or max_minutes, or cut candidates / deepen_k"}
    b, _ = _bases(bases or {})
    extra = (["--workers", str(workers)] if workers else []) + (["--deepen-k", str(deepen_k)] if deepen_k is not None else []) \
        + (["--max-minutes", str(max_minutes)] if max_minutes is not None else []) + (["--force"] if force else [])
    r = _launch("slate", "slate.yaml", _plain(slate), lambda d: ["-m", "pos_pipeline", "slate", "run", str(d / "slate.yaml"),
                *[f"{k}={v}" for k, v in b.items()], "--out", str(d), *extra], pf["summary"], {"kept": pf["kept"]})
    if r.get("ok") and pf["rejected"]:
        r["rejected"] = pf["rejected"]
    return r


def start_play(prompt: str, slate: str | dict, bases: dict[str, str] | None = None, *, workers: int | None = None, k: int = 3, outer_rounds: int = 2,
               children: int = 1, inner_rounds: int = 3, max_minutes: float | None = None, force: bool = False, allow_assumed: bool = False,
               assume: list[str] | None = None, unarmed_ok: bool = False) -> dict:
    """L6: the whole loop as one background job: screen the slate's ideas, creative improvement rounds, inner loop on the finalists, player report."""
    from pos_pipeline.gear import SLOTS
    from pos_pipeline.orchestrate import DEFAULT_MAX_MINUTES
    from pos_pipeline.play import play_estimate

    v = validate_slate(slate)
    if not v["ok"]:
        return {"ok": False, "validation": v}
    s = _slate_from(slate)
    b, err = _bases(bases or {})
    if err:
        return {"ok": False, "error": err}
    kept = {r["name"] for r in v["candidates"] if r["kept"]}
    cands = [c for c in s.candidates if c.name in kept]
    no_bases = [c.name for c in cands if not {**b, **c.bases}]
    if no_bases and not unarmed_ok:
        return {"ok": False, "error": f"no gear bases for {no_bases}: pass bases (slot -> base) or give the candidate `bases:`; unarmed_ok=true runs them with no searched gear"}
    cap = DEFAULT_MAX_MINUTES if max_minutes is None else max_minutes
    est = play_estimate(cands, s.brief, b, workers or os.cpu_count() or 1, k=k, outer_rounds=outer_rounds, children=children, inner_rounds=inner_rounds, max_minutes=cap)
    if est.over_cap and not force:
        return {"ok": False, "refused": est.summary(), "hint": "estimate is above the cap; tell the user, then pass force=true or max_minutes, or cut ideas, k, rounds"}
    extra = (["--workers", str(workers)] if workers else []) + (["--max-minutes", str(max_minutes)] if max_minutes is not None else []) \
        + (["--force"] if force else []) + (["--assumed"] if allow_assumed else []) + [x for a in (assume or []) for x in ("--assume", a)]
    return _launch("play", "slate.yaml", _plain(slate), lambda d: ["-m", "pos_pipeline", "play", prompt, "--slate", str(d / "slate.yaml"),
                   *[f"{k_}={v_}" for k_, v_ in b.items()], "--out", str(d), "--k", str(k), "--outer-rounds", str(outer_rounds), "--children", str(children),
                   "--inner-rounds", str(inner_rounds), *extra], est.summary(), {"kept": sorted(kept)})


SWEEP_KINDS = ("keystone", "ascendancy", "support", "unique:<slot>")


def start_sweep(spec: str | dict, kind: str, *, searched: bool = True, top: int = 20, workers: int | None = None,
                weapon: str | None = None) -> dict:
    from pos_pipeline.gear import SLOTS
    if not (kind in ("keystone", "ascendancy", "support") or (kind.startswith("unique:") and kind[7:] in SLOTS)):
        return {"ok": False, "error": f"kind must be one of {list(SWEEP_KINDS)}; slots: {', '.join(SLOTS)}"}
    v = validate_spec(spec)
    if not v["ok"]:
        return {"ok": False, "validation": v}
    est = "about 2 min (probe seed: supports + tree search ~1.3 min on 4 vCPU, then the sweep 10-25 s)" if searched else "under 1 min"
    extra = (["--workers", str(workers)] if workers else []) + ([] if searched else ["--no-search"]) + (["--weapon", weapon] if weapon else [])
    return _launch("sweep", "spec.yaml", _plain(spec), lambda d: ["-m", "pos_mcp.jobs", "sweep", str(d / "spec.yaml"), kind,
                   "--out", str(d), "--top", str(top), *extra], est, {"kind": kind, **({"weapon": weapon} if weapon else {})})


def ceilings(build: str, metric: str = "FullDPS", ids: list[str] | None = None, required: float | None = None,
             lines: dict[str, str] | None = None) -> dict:
    """Uptime ceilings (L5b) for mechanics PoB cannot calculate, on a PoB build (XML text)."""
    from pos_pipeline import ceilings as C
    xml = build.strip()
    if not xml.startswith("<"):
        return {"error": "build must be PoB build XML text (a run's builds are exported as XML)"}
    try:
        res = C.evaluate(xml, ids, metric=metric, lines=lines)
        joint = C.interaction(res, xml, metric=metric)
    except Exception as ex:
        return {"error": f"{type(ex).__name__}: {ex}"}
    return {"results": [r.to_dict() for r in res], "joint": joint, "text": C.render(res, metric, required, joint)}


def diagnose(build: str, metric: str = "FullDPS", benchmarks: list[str] | None = None, top: int = 8) -> dict:
    """Diagnose a PoB build (XML text): binding constraint, levers by shadow price, probes that failed calibration."""
    from pos_pipeline.diagnose import diagnose as _diag, render
    xml = build.strip()
    if not xml.startswith("<"):
        return {"error": "build must be PoB build XML text (a run's builds are exported as XML)"}
    try:
        d = _diag(xml, metric, benchmarks or [])
    except Exception as ex:
        return {"error": f"{type(ex).__name__}: {ex}"}
    out = d.to_dict()
    out["probes"] = out["probes"][:top]
    out["text"] = render(d, top)
    return out
