#!/usr/bin/env python3
"""Pool benchmark (G4): evals/s versus worker count on the large-tree fixture.

Each job swaps one weapon (unique mod value => cache miss) on a build with ~200 allocated nodes,
so a job is the realistic search unit: load XML, mutate, read stats.
Usage: python tools/bench_pool.py [--jobs 200] [--workers 1,2,4] [--xml PATH]
"""
import argparse, os, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pos_pool import EnginePool, Job  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--jobs", type=int, default=200)
ap.add_argument("--workers", default="1,2,4")
ap.add_argument("--xml", default=str(Path(__file__).resolve().parents[1] / "pos_pool/tests/fixtures/large_tree.xml"))
a = ap.parse_args()
xml = Path(a.xml).read_text()
print(f"cpus={os.cpu_count()} jobs={a.jobs} nodes~{xml.split('nodes=\"')[1].split('\"')[0].count(',')+1}")
def mk(i, mode):
    raw = f"Rarity: Rare\nB{mode}{i}\nDueling Wand\n{i+1}% increased Spell Damage"
    keys = ("TotalDPS", "TotalEHP")
    if mode == "swap":  # full XML reload + mutation per job
        return Job(xml, (("add_item", {"raw": raw, "slot": "Weapon 1"}),), keys)
    return Job(xml, (), keys, slot_item=("Weapon 1", raw))  # eval_items fast path

for mode in ("swap", "slot_item"):
    for n in [int(x) for x in a.workers.split(",")]:
        jobs = [mk(i, mode) for i in range(a.jobs)]
        with EnginePool(workers=n) as p:
            t0 = time.time(); p.map(jobs[:n]); warm = time.time() - t0  # includes engine boot
            t0 = time.time(); rs = p.map(jobs[n:]); dt = time.time() - t0
            assert all(r.ok for r in rs)
            print(f"{mode:9s} workers={n}: boot+first={warm:.1f}s  {len(rs)} evals in {dt:.1f}s = {len(rs)/dt:.1f} evals/s  {p.stats}")
