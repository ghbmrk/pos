"""I7 ideation evaluation harness (docs/ideation-eval.md).

Input: one directory per prompt under evals/ideation/<pid>/ holding the slates a client model submitted to the gate
(round1.yaml, round2.yaml, ...; final.yaml = what it ended with), optionally notes.md (the client's own log) and run/
(a `slate run --out` directory with slate_run.json). Everything here is deterministic: the gate is re-run on each
saved round, so numbers do not depend on what the client says it saw.

Scores per prompt:
- gate: submitted / kept per round, issue codes per round, rounds used;
- contamination caught: `unresolved` names and `quote_mismatch` cites the gate rejected (round 1 = before any fix);
- diversity of the kept set: distinct values per archetype field, mean pairwise differing fields (of 6);
- generator mix: `source` llm vs sweep among kept;
- engine (if run/): ablation verdict counts, share `confirmed`, top-ranked candidate and its source.

Usage: python tools/eval_ideation.py [evals/ideation] [--out evals/ideation/results.md] [--json]
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pos_catalogue import Catalogue  # noqa: E402
from pos_pipeline import slate as sl  # noqa: E402
from pos_pipeline.spec import SpecError  # noqa: E402

CONTAM_CODES = ("unresolved", "quote_mismatch", "quote_short", "ambiguous")


def _rounds(d: Path) -> list[Path]:
    rs = sorted(d.glob("round*.yaml"), key=lambda p: int(re.sub(r"\D", "", p.stem) or 0))
    if not rs and (d / "final.yaml").exists():
        rs = [d / "final.yaml"]
    return rs


def gate_round(path: Path, cat_cache: dict) -> dict:
    try:
        s = sl.load_slate(path)
    except (SpecError, ValueError, OSError, yaml.YAMLError) as e:   # a slate that does not parse counts as a failed round
        return {"file": path.name, "parse_error": str(e)[:300], "submitted": 0, "kept": 0, "codes": {}, "ok": False}
    cat = cat_cache.setdefault(s.pob_sha, Catalogue.load(pob_sha=s.pob_sha))
    rep = sl.validate_slate(s, cat)
    codes = Counter(i.code for c in rep.candidates for i in c.errors)
    codes.update(i.code for i in rep.issues if i.severity == "error")
    unresolved = sorted({i.message.split("'")[1] if "'" in i.message else i.message
                         for c in rep.candidates for i in c.errors if i.code == "unresolved"})
    kept = rep.kept
    by_name = {c.name: c for c in s.candidates}
    return {
        "file": path.name, "submitted": len(rep.candidates), "kept": len(kept), "ok": rep.ok,
        "codes": dict(sorted(codes.items())),
        "unresolved_names": unresolved,
        "vectors": [k.vector for k in kept],
        "kept_names": [k.name for k in kept],
        "sources": [by_name[k.name].source if k.name in by_name else "?" for k in kept],
    }


def diversity(vectors: list[dict]) -> dict:
    if not vectors:
        return {"n": 0}
    fields = list(vectors[0])
    distinct = {f: len({v[f] for v in vectors}) for f in fields}
    pairs = list(combinations(vectors, 2))
    mean = sum(sum(a[f] != b[f] for f in fields) for a, b in pairs) / len(pairs) if pairs else 0.0
    return {"n": len(vectors), "distinct": distinct, "mean_pairwise_diff": round(mean, 2), "of": len(fields)}


def engine(run_dir: Path) -> dict | None:
    j = run_dir / "slate_run.json"
    if not j.exists():
        return None
    d = json.loads(j.read_text(encoding="utf-8"))
    verdicts = Counter(a.get("verdict", "?") for c in d["candidates"] for a in c.get("ablations", []))
    tested = sum(v for k, v in verdicts.items() if k != "not_testable")
    ranked = sorted((c for c in d["candidates"] if c.get("screen_rank")), key=lambda c: c["screen_rank"])
    return {
        "screened": sum(c.get("status") == "screened" for c in d["candidates"]),
        "failed": [(c["name"], (c.get("error") or "")[:120]) for c in d["candidates"] if c.get("status") == "failed"],
        "verdicts": dict(sorted(verdicts.items())),
        "confirmed_share": round(verdicts.get("confirmed", 0) / tested, 2) if tested else None,
        "top": [(c["name"], c.get("source"), c.get("rank_note", "")) for c in ranked[:3]],
        "wall_s": d.get("meta", {}).get("wall_s"),
    }


def evaluate(root: Path) -> list[dict]:
    out, cache = [], {}
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        rounds = [gate_round(p, cache) for p in _rounds(d)]
        if not rounds:
            continue
        first, last = rounds[0], rounds[-1]
        contam_r1 = {c: first["codes"].get(c, 0) for c in CONTAM_CODES if first["codes"].get(c)}
        out.append({
            "prompt_id": d.name,
            "prompt": _prompt(d),
            "rounds": rounds,
            "rounds_used": len(rounds),
            "first_pass_rate": round(first["kept"] / first["submitted"], 2) if first["submitted"] else 0.0,
            "final_kept": last["kept"], "final_submitted": last["submitted"], "final_ok": last["ok"],
            "contamination_caught_r1": contam_r1,
            "unresolved_names_all": sorted({n for r in rounds for n in r.get("unresolved_names", [])}),
            "diversity": diversity(last.get("vectors", [])),
            "sources": dict(Counter(s.split(":")[0] for s in last.get("sources", []))),
            "engine": engine(d / "run"),
        })
    return out


def _prompt(d: Path) -> str:
    for p in [d / "final.yaml", *_rounds(d)]:
        if p.exists():
            m = re.search(r'^prompt:\s*"?(.*?)"?\s*$', p.read_text(encoding="utf-8"), re.M)
            if m:
                return m.group(1)
    return ""


def render(rows: list[dict]) -> str:
    L = ["| id | prompt | rounds | r1 kept/sub | final kept/sub | gate rejections r1 (codes) | PoE1/ungrounded caught r1 | "
         "distinct class/deliv/dmg/def/skill | mean diff /6 | sources | ablation confirmed | top (source) |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        f, dv, e = r["rounds"][0], r["diversity"], r["engine"]
        ds = dv.get("distinct", {})
        dist = "/".join(str(ds.get(k, "-")) for k in ("class_asc", "delivery", "damage", "defence", "main_skill"))
        codes = ", ".join(f"{k} {v}" for k, v in f["codes"].items()) or "none"
        contam = ", ".join(f"{k} {v}" for k, v in r["contamination_caught_r1"].items()) or "none"
        conf = "-" if not e else f"{e['confirmed_share']} ({', '.join(f'{k} {v}' for k, v in e['verdicts'].items())})"
        top = "-" if not e or not e["top"] else f"{e['top'][0][0]} ({e['top'][0][1]})"
        L.append(f"| {r['prompt_id']} | {r['prompt']} | {r['rounds_used']} | {f['kept']}/{f['submitted']} | "
                 f"{r['final_kept']}/{r['final_submitted']}{'' if r['final_ok'] else ' NOT ok'} | {codes} | {contam} | "
                 f"{dist} | {dv.get('mean_pairwise_diff', '-')} | "
                 f"{', '.join(f'{k} {v}' for k, v in r['sources'].items()) or '-'} | {conf} | {top} |")
    tot_sub = sum(r["rounds"][0]["submitted"] for r in rows)
    tot_keep = sum(r["rounds"][0]["kept"] for r in rows)
    names = sorted({n for r in rows for n in r["unresolved_names_all"]})
    L += ["", f"First-round gate pass: {tot_keep}/{tot_sub}. Unresolved names caught (all rounds): "
          + (", ".join(names) if names else "none") + "."]
    return "\n".join(L) + "\n"


def main(argv: list[str]) -> int:
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--out")]
    root = Path(args[0]) if args else ROOT / "evals" / "ideation"
    rows = evaluate(root)
    if "--json" in argv:
        print(json.dumps(rows, indent=1, default=str))
        return 0
    md = render(rows)
    if "--out" in argv:
        Path(argv[argv.index("--out") + 1]).write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
