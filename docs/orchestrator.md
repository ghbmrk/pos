# Orchestrator (G8a)

`pos_pipeline/orchestrate.py`; pipeline stage 3 glue (docs/pipeline.md). Turns a validated spec into seeds x tiers and runs the merged stages.

## Flow
1. **Preflight**: `estimate(seeds, tiers, slots, workers, realloc_rounds)` from `data/rates.yaml` (measured core-seconds per stage, each with its source). Tree seeds run one per core, so tree wall time is `ceil(seeds/workers) x per-seed`; other stages divide core-seconds by workers. Above the cap (default 45 min) `run` raises `RunRefused` unless `force`.
2. **Per seed** (axis combination, `variants(spec)`): assemble (G3b) -> supports (G5) -> tree (G6, all seeds in one parallel batch, caps 100/200/400).
3. **Per seed x tier**: gear (G7/G7b) on the tree result, with `STANDARD_FLOORS` when the spec has `resist_capped`. A failed seed or tier is recorded (`SeedRun.error`, `TierRun.error`) and the run continues.
4. Output: `RunResult` (`to_dict()`, `best_per_tier()`); with `out_dir`, `run.json` (no XML) and `cache.sqlite` (pool cache, so reruns and shared candidates are free).

Stages are injected (`Stages`), so unit tests use fakes. Benchmark metrics (B2) plug in by supplying stages that score with a derived metric; the loop only passes `metric` through and does not interpret it.

## CLI
`python -m pos_pipeline run spec.yaml slot=Base ... [--preflight] [--workers N] [--max-minutes M] [--force] [--realloc-rounds N] [--out DIR]`. `--preflight` prints the estimate and the rates used, runs nothing, exits 1 if over the cap. Exit 3 = refused by the cap. `--realloc-rounds 0` is the cheap gear mode (about 2.3x less gear time than 4 rounds, final DPS lower: 865 vs 1,045 in G7b).

## Decisions made here
- Bases are an input (`slot=Base`), as in the `gear` command. A `weapon_base` axis value overrides the weapon base only when it names a catalogue base; type tokens such as `wand+focus` are not applied (noted in the seed).
- Supports are searched on the ungeared seed. Picks made before gear exists may differ from picks on a geared build; the per-tier support re-check in docs/pipeline.md is not built.
- Off-hand, jewels, runes, weapon-set points: outside search, as before.
- Known limit (G7b finding, not solved): a pure-DPS metric leaves boots/belt and other stat-only slots without damage affixes; only floors shape them.

## Preflight accuracy
Rates come from Spark Stormweaver L90 on 4 vCPU (not an endgame build); larger builds may cost more. See the validation run below, and re-measure by comparing `SeedRun.seconds` / `TierRun.seconds` in `run.json` with `data/rates.yaml`.

Validation run (4 vCPU, Spark Stormweaver L90, 1 seed x mid, weapon + amulet, `--realloc-rounds 0`, 143 s wall): supports 28.9 s (estimated 29), tree 75.0 s (estimated 75, three caps), gear 35.4 s for 658 evals (first estimate 16 s from the 9-slot rate: few-slot searches cost about 2x more per slot, so `gear_per_slot_few` was added; its `realloc_4` entry is assumed, not measured). FullDPS 9,649 -> 30,726 over the geared seed.
