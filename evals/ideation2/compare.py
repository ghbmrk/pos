"""I13 before/after table over the slate_run.json files of each arm (docs/ideation-eval.md, section I13).
Usage: python evals/ideation2/compare.py   (prints Markdown)"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARMS = {
    "I7 (baseline)": "evals/ideation/{p}/run/slate_run.json",
    "A: I7 slates, I8-I12 engine": "evals/ideation2/{p}/frozen/run/slate_run.json",
    "A2: I7 slates, I8-I13 engine": "evals/ideation2/{p}/frozen/run_i13/slate_run.json",
    "B: fresh slates, I8-I13 engine": "evals/ideation2/{p}/run/slate_run.json",
}
PROMPTS = ["p1", "p2", "p3", "p4", "p5"]


def arm_stats(pattern: str, prompts=PROMPTS) -> dict | None:
    v, n_cand, pack_ok, boss_ok, art, art_top, top_conf, sweep_c, conds = Counter(), 0, 0, 0, 0, 0, 0, 0, 0
    for p in prompts:
        f = ROOT / pattern.format(p=p)
        if not f.exists():
            return None
        for c in json.loads(f.read_text())["candidates"]:
            n_cand += 1
            ab = c.get("ablations") or []
            v.update(a["verdict"] for a in ab)
            bench = ((c.get("screen") or {}).get("tier_run") or {}).get("bench") or {}
            pack_ok += any(k.startswith("breach") and b.get("clear_s") is not None for k, b in bench.items())
            boss_ok += any(k.startswith("arbiter") and b.get("ttk_s") is not None for k, b in bench.items())
            rn = c.get("rank_note") or ""
            dps = ((c.get("screen") or {}).get("tier_run") or {}).get("stats") or {}
            flagged = (dps.get("FullDPS") or 0) > 3 * (dps.get("TotalDPS") or 0) > 0
            art += flagged
            if c.get("screen_rank") == 1:
                art_top += flagged and "ARTEFACT" not in rn
                top_conf += any(a["verdict"] == "confirmed" for a in ab)
            sweep_c += c.get("source", "llm") != "llm"
            conds += bool(c.get("conditions"))
    t = sum(v.values())
    return {"cand": n_cand, "pieces": t, "confirmed": v["confirmed"], "share": v["confirmed"] / t if t else 0.0,
            "verdicts": dict(v), "pack_value": pack_ok, "boss_value": boss_ok, "flagged": art,
            "rank1_unlabelled_artefact": art_top, "rank1_with_confirmed_piece": top_conf, "sweep_cands": sweep_c,
            "cands_with_conditions": conds}


def main() -> None:
    print("| arm | candidates | key pieces confirmed (p1-p4) | confirmed (p5) | possibly_unmodelled / not_load_bearing / not_testable (all) "
          "| pack value present | rank 1 rests on a confirmed piece | rank 1 on an unlabelled >3x artefact | sweep-sourced | with declared conditions |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for name, pat in ARMS.items():
        a, a14, a5 = arm_stats(pat), arm_stats(pat, PROMPTS[:4]), arm_stats(pat, PROMPTS[4:])
        if a is None:
            print(f"| {name} | not run |" + " |" * 8)
            continue
        v = a["verdicts"]
        print(f"| {name} | {a['cand']} | {a14['confirmed']}/{a14['pieces']} ({a14['share']:.0%}) | {a5['confirmed']}/{a5['pieces']} "
              f"| {v.get('possibly_unmodelled', 0)} / {v.get('not_load_bearing', 0)} / {v.get('not_testable', 0)} "
              f"| {a['pack_value']}/{a['cand']} | {a['rank1_with_confirmed_piece']}/5 | {a['rank1_unlabelled_artefact']}/5 "
              f"| {a['sweep_cands']} | {a['cands_with_conditions']} |")


if __name__ == "__main__":
    main()
