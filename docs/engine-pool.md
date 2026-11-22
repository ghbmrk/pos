# Engine pool (G4)

`pos_pool`: N persistent `PobEngine` LuaJIT processes behind `EnginePool.map(jobs)`; SQLite result cache; crash/hang recovery. Spec: pipeline stage 4.

## API
- `Job(xml, mutations=(("add_item", {...}), ...), stat_keys=("TotalDPS", ...))`: load XML, apply `PobEngine` methods in order, read stats. General path.
- `Job(xml, stat_keys=..., slot_item=("Weapon 1", raw_item))`: gear-search fast path. Jobs sharing (XML, slot, keys) are batched into one engine `eval_items` call (which restores the build); a worker holding the XML skips the reload.
- `EnginePool(workers=cpu_count, cache=path|ResultCache, timeout=60, max_rss_mb=1500, max_batch=16)`; `map()` keeps input order, dedupes identical jobs, serves cache hits without touching an engine; `stats` counts hits/evals/retries/failures.
- Cache key: `sha256(pob_sha, canonical-XML hash, mutations, sorted stat keys, slot_item)`. `pob_sha` = submodule HEAD (override `POS_POB_SHA`), so a re-pin invalidates the cache.
- Failure: any engine error, crash, or `timeout` (watchdog kills the process) restarts the worker and retries once; a second failure returns `Result(ok=False, error=...)` (not cached). Engine boot is outside the watchdog window.

## Findings that shaped the design (measured, 4 vCPU, PoB `601768b`)
1. `load_build_xml` costs ~0.25 s and **leaks engine memory** (~30-50 MB per load; RSS reached 0.8-1.3 GB per worker within tens of loads, and an OOM kill happened at 4 workers). Workers are recycled above `max_rss_mb`.
2. `eval_items` has a fixed ~0.3 s cost per call but ~0.05-0.1 s per extra item, so batching matters. `add_item` + `get_stats` on a loaded build is ~0.03-0.05 s but leaves the slot dirty; not used because two-handers may touch other slots (unverified).
3. Sequential single-swap jobs through the general path are therefore reload-bound (~4 evals/s per worker).

## Benchmark (`python tools/bench_pool.py`, 200 jobs, one weapon swap each)
Build: `pos_pool/tests/fixtures/large_tree.xml`, Witchhunter L90, 202 allocated nodes, **no gear**. Larger than the S2 fixture (about 5 nodes) but not a full endgame build; a real endgame import (gear, jewels, many skills) was not available here (no corpus), so rates on one are unmeasured and likely lower.

| Path | 1 worker | 2 | 4 |
|---|---|---|---|
| general (`swap`: reload + `add_item`) | 3.7 evals/s | 5.8 | 13.5 |
| `slot_item` (batched `eval_items`) | 18.0 | 33.2 | 57.6 |

Engine boot ~2.8 s per worker (first batch). Scaling is near-linear for `slot_item` (3.2x at 4 workers); the general path is noisy (memory/GC dependent; one earlier run gave 2.5 -> 4.4 evals/s). Earlier prior-art figure (16.5 evals/s on 4 vCPU, small fixture) is consistent with the general path on a small build.

Consequence for pipeline cost estimates: search stages that vary one slot at a time (supports excepted, which change the skill group) can run at ~50+ evals/s on 4 cores; stages that must reload per candidate (tree, supports, multi-slot changes) should be budgeted at ~4-14 evals/s.
