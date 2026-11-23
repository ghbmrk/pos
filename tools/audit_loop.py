"""L0 audit (docs/loop.md 1.1): golden Spark, pass 1 = today's pipeline, then a second supports/tree/gear pass on the
geared build; Arbiter result; probe deltas (PoB custom modifiers) on the final build. Gear in pass 2 runs on a fresh
engine (the long-lived one was OOM-killed once in this sequence). ~6 min on 4 vCPU.
Usage: python tools/audit_loop.py [BodyBase]   (default Vile Robe)"""
import json, sys, time
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pos_catalogue.catalogue import Catalogue
from pos_pipeline.spec import load_spec
from pos_pipeline.validate import validate
from pos_pipeline.orchestrate import engine_stages, run
from pos_pipeline.benchmarks import evaluate
from pos_pipeline import supports as S
from pos_engine.engine import PobEngine
from dataclasses import asdict
T = {}
def tick(k, t0): T[k] = round(time.perf_counter() - t0, 1)
cat = Catalogue.load()
spec = load_spec(str(__import__("pathlib").Path(__file__).resolve().parents[1] / "examples/spark_golden.yaml"))
rep = validate(spec, cat)
bases = {"weapon": "Acrid Wand", "amulet": "Lapis Amulet", "body_armour": sys.argv[1] if len(sys.argv) > 1 else "Vile Robe"}
out = {"metric": rep.metric}
t0 = time.perf_counter()
with engine_stages(spec, cat, rep, bases, workers=4, realloc_rounds=0) as (st, skill_of):
    tick("boot", t0); t0 = time.perf_counter()
    res = run(spec, st, metric=rep.metric, slots=len(bases), workers=4, skill_id=skill_of, realloc_rounds=0, force=True,
              benchmarks=["arbiter_ash", "breach_t15"], log=print)
    tick("pass1_total", t0)
    s = res.seeds[0]; tr = s.tiers["mid"]
    out["pass1"] = {"seconds": s.seconds, "gear_s": tr.seconds, "value": tr.value, "supports": s.supports,
                    "bench": tr.bench, "floors_met": tr.floors_met, "items": tr.items, "evals": tr.evals}
    sk = skill_of({})
    # pass 2: supports on the geared build, tree on that, gear again
    xml = tr.xml
    t0 = time.perf_counter(); sup = st.supports(xml, sk); tick("p2_supports", t0)
    x2 = st.apply_supports(xml, sk, list(sup.best.supports))
    t0 = time.perf_counter(); tt = st.trees([x2])[0]; tick("p2_tree", t0)
    x3 = tt.xml if tt.ok else x2
with engine_stages(spec, cat, rep, bases, workers=4, realloc_rounds=0) as (st, skill_of):
    t0 = time.perf_counter(); g = st.gear(x3, "mid", {}); tick("p2_gear", t0)
    out["pass2"] = {"supports": list(sup.best.supports), "sup_gain": sup.gain, "tree_ok": tt.ok, "tree_gain": tt.gain,
                    "value": g.value, "bench": {b: (lambda r: asdict(r))(st.bench(g.xml, b, {})) for b in ("arbiter_ash",)}}
    # probes on the pass-1 and the pass-2 build
    probes = ["10% more Damage", "+10% to Critical Hit Chance", "+50% to Critical Damage Bonus", "10% increased Cast Speed",
              "+1 to Level of all Spell Skills", "Enemies have -10% to Lightning Resistance",
              "Nearby Enemies have -10% to Lightning Resistance", "Damage Penetrates 10% Lightning Resistance",
              "+500 to maximum Energy Shield", "+500 to maximum Life", "+1000 to Armour", "+1000 to Evasion Rating",
              "+10% to all Elemental Resistances", "Adds 10 to 100 Lightning Damage to Spells", "+10 to Intelligence"]
    eng = PobEngine()
    for label, bx in (("pass1", xml), ("pass2", g.xml)):
        eng.load_build_xml(bx)
        base = eng.get_stats([rep.metric, "TotalEHP"])["stats"]
        pv = {}
        t0 = time.perf_counter()
        for p in probes:
            eng.load_build_xml(bx)
            try:
                eng.set_config(custom_mods=p)
                s2 = eng.get_stats([rep.metric, "TotalEHP"])["stats"]
                pv[p] = {k: round((s2.get(k) or 0) / (base.get(k) or 1) - 1, 4) for k in (rep.metric, "TotalEHP")}
            except Exception as ex:
                pv[p] = str(ex)
        tick(f"probes_{label}", t0)
        out[f"probes_{label}"] = pv
    eng.close()
out["timings"] = T
print(json.dumps(out, indent=1, default=str))
