"""Background job entry points the MCP server launches (`python -m pos_mcp.jobs ...`). Each writes its report file last,
so the file's existence means done (pos_mcp.core._state).

sweep SPEC KIND --out DIR [--top N] [--workers W] [--no-search] [--weapon BASE]
    Probe seed = the spec's first variant, assembled; unless --no-search, supports-searched and tree-searched (cap 200)
    so keystone deltas are not dominated by path nodes (docs/sweep.md). --weapon BASE equips a plain unmodded weapon base
    first, so an attack main skill evaluates (the seed otherwise has no gear). Metric = the spec's metric under the first boss
    benchmark's PoB options when the spec names benchmarks. Writes sweep.json and report.md."""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path


def _flag_note(flags: list[str]) -> str:
    notes = {"audit_outlier": "audit: >3x baseline, check for an engine artefact before trusting",
             "possibly_unmodelled": "zero delta though it has text: PoB may not model it, or it does not touch this metric",
             "over_budget": "path costs more than the unspent points: delta is on top of the full tree, not a trade",
             "unparsed": "PoB cannot parse all its lines: not scored", "unreachable": "tree cannot reach it"}
    return "; ".join(notes.get(f, f) for f in flags)


def sweep_job(spec_path: str, kind: str, out: str, top: int, workers: int, search: bool, weapon: str | None = None) -> int:
    from pos_catalogue import Catalogue
    from pos_engine.engine import PobEngine
    from pos_pool.pool import EnginePool
    from pos_pipeline import load_spec, validate
    from pos_pipeline.benchmarks import benchmarks, pob_options
    from pos_pipeline.orchestrate import engine_stages
    from pos_pipeline.assemble import variants
    from pos_pipeline.sweep import equip_probe_weapon, sweep

    d = Path(out)
    spec = load_spec(spec_path)
    cat = Catalogue.load(pob_sha=spec.pob_sha)
    rep = validate(spec, cat)
    if not rep.ok:
        print("spec does not validate: " + "; ".join(i.message for i in rep.errors)); return 1
    v = variants(spec)[0]
    with engine_stages(spec, cat, rep, {}, workers=workers, tree_caps=(200,)) as (st, skill_of):
        sk = skill_of(v)
        a = st.assemble(v)
        if not a.ok:
            print("assemble failed: " + "; ".join(i.message for i in a.issues if i.severity == "error")); return 1
        xml, seed_note = a.xml, "assembled seed, no support or tree search (keystone deltas include path nodes)"
        if weapon:
            try:
                with PobEngine() as weng:
                    xml = equip_probe_weapon(cat, weng, xml, weapon)
            except ValueError as ex:
                print(str(ex)); return 1
            seed_note += f"; plain {weapon} in Weapon 1 (implicits only)"
        if search:
            sup = st.supports(xml, sk)
            xml = st.apply_supports(xml, sk, list(sup.best.supports))
            print(f"probe seed supports {sup.gain:+.1%}", flush=True)
            [tr] = st.trees([xml])
            if tr.ok:
                xml, seed_note = tr.xml, f"assembled seed + searched supports ({', '.join(sup.best.supports) or 'none'}) + searched tree (cap 200), no gear"
            else:
                seed_note = f"tree search failed ({tr.error}); assembled seed with searched supports"
            print("probe seed ready", flush=True)
    bms = benchmarks()
    bid = next((b for b in spec.benchmarks if bms.get(b, {}).get("kind") == "boss"), None)
    options = pob_options(bms[bid]) if bid else None
    with PobEngine() as eng:   # fail fast: a seed with no damage gives all-zero deltas (an attack skill without a weapon)
        eng.load_build_xml(xml)
        eng.set_config(options=dict(options) if options else None)
        if not float(eng.get_stats([rep.metric])["stats"].get(rep.metric) or 0.0) > 0:
            print(f"probe seed computes 0 {rep.metric}: nothing to measure against. " +
                  ("The weapon base does not fit the main skill." if weapon else
                   "An attack main skill needs a weapon on the probe seed: pass --weapon BASE (spells need none)."))
            return 1
    with PobEngine() as eng, EnginePool(workers=workers) as pool:
        s = sweep(cat, pool, xml, kind, rep.metric, options=options, engine=eng, skill_id=sk)
    j = {"kind": s.kind, "metric": s.metric, "baseline": s.baseline, "benchmark_options": bid, "seed": seed_note, "variant": v,
         "evals": s.evals, "seconds": round(s.seconds, 1), "notes": s.notes, "entries": [asdict(e) for e in s.entries]}
    (d / "sweep.json").write_text(json.dumps(j, indent=1, default=str), encoding="utf-8")
    lines = [f"# Sweep: {s.kind} on {s.metric}", "",
             f"Probe seed: {seed_note}. Baseline {s.metric} {s.baseline:,.1f}" + (f" under {bid} options" if bid else "") +
             f". {len(s.entries)} entries, {s.evals} evals, {s.seconds:.0f} s.",
             "", "Deltas are one change at a time on this seed, not a finished build: leads, not results. A defensive entry shows zero "
             "under a damage metric by design. Engine numbers only; quote them as sweep deltas.", "",
             "| # | entry | delta | rel | points | flags |", "|---|---|---|---|---|---|"]
    shown = [e for e in s.entries if e.delta is not None][:top]
    for n, e in enumerate(shown, 1):
        lines.append(f"| {n} | {e.name} | {e.delta:+,.1f} | {e.rel:+.1%} | {'' if e.points is None else e.points} | {_flag_note(e.flags)} |"
                     if e.rel is not None else f"| {n} | {e.name} | {e.delta:+,.1f} | | | {_flag_note(e.flags)} |")
    for flag in ("possibly_unmodelled", "audit_outlier"):
        fl = [e.name for e in s.flagged(flag) if e not in shown]
        if fl:
            lines += ["", f"Also {flag} (not in the top {top}): " + ", ".join(fl[:30]) + (" ..." if len(fl) > 30 else "")]
    skipped = [e for e in s.entries if e.delta is None]
    if skipped:
        lines += ["", f"Not evaluated: {len(skipped)} (" + ", ".join(sorted({f for e in skipped for f in e.flags})) + ")"]
    lines += [f"- note: {n}" for n in s.notes]
    (d / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m pos_mcp.jobs")
    sub = ap.add_subparsers(dest="job", required=True)
    sw = sub.add_parser("sweep")
    sw.add_argument("spec"); sw.add_argument("kind"); sw.add_argument("--out", required=True)
    sw.add_argument("--top", type=int, default=20); sw.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) // 2))   # 4 workers on 4 vCPU/16 GB OOM-killed (2026-11-22)
    sw.add_argument("--no-search", action="store_true")
    sw.add_argument("--weapon", default=None, help="plain weapon base to equip on the probe seed (needed for attack main skills)")
    a = ap.parse_args(argv)
    return sweep_job(a.spec, a.kind, a.out, a.top, a.workers, not a.no_search, a.weapon)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
