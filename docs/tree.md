# Tree stage (G6)

`pos_pipeline/tree.py`: `search_tree(engine, xml, metric, ...)` wraps the engine's `optimize_passives` (greedy: per pick, a what-if calc for up to `candidates` nearest unallocated notables, take the best positive gain, then Normal nodes with leftover points) and returns the new XML, stats, picks and timing. `search_trees(xmls, workers=N)` runs seeds in parallel, one dedicated engine each (not `EnginePool`: a call takes 10-50 s, past its 60 s watchdog, and mutates the build). A seed that errors is retried once on a fresh engine. CLI: `python -m pos_pipeline tree spec.yaml [workers] [candidates]`.

Defaults: `reset=True` (re-plan regular nodes from scratch so `require`d nodes fit and the tree cannot go over budget; ascendancy and class start kept), `points=0` (fill the whole budget), `candidates=200`.

## Timing (4 vCPU, Spark Sorceress, no gear, PoB-PoE2 601768b; `python tools/bench_tree.py`)
| level | candidates | seconds | picks | points used / left | TotalDPS |
|---|---|---|---|---|---|
| 90 | 50 | 11.5 | 42 | 102 / 11 | 88 -> 2004 |
| 100 | 25 | 3.2 | 16 | 44 / 79 | 88 -> 630 |
| 100 | 50 | 12.0 | 42 | 102 / 21 | 88 -> 2004 |
| 100 | 100 | 16.0 | 33 | 123 / 0 | 88 -> 3129 |
| 100 | 200 | 23.1 | 25 | 123 / 0 | 88 -> 3389 |
| 100 | 400 | 35.6 | 21 | 123 / 0 | 88 -> 3468 |
| 100 | 1000 | 46.6 | 12 | 123 / 0 | 88 -> 2048 |

4 seeds on 4 engines in parallel: 15.5 s wall (per call 11.5-12.5 s), so seeds scale near-linearly. A per-seed cost of 10-50 s replaces the "~5,000 calcs, dominant cost" worry in `docs/pipeline.md`: it is minutes per whole run, not hours. An endgame build with gear is unmeasured (none available offline); calc cost per what-if grows with build complexity, so treat these as a floor.

## Findings (judgement from the table)
- The `candidates` cap picks the nearest nodes by path distance, so a small cap strands points (25: 79 unspent, 630 DPS) and a huge cap lets the greedy buy expensive nodes early and finish worse (1000: 2048 DPS). Quality is non-monotonic; 200 is the default (best DPS-per-second knee here), 400 for a final pass.
- The greedy is order-dependent and a local optimum. Mitigation if reports show it matters: run 2-3 candidate caps per seed and keep the best (they are cheap in parallel).
- Metric must be a `mainOutput` key; for triggered/granted-skill supports `FullDPS` is inflated (see `docs/supports.md`, Fiery Death audit).
- Jewels, weapon-set points and ascendancy ordering are as in the engine; not modelled here.
