# Slate runner (I5)

`python -m pos_pipeline slate run slate.yaml [slot=Base ...] [--preflight] [--workers N] [--max-minutes M] [--force] [--deepen-k K] [--out DIR]`. Code: `pos_pipeline/slate_run.py`; thresholds in `data/ideation.yaml` (`run:` block); rates in `data/rates.yaml` (`tree_screen`, `ablation`). Design: `docs/ideation.md` sections 4-6. Input must pass `slate validate` (the runner refuses otherwise). Example: `examples/ideation_slate.yaml`.

## Flow

1. **Preflight**: `estimate_slate` = per kept candidate (screen at one tier, no realloc rounds, tree cap 200) + ablation + the full run for the K most expensive candidates (an upper bound: the top K are not known yet). Refuses above the cap (45 min) unless `--force`.
2. **Screen**: per candidate one `orchestrate.run` at the screen tier (`mid`, or the brief's highest tier if lower), with the brief's benchmarks and floors, then **ablation** of its key pieces on the best seed's final build.
3. **Rank** on benchmark metrics only (below).
4. **Deepen**: the top K (default 3) get the full run at every brief tier (realloc 4, default tree caps). Candidates that lose the screen stay in the report with their screen numbers.
5. **Report**: `slate_report.md`, `slate_results.sqlite` (candidates, ablations, deep_rank), `slate_run.json`; `cache.sqlite` is shared by all runs in the slate.

Bases: a candidate may give `bases: {slot: Base}` (new optional slate key, slot and base validated by the gate); `slot=Base` on the command line fills the slots a candidate does not set.

## Ranking

Per benchmark, candidates with a value are ordered by (survival-check failed last, value, name): boss = time-to-kill, pack = clear proxy. A candidate's score is (benchmarks available, mean position), so one missing a benchmark ranks after one that has it, with the gap in the report. The per-skill DPS (`TotalDPS` / `FullDPS`) is shown but never ranks across archetypes. An empty `brief.benchmarks` is refused.

## Ablation

Run on the screen's final build, metric = the spec's objective stat under the first boss benchmark's PoB options (so it is a DPS share, not time-to-kill; the two move together but are not identical).
- keystone / notable: deallocated; support: swapped for the best other eligible support (or left empty if better); verdicts from `sweep.ablate` (`confirmed` at or above `ablation_threshold`, else `not_load_bearing` / `possibly_unmodelled`).
- **unique: replaced by the best rare** for its slot at the screen tier (`GearSearcher.best_item` on the unique's own base, within the tier's slot budget, all uniques excluded). This removes the upper-bound bias of unequipping (I4 deferred it to here). If the rare search fails (base without mods, engine refusal) the slot is emptied and the label says the verdict is an upper bound. If the unique is not in the final build, because the screen's gear search overwrote its slot, the piece is `not_testable` with that reason: a unique in a searched slot is not preserved by the gear stage (G7: only priced uniques in `data/unique_prices.yaml` compete), so put fixed uniques in slots outside `slot=Base`.

## Limits (judgement)

- Screening at one tier can drop an idea that only works with a bigger budget (set the brief's tiers accordingly; `screen_tier` in `data/ideation.yaml`).
- While B3 inputs are unsourced the pack benchmark has no value, so ranking rests on the boss time-to-kill alone and survival stays `n/a`.
- Ablation of the best rare is a search result (beam, `realloc` 0 mode), not a proof of optimality; a small `worth` can mean a weak search.
- One seed per candidate is ranked: the highest objective across axis variants, not the best benchmark.
