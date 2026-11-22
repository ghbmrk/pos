"""Report (G8b + B4, docs/pipeline.md section 5): ranked variants per tier as report.md plus results.sqlite.

Input is the dict form of a `RunResult` (`RunResult.to_dict()` or run.json), so a report can be re-rendered from disk
without an engine. Every number shown is a PoB output, a benchmark formula over PoB outputs, or is labelled
(`~` price estimate, `proxy`, `ASSUMPTION`). Nothing here supplies a game fact."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .benchmarks import benchmarks, validate_benchmark

RESISTS = ("FireResist", "ColdResist", "LightningResist")


# ---- run metadata (stored in run.json so a report is self-contained) ---------------------------------------
def run_meta(spec, bench_ids: list[str]) -> dict[str, Any]:
    bm = {}
    for bid in bench_ids:
        errors, unsourced = validate_benchmark(bid)
        if errors:
            raise ValueError("; ".join(errors))
        b = benchmarks()[bid]
        assumptions = sorted({k for k, v in _cells(b) if "ASSUMPTION" in str(v.get("source", ""))})
        bm[bid] = {"kind": b["kind"], "patch": b["patch"], "description": b.get("description", ""),
                   "unsourced": [u.split(".", 1)[1] for u in unsourced], "assumptions": assumptions}
    return {"pob_sha": spec.pob_sha, "class": spec.class_, "ascendancy": spec.ascendancy, "level": spec.level,
            "main_skill": spec.main_skill, "config_profile": spec.config_profile, "tiers": list(spec.tiers) or ["mid"],
            "benchmarks": bm, "metric_note": "",
            "limitations": ([f"companion {spec.companion.kind}: separate_build model (own PoB build, effects applied as config options "
                             "from data/actors.yaml); the table's metric column is the player without effects, the companion's "
                             "gear is not searched (K3)"] if getattr(spec, "companion", None) else [])}


def _cells(b: dict):
    from .benchmarks import _cells as cells
    return cells(b)


# ---- formatting helpers ------------------------------------------------------------------------------------
def _num(x, nd: int = 0) -> str:
    return "n/a" if x is None else f"{x:,.{nd}f}"


def _effects(ac: dict) -> str:
    txt = ", ".join(f"{e['id']} x{e['uptime']:g}" for e in ac["effects"])
    return txt + (" (uptime-blended: linear on/off approximation)" if ac.get("blended") else "")


def _actor_cells(ac: dict) -> list[str]:
    if not ac or ac.get("error"):
        return ["n/a"] * 4
    return [_num(ac.get("main"), 1) + ("*" if ac.get("blended") else ""), _num(ac.get("companion"), 1),
            _num(ac.get("total"), 1), _num(ac.get("without_companion"), 1)]


def _gate(g) -> str:
    return {True: "pass", False: "FAIL", None: "n/a"}[g]


def _res(stats: dict) -> str:
    vals = [stats.get(k) for k in RESISTS]
    return "n/a" if None in vals else f"{min(vals):.0f}%" + ("" if min(vals) >= 75 else " (<75 uncapped)")


def _axes(v: dict) -> str:
    return ", ".join(f"{k}={x}" for k, x in v.items()) or "(no axes)"


def _bench_cell(b: dict | None) -> str:
    if not b:
        return "n/a"
    if "error" in b:
        return f"error: {b['error']}"
    incomplete = any(str(f).startswith("incomplete") for f in b.get("flags", []))
    mark = " incomplete" if incomplete else ""
    if "ttk_s" in b:  # boss
        ttk = "TTK n/a" if b["ttk_s"] is None else f"TTK {b['ttk_s']:.1f}s {_gate(b.get('gate_ttk'))}"
        surv = {True: "survives", False: "DIES", None: "survival n/a"}[b.get("survive")]
        if b.get("survive_basis") != "named":
            surv += " (named hits unsourced)"
        return f"{ttk}; {surv}; EHP {_num(b.get('ehp'))}{mark}"
    clear = "clear n/a" if b.get("clear_s") is None else f"clear {b['clear_s']:.1f} proxy-s {_gate(b.get('gate_clear'))}"
    cov = "" if b.get("coverage") is None else f"; coverage {b['coverage']:.0%}"
    return f"{clear}{cov}{mark}"


def ranked(d: dict) -> dict[str, list[tuple[dict, dict]]]:
    """tier -> [(seed, tier_run)] best first; ties broken by axes text so output is deterministic."""
    out: dict[str, list] = {}
    for s in d["seeds"]:
        for t, tr in s["tiers"].items():
            if tr["ok"] and tr["value"] is not None:
                out.setdefault(t, []).append((s, tr))
    for rows in out.values():
        rows.sort(key=lambda r: (-r[1]["value"], _axes(r[0]["variant"])))
    return out


# ---- markdown ----------------------------------------------------------------------------------------------
def render_markdown(d: dict) -> str:
    m, metric = d.get("meta", {}), d["metric"]
    L: list[str] = []
    a = L.append
    a(f"# Ranked report: {m.get('class')} {m.get('ascendancy') or ''} L{m.get('level')}, {m.get('main_skill')}".replace("  ", " "))
    a("")
    a(f"- Objective metric: `{metric}` (PoB output, one config profile `{m.get('config_profile')}` for every variant). {m.get('metric_note', '')}".rstrip())
    a(f"- Engine: PoB-PoE2 pin `{m.get('pob_sha')}`. Tiers: {', '.join(m.get('tiers', []))}.")
    a("- Source of numbers: PoB calculations unless marked: `~` = price model estimate, `proxy` = benchmark density proxy, "
      "`ASSUMPTION` = owner-tunable constant, not game data. Variants and items are tool output, not advice.")
    a(f"- Preflight estimate: {_est(d['estimate'])}")
    a("")
    rk = ranked(d)
    for tier in m.get("tiers") or list(rk):
        rows = rk.get(tier, [])
        a(f"## Tier `{tier}`")
        a("")
        if not rows:
            a("No variant completed at this tier.")
            a("")
            continue
        best = rows[0][1]["value"]
        bids = list(m.get("benchmarks", {}))
        has_actor = any((tr.get("actor") or {}) for _, tr in rows)
        head = ["#", "variant", metric, "vs best", "EHP", "Life / ES", "min res", "price", "floors"] + bids
        if has_actor:
            head += [f"{metric} with effects", "companion", "combined", "without companion"]
        a("| " + " | ".join(head) + " |")
        a("|---|---|---:|---:|---:|---:|---|---|---|" + "---|" * len(bids) + ("---:|---:|---:|---:|" if has_actor else ""))
        for n, (s, tr) in enumerate(rows, 1):
            st = tr.get("stats") or {}
            delta = "best" if n == 1 else f"{(tr['value'] / best - 1):+.1%}" if best else "n/a"
            price = "n/a" if not tr.get("price") else tr["price"] if tr["price"].startswith("no price") else f"~{tr['price']}"
            cells = [str(n), _axes(s["variant"]), _num(tr["value"], 1), delta, _num(st.get("TotalEHP")),
                     f"{_num(st.get('Life'))} / {_num(st.get('EnergyShield'))}", _res(st), price,
                     {True: "met", False: "NOT met", None: "n/a"}[tr.get("floors_met")]]
            cells += [_bench_cell((tr.get("bench") or {}).get(b)) for b in bids]
            if has_actor:
                cells += _actor_cells(tr.get("actor") or {})
            a("| " + " | ".join(cells) + " |")
        a("")
        for n, (s, tr) in enumerate(rows, 1):
            a(f"**{n}. {_axes(s['variant'])}**: supports {', '.join(s['supports']) or 'none'}; tree +{_pct(s.get('tree_gain'))} "
              f"({s.get('tree_points')} points); gear {_num(tr['baseline'], 1)} -> {_num(tr['value'], 1)} {metric}, {tr['evals']} engine evals.")
            for slot, desc in tr["items"].items():
                a(f"  - {slot}: {desc}")
            if (tr.get("actor") or {}).get("effects"):
                a("  - companion effects: " + _effects(tr["actor"]))
            if (tr.get("actor") or {}).get("error"):
                a(f"  - companion FAILED: {tr['actor']['error']}")
            if tr.get("unparsed"):
                a(f"  - candidate mods rejected, PoB cannot parse: {', '.join(tr['unparsed'])}")
            for note in tr.get("notes", []):
                a(f"  - note: {note}")
            a("")
        flags = dict.fromkeys(f"{bid}: {f}" for _, tr in rows for bid, b in (tr.get("bench") or {}).items() for f in (b or {}).get("flags", []))
        if flags:
            a("Benchmark flags:")
            a("")
            for f in flags:
                a(f"- {f}")
            a("")
        a("")
    a(_across(d, rk))
    a("## Benchmarks")
    a("")
    if not m.get("benchmarks"):
        a("None requested (`benchmarks:` in the spec).")
    for bid, b in m.get("benchmarks", {}).items():
        a(f"- `{bid}` ({b['kind']}, patch {b['patch']}): {b['description']}")
        if b["unsourced"]:
            a(f"  - incomplete, unsourced inputs: {', '.join(b['unsourced'])} (metrics depending on them are n/a, never guessed)")
        if b["assumptions"]:
            a(f"  - ASSUMPTION constants (owner-tunable, not game data): {', '.join(b['assumptions'])}")
    a("")
    a("## Limitations and flags")
    a("")
    lim = m.get("limitations") or []
    for x in lim:
        a(f"- {x}")
    for n in d.get("notes", []):
        a(f"- {n}")
    a("- Outside the search: jewels, runes/soul cores and weapon-set passive points stay as in the seed (docs/pipeline.md section 4).")
    a("- Prices are a model estimate (`~`), not a market quote; see docs/price-tiers.md for the sample label.")
    fails = [(s, t, tr) for s in d["seeds"] for t, tr in s["tiers"].items() if not tr["ok"]]
    for s in d["seeds"]:
        if s.get("error"):
            a(f"- FAILED seed {_axes(s['variant'])}: {s['error']}")
    for s, t, tr in fails:
        a(f"- FAILED {_axes(s['variant'])} at tier {t}: {tr['error']}")
    for s in d["seeds"]:
        for n in s.get("notes", []):
            a(f"- seed {_axes(s['variant'])}: {n}")
    a("")
    return "\n".join(L)


def _pct(x) -> str:
    return "n/a" if x is None else f"{x:.1%}"


def _est(e: dict) -> str:
    return (f"{e['seeds']} seed(s) x {e['tiers']} tier(s) x {e['slots']} slot(s), ~{e['engine_evals']:,} engine evals, "
            f"~{e['wall_seconds'] / 60:.1f} min wall (rates: data/rates.yaml)")


def _across(d: dict, rk: dict) -> str:
    out = ["## Across tiers", ""]
    if not rk:
        return "\n".join(out + ["No results.", ""])
    axes = sorted({k for s in d["seeds"] for k in s["variant"]})
    if not axes:
        out.append("No axes: a single variant per tier, nothing to compare.")
        return "\n".join(out + [""])
    tiers = [t for t in d["meta"].get("tiers", []) if t in rk]
    for ax in axes:
        out.append(f"Axis `{ax}`: best {d['metric']} per value, by tier (winner in bold).")
        out.append("")
        vals = sorted({s["variant"][ax] for s in d["seeds"] if ax in s["variant"]})
        out.append("| tier | " + " | ".join(vals) + " |")
        out.append("|---|" + "---:|" * len(vals))
        for t in tiers:
            best: dict[str, float] = {}
            for s, tr in rk[t]:
                v = s["variant"].get(ax)
                if v is not None:
                    best[v] = max(best.get(v, float("-inf")), tr["value"])
            top = max(best.values()) if best else None
            out.append(f"| {t} | " + " | ".join(("**" + _num(best[v], 1) + "**") if best.get(v) == top else _num(best.get(v), 1)
                                                 for v in vals) + " |")
        out.append("")
    return "\n".join(out)


# ---- sqlite ------------------------------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE seeds(seed INTEGER PRIMARY KEY, axes TEXT, ok INTEGER, supports TEXT, supports_gain REAL, tree_gain REAL,
                   tree_points INTEGER, error TEXT);
CREATE TABLE tier_runs(seed INTEGER, tier TEXT, rank INTEGER, ok INTEGER, value REAL, baseline REAL, price TEXT,
                       floors_met INTEGER, evals INTEGER, seconds REAL, items TEXT, stats TEXT, unparsed TEXT, notes TEXT, error TEXT,
                       PRIMARY KEY(seed, tier));
CREATE TABLE bench(seed INTEGER, tier TEXT, benchmark TEXT, result TEXT, PRIMARY KEY(seed, tier, benchmark));
"""


