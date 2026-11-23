# Prompt-to-report loop (L6)

Owner spec (cmsg_01RxGYnd78N9kMbbAJ5pWDhU1dnxqDdRaEYAuumsEdPHoc): player prompt -> several likely-competitive ideas -> sim validates each ->
several rounds of creative improvement verified by the sim -> results for the player. Code: `pos_pipeline/play.py`; CLI `python -m pos_pipeline play`;
MCP tool `play` and prompt `play`.

## Shape

The server has no embedded LLM (decided, docs/pipeline.md), so the ideas step is the client's: it writes a slate from the prompt (`ideation_guide`,
`validate_slate`) and calls `play`. Everything after that is one background job:

1. **Screen** every kept idea at one tier (`run_slate` with deepen off: spec -> supports -> tree -> gear -> benchmarks, plus key-piece ablation). Rank on benchmarks only.
2. **Creative rounds** (`--outer-rounds`, default 2). For each of the top `--k` ideas the engine sweeps keystones and ascendancy notables on that
   idea's own screened build (`sweep`, flags and `over_budget` picks dropped, predicted gain >= 3%). The best `--children` picks join the spec as a child
   idea, which is re-simulated through the whole screen (supports and tree are re-searched around the change). A child **replaces its parent only if the
   mean benchmark value improves >= 2% and no survival check is lost** (`bench_gain`); otherwise it is recorded as rejected. Stops when a round keeps nothing,
   at the round limit or at `--max-minutes`.
3. **Finalists** (top k) get the full pipeline with the L3 inner loop (`--inner-rounds`, default 3; dead-move skipping on, L4 `--direct` stays off, PR #58).
4. **Report** (`report.md`, `play.json`): ranking per tier on the benchmarks, how every idea fared, every creative step with sweep-predicted vs sim-measured
   change, a **compounding check**, the calibrated-probe diagnosis of the winner, and an ASSUMED banner for stand-ins (`--assume`).

The creative step is deliberately numeric: the sweep proposes and the sim disposes, so a kept change always carries its own evidence. Creative moves beyond
single keystone/notable additions (a different ascendancy, a swapped skill, a new engine) are the client's job: it reads the report and calls `play` again with a revised slate.

## Compounding check (owner principle cmsg_01RxGYnd78N9kMbbAJ5pWDhUMPY2hjQhYp2yGeFZAi2wG1)

On the winner's final build: each key piece is ablated alone (as in the slate runner), then **all tree key pieces are removed together**. Independent
multiplicative pieces predict a joint loss of `1 - prod(1 - d_i)`; a larger measured loss means the pieces feed each other (`compounds`), a smaller one
means they overlap. The report also states how many times weaker the build is without its core (`core_ratio`). Limits: only keystone/notable pieces enter the
joint test (uniques and supports have no joint removal), it needs at least two of them, and a core made of gear or supports reads as `n/a`.

## Assumed what-ifs

`brief.assumed_ok: true` lets a slate contain assumed-Squire specs (`companion.assumed`) **only if every kept candidate is assumed**, so assumptions are
ranked against assumptions and never against real builds; `--assumed` (MCP `allow_assumed`) is still required. Two-actor specs with companion gear refuse the
inner loop (kept as a note, single pass result); specs without companion gear keep it.

## Not done

- No LLM-driven creative move inside the job (by design); no meta-build comparison unless `--meta BUILD.xml` is given.
- Single run per cell, no variance estimate. Sweep picks are single additions; a swap (drop one keystone to add another) is not proposed.
- Estimate (`play_estimate`) is an upper bound built from the slate estimate and the L3 bound.

## Acceptance run (2026-11-23): "Knight Squire + Cyclone", real engine

Slate `examples/play/squire_cyclone_slate.yaml` (3 ideas: Squire as ground painter / debuff bot / own-damage; all assumed, Whirling Slash stands in for Cyclone,
Huntress for the Knight), `--k 3 --outer-rounds 2 --inner-rounds 3 --workers 3`, 4 vCPU, one run, 28.2 min unattended. Report: `examples/play/squire_cyclone_report.md`.
- The loop ran as specified: screen -> 2 creative rounds (5 kept, 0 rejected, 1 "no pick") -> finalists -> report. Best build 6,943 s -> 1,526 s time-to-kill (4.5x) from
  Dance with Death (+25% predicted, +20% measured benchmark time, identical on all three ideas) then an ascendancy notable (+17-19%).
- **Verdict on the builds: weak.** Every build still dies to the named Arbiter hit and TTK is 1,500-4,500 s against a 60 s gate. One weapon slot is searched (Squire stand-in
  data), so this is a pipeline demonstration, not a build recommendation.
- **Compounding check: no.** The winner's tree pieces `overlap` (joint loss 17% vs 20% independent; core worth 1.2x). Dance with Death carries almost all of it (19.9% alone);
  Resolute Technique is negative (removing it raises the metric), Surging Avatar reads zero (`possibly_unmodelled`). The loop's own principle check says: marginal gains, not a core that compounds.
- Weaknesses found: the sweep proposes the same pick for every idea (ideas converge: low diversity after round 1, which is the client's job to counter with a revised slate);
  the first run lost proposals to the memory watchdog (engine code -9) so proposals now run on half the pool with one retry (two retries still logged in the second run, both recovered).
  The inner loop's effect on these builds is not isolated (single run, no ablation of `--inner-rounds`).
