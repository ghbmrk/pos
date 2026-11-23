"""L1 measurement (docs/loop.md 2.1): bare-metric searches vs benchmark-objective searches, same inputs, same machine.
Arms per case: `metric` (objective off) and `objective` (on). Cases: golden Spark (examples/spark_golden.yaml, slots weapon
Acrid Wand + amulet Lapis Amulet + body Vile Robe, mid tier, realloc 0) and the rank-1 candidate of each I13 arm-B slate
(evals/ideation2/pN/final.yaml, screen as `slate run`). Reports Arbiter survival (named hits), TTK, floors, wall time.
Appends one JSON line per (case, arm) to OUT. Usage: python tools/measure_l1.py OUT.jsonl [case ...]   (cases: golden p1..p5, optionally case:arm)"""
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pos_catalogue.catalogue import Catalogue
from pos_pipeline import data
from pos_pipeline import slate as sl
from pos_pipeline.orchestrate import engine_stages, run
from pos_pipeline.slate_run import EngineRunner, best_run
from pos_pipeline.spec import load_spec
from pos_pipeline.validate import validate

RANK1 = {"p1": "Thunder Monk Staff", "p2": "Stacked poison archer", "p3": "Blood Mage Crit Bone Storm",
         "p4": "Infusion Orb Stormweaver", "p5": "Wildsurge Thunderstorm"}
TIER = {"p1": "budget"}


def summarise(tr: dict | None) -> dict:
    if not tr:
        return {"ok": False}
    a = (tr.get("bench") or {}).get("arbiter_ash") or {}
    b = (tr.get("bench") or {}).get("breach_t15") or {}
    return {"ok": tr.get("ok"), "error": tr.get("error"), "notes": tr.get("notes"), "value": tr.get("value"), "floors_met": tr.get("floors_met"), "evals": tr.get("evals"),
            "gear_s": round(tr.get("seconds") or 0, 1), "survive": a.get("survive"), "ttk_s": a.get("ttk_s"),
            "margins": a.get("hit_margins"), "clear_s": b.get("clear_s"), "dps": a.get("dps"),
            "life": (tr.get("stats") or {}).get("Life"), "ehp": (tr.get("stats") or {}).get("TotalEHP")}


def golden(objective: bool) -> dict:
    cat = Catalogue.load()
    spec = load_spec(str(ROOT / "examples/spark_golden.yaml"))
    rep = validate(spec, cat)
    bases = {"weapon": "Acrid Wand", "amulet": "Lapis Amulet", "body_armour": "Vile Robe"}
    t0 = time.perf_counter()
    with engine_stages(spec, cat, rep, bases, workers=4, realloc_rounds=0, objective=objective) as (st, skill_of):
        res = run(spec, st, metric=rep.metric, slots=3, workers=4, skill_id=skill_of, realloc_rounds=0, force=True,
                  benchmarks=["arbiter_ash", "breach_t15"], log=lambda s: None)
    d = res.to_dict(xml=True)
    tr = d["seeds"][0]["tiers"]["mid"]
    wall = round(time.perf_counter() - t0, 1)
    from pos_engine.engine import PobEngine
    from pos_pipeline.objective import Objective
    from pos_pool.pool import EnginePool, Job
    o = Objective(rep.metric, ["arbiter_ash", "breach_t15"], floors={"FireResist": 75, "ColdResist": 75, "LightningResist": 75})
    with EnginePool(workers=2) as pool:   # common yardstick: both arms' final builds scored by the same objective
        sc = o.score([r.stats for r in pool.map([Job(tr["xml"], mutations=o.mutations(f), stat_keys=o.keys) for f in o.fights])])
    return {"wall_s": wall, "supports": d["seeds"][0]["supports"], "obj_deficit": sc.deficit, "obj_goal": sc.goal, "obj_parts": sc.parts, **summarise(tr)}


def candidate(pid: str, objective: bool) -> dict:
    s = sl.load_slate(str(ROOT / f"evals/ideation2/{pid}/final.yaml"))
    cat = Catalogue.load(pob_sha=s.pob_sha)
    rep = sl.validate_slate(s, cat)
    by = {c.name: c for c in s.candidates}
    c = by[RANK1[pid]]
    runner = EngineRunner(cat, s, {}, workers=4, objective=objective)
    t0 = time.perf_counter()
    res, _ = runner.screen(c, TIER.get(pid, "mid"))
    best = best_run(res, TIER.get(pid, "mid"))
    return {"wall_s": round(time.perf_counter() - t0, 1), "supports": (best or {}).get("supports"),
            **summarise((best or {}).get("tier_run"))}


if __name__ == "__main__":
    out = Path(sys.argv[1])
    cases = sys.argv[2:] or ["golden", "p1", "p2", "p3", "p4", "p5"]   # `p3:objective` runs one arm only
    for case in cases:
        case, _, only = case.partition(":")
        for arm in ([only] if only else ["metric", "objective"]):
            try:
                r = golden(arm == "objective") if case == "golden" else candidate(case, arm == "objective")
            except Exception as ex:
                r = {"error": f"{type(ex).__name__}: {ex}"}
            with out.open("a") as f:
                f.write(json.dumps({"case": case, "arm": arm, **r}, default=str) + "\n")
            print(case, arm, r.get("wall_s"), r.get("survive"), r.get("ttk_s"), flush=True)
