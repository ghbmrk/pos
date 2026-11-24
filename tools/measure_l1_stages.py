"""L1 paired stage test (docs/loop.md 2.1): on the SAME input build, does a search scored by the benchmark objective end
higher on the benchmark objective than the same search scored by the bare metric? Both results are scored by one
common yardstick (the objective evaluated on the final build), so a stage that wins its own score but loses the
yardstick shows. Stages: supports (ungeared seed), gear (seed with the metric arm's supports).
Usage: python tools/measure_l1_stages.py OUT.jsonl golden|p1..p5   (cases as tools/measure_l1.py)"""
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from pos_catalogue.catalogue import Catalogue
from pos_engine.engine import PobEngine
from pos_pipeline import slate as sl
from pos_pipeline.assemble import assemble
from pos_pipeline.gear import STANDARD_FLOORS, GearSearcher
from pos_pipeline.objective import Objective
from pos_pipeline.spec import load_spec
from pos_pipeline.supports import search_supports
from pos_pipeline.validate import validate
from pos_pool.pool import EnginePool, Job
from measure_l1 import RANK1, TIER
from dataclasses import replace


def run_case(case: str) -> dict:
    if case == "golden":
        cat = Catalogue.load()
        spec = load_spec(str(ROOT / "examples/spark_golden.yaml"))
        bases, tier = {"weapon": "Acrid Wand", "amulet": "Lapis Amulet", "body_armour": "Vile Robe"}, "mid"
        bids = ["arbiter_ash", "breach_t15"]
    else:
        s = sl.load_slate(str(ROOT / f"evals/ideation2/{case}/final.yaml"))
        cat = Catalogue.load(pob_sha=s.pob_sha)
        c = {c.name: c for c in s.candidates}[RANK1[case]]
        spec, bases, tier = c.spec, dict(c.bases), TIER.get(case, "mid")
        bids = list(s.brief.get("benchmarks", []))
    spec = replace(spec, benchmarks=bids)
    rep = validate(spec, cat)
    metric = rep.metric
    floors = dict(STANDARD_FLOORS) if spec.floors.get("resist_capped") else {}
    obj = Objective(metric, bids, floors=floors, projectile=False, conditions=spec.conditions)
    sk = cat.resolve("skill", spec.main_skill).entry["id"]
    fixed = [cat.resolve("support", n).entry["id"] for n in spec.supports]
    out = {"case": case, "metric": metric, "benchmarks": bids, "floors": bool(floors)}
    with PobEngine() as eng, EnginePool(workers=4) as pool:
        a = assemble(spec, cat, eng)
        assert a.ok, a.issues
        xml0 = a.xml

        def yard(xml):
            rs = pool.map([Job(xml, mutations=obj.mutations(f), stat_keys=obj.keys) for f in obj.fights])
            sc = obj.score([r.stats for r in rs])
            b = [r.stats for r in rs]
            return {"deficit": round(sc.deficit, 4), "goal": round(sc.goal, 4), "parts": sc.parts, "dps": b[0].get(metric)}

        def apply(xml, ids):
            from pos_pipeline.assemble import _gem_line
            text = "\n".join(_gem_line(e["name"]) for e in [cat.get("skill", sk)] + [cat.get("support", i) for i in ids])
            eng.load_build_xml(xml); eng.paste_skill(text); return eng.get_xml()

        sup = {}
        for arm, o in (("metric", None), ("objective", obj)):
            t0 = time.perf_counter()
            r = search_supports(cat, pool, xml0, sk, fixed, metric, allow_triggered=[], objective=o)
            sup[arm] = (r, round(time.perf_counter() - t0, 1))
        base_xml = apply(xml0, sup["metric"][0].best.supports)
        out["supports"] = {arm: {"s": t, "set": list(r.best.supports), **yard(apply(xml0, r.best.supports))} for arm, (r, t) in sup.items()}
        out["supports"]["input"] = yard(xml0)
        if not bases:
            return out
        out["gear"] = {"input": yard(base_xml)}
        for arm, o in (("metric", None), ("objective", obj)):
            t0 = time.perf_counter()
            g = GearSearcher(cat, pool, eng, metric=metric, floors=floors, objective=o).search(base_xml, tier, bases, slots=tuple(bases), realloc_rounds=0)
            out["gear"][arm] = {"s": round(time.perf_counter() - t0, 1), "evals": g.evals, **yard(g.xml)}
    return out


if __name__ == "__main__":
    for case in sys.argv[2:]:
        try:
            r = run_case(case)
        except Exception as ex:
            import traceback; traceback.print_exc()
            r = {"case": case, "error": f"{type(ex).__name__}: {ex}"}
        with open(sys.argv[1], "a") as f:
            f.write(json.dumps(r, default=str) + "\n")
        print(json.dumps(r, default=str)[:1500], flush=True)
