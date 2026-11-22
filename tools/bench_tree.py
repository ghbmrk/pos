"""Time the tree stage on a Spark seed at several levels / candidate caps: `python tools/bench_tree.py`."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pos_catalogue import Catalogue  # noqa: E402
from pos_engine.engine import PobEngine  # noqa: E402
from pos_pipeline.assemble import assemble  # noqa: E402
from pos_pipeline.spec import parse_spec  # noqa: E402
from pos_pipeline.tree import search_tree, search_trees  # noqa: E402

cat = Catalogue.load()
print("level cands reset  secs  picks used remain  start -> final")
for level, cands in [(90, 50), (100, 50), (100, 25), (100, 100)]:
    spec = parse_spec({"pob_sha": cat.pob_sha[:7], "class": "Sorceress", "ascendancy": "Stormweaver", "level": level,
                       "main_skill": {"gem": "Spark"}, "tiers": ["mid"]})
    with PobEngine() as e:
        a = assemble(spec, cat, e)
        r = search_tree(e, a.xml, "TotalDPS", candidates=cands)
    print(f"{level:5} {cands:5} {r.reset!s:5} {r.seconds:5.1f} {len(r.allocated):6} {r.points_used:4} {r.points_remaining:6} "
          f"{r.start:.0f} -> {r.final:.0f}")
    if (level, cands) == (100, 50):
        xml = a.xml
t = time.perf_counter()
rs = search_trees([xml] * 4, "TotalDPS", workers=4)
print(f"4 seeds in parallel (4 engines): {time.perf_counter() - t:.1f} s wall; per-call {[round(r.seconds, 1) for r in rs]}")