def write_sqlite(d: dict, path: Path) -> None:
    path = Path(path)
    path.unlink(missing_ok=True)
    rk = ranked(d)
    rank = {(id(s), t): n for t, rows in rk.items() for n, (s, _) in enumerate(rows, 1)}
    j = lambda x: json.dumps(x, sort_keys=True)  # noqa: E731
    with sqlite3.connect(path) as c:
        c.executescript(SCHEMA)
        c.executemany("INSERT INTO meta VALUES(?,?)", [("metric", d["metric"]), ("meta", j(d.get("meta", {}))), ("estimate", j(d["estimate"]))])
        for i, s in enumerate(d["seeds"]):
            c.execute("INSERT INTO seeds VALUES(?,?,?,?,?,?,?,?)", (i, j(s["variant"]), int(s["ok"]), j(s["supports"]), s["supports_gain"],
                                                                      s["tree_gain"], s["tree_points"], s["error"]))
            for t, tr in s["tiers"].items():
                c.execute("INSERT INTO tier_runs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (i, t, rank.get((id(s), t)), int(tr["ok"]), tr["value"], tr["baseline"], tr["price"],
                           None if tr["floors_met"] is None else int(tr["floors_met"]), tr["evals"], tr["seconds"], j(tr["items"]),
                           j(tr.get("stats", {})), j(tr.get("unparsed", [])), j(tr["notes"]), tr["error"]))
                for bid, b in (tr.get("bench") or {}).items():
                    c.execute("INSERT INTO bench VALUES(?,?,?,?)", (i, t, bid, j(b)))


def write_report(d: dict, out_dir: Path | str) -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    md, db = out / "report.md", out / "results.sqlite"
    md.write_text(render_markdown(d), encoding="utf-8")
    write_sqlite(d, db)
    return md, db


def load_run(path: Path | str) -> dict:
    p = Path(path)
    return json.loads((p / "run.json" if p.is_dir() else p).read_text(encoding="utf-8"))
