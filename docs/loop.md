# Idea-to-sim iteration loop (L0: audit, design, ranked plan)

Status: design. Owner ask 2026-11-23 (cmsg_01RxGYnd78N9kMbbAJ5pWDhU5w5YpgaUH9T5ot7epWKk3s): first-principles idea in ->
build refined granularly -> sim and iteration loop. This doc audits the current pipeline against the shape
archetype -> skill/supports -> tree -> gear -> sim/iterate, measures where time and quality are lost, and ranks the work.

## 1. Audit

### 1.1 Measurement (real engine, pin 601768b, 4 vCPU)

Golden Spark (`examples/spark_golden.yaml`), slots weapon Acrid Wand + amulet Lapis Amulet + body Vile Robe, mid tier,
`realloc_rounds 0`, benchmarks Arbiter of Ash + Breach T15. Script: `tools/audit_loop.py` (reproduces every number here).

| step | wall | result |
|---|---|---|
| engine + pool boot | 2.0 s | |
| pass 1 = today's pipeline: supports (ungeared) / tree / gear | 27 / 64 / 62 s (154 s) | FullDPS 30,726; floors **not met**; Arbiter TTK 280 s vs gate 60 s; chasm_slam margin 1.008 |
| pass 2: supports on the geared build / tree / gear again | 32 / 65 / 52 s (148 s) | FullDPS 34,199 (**+11.3%**); support set changed (Rapid Casting -> Inevitable Criticals); TTK 250 s |
| 13 stat probes on one engine (PoB custom modifiers) | 4.5 s total (0.35 s each) | on the pass-1 build: +10% crit chance = **+43.6%** FullDPS; 10% more damage = +10.0%; +50% crit damage = +19.6%; 10% cast speed = +4.7%; +500 life = +31.5% EHP |
| probes that lied | | "Enemies have -10% to Lightning Resistance" and "Damage Penetrates 10% Lightning Resistance" = 0; "Nearby Enemies have -10% to Lightning Resistance" = **-6.5%** (wrong sign); "+10 to Intelligence" = 0 |

Eval evidence (docs/ideation-eval.md, I13 arm B, 38 candidates): Arbiter survival fails 32/38; 27 key pieces
`possibly_unmodelled` with exactly zero change; key pieces confirmed 20%; client 81-101k tokens and 2-3 min per slate;
screen 8-15 min per slate on 2 workers.

### 1.2 Findings, ranked by quality lost

1. **Every stage optimises the wrong objective.** Supports, tree and gear maximise one per-skill stat (FullDPS here);
   ranking uses benchmark TTK plus a survival gate; defence enters only as resist/attribute floors, and the golden run
   did not even meet those. Result: a build that is 4.7x over the TTK gate and one hit from death ranks on DPS, and the
   survival gate fails for 32/38 eval candidates, so it does not discriminate. This is a modelling error, not a tuning
   one: no amount of search fixes an objective that ignores the constraint that binds.
2. **The pipeline is open-loop and order-dependent.** One feed-forward pass. A second pass found +11.3% and a different
   support set, because supports were chosen before gear existed (crit gear makes Inevitable Criticals worth a slot).
   docs/pipeline.md planned a support re-check; it was never built. Nothing measures convergence.
3. **No diagnosis.** Nothing asks "what limits this build". Probes answer it in seconds: before pass 2 the probe vector
   ranked crit chance far above every other lever (+43.6% per +10%), which is what pass 2 then found in 148 s by
   blind re-search. Diagnosis costs ~3% of a pass and can direct which stage to re-run and toward what.
4. **Unmodelled mechanics are a smaller gap than the eval suggests** (advisor review,
   /mnt/project-files/reviews/unmodelled-mechanics-review.md). Of the 27 `possibly_unmodelled` key pieces in I13 arm B,
   ~9 are defensive pieces in a weapon+body screen (finding 1), ~10 are gated by an unset state or a blind metric, and
   ~8 have no PoB model (Thrilling Chase, Avidity, One with the Storm, Earthbreaker x2, Martial Master, two infusion
   notables). The eval's "all exactly zero damage and EHP change" is wrong: 7 have a non-zero EHP delta (Harmony
   Within: +17% EHP on removal, still labelled possibly_unmodelled), a verdict bug fixed in L2.
5. **Probes and custom mods can lie silently** (zero or wrong sign, above). Any feature built on custom modifiers needs
   the same discipline as the unparsed-mod check: each probe is calibrated against a reference build with an expected
   sign, or it is not used.
6. **Time: the tree dominates** (64 of 154 s, 42%) and every call re-plans from an empty tree (`reset=True`). In a loop,
   later passes should warm-start from the current tree; whether `reset=False` with swap moves holds quality is
   unmeasured (L3 measures it).
7. **Redundant work.** Slate `deepen` re-runs supports and tree from scratch instead of starting from the screen build;
   ablation boots its own engine and pool per candidate (boot is cheap at 2 s, the repeated searches are not); a unique
   ablation runs a gear search. Engine boot itself is not a cost worth optimising.
8. **Ideas are not granular enough to test.** A slate candidate is a spec + quoted claims + key pieces. It never states
   the mechanism as a testable quantity (which stat is the payoff, which constraint should bind). The Squire
   theorycraft reasoned in exactly those terms (multiplicative layers, persistent vs consumed payoffs); the pipeline
   cannot check such a claim.

## 2. Design

### 2.1 One objective for every stage

`Objective` = (PoB keys to read, pure function stats -> score), built from the run's benchmarks with the existing
`benchmarks.boss_metrics` / `pack_metrics`. Score is lexicographic: first the constraint deficit (floors, survive every
named hit with margin >= 1, the TTK gate if the owner sets it as hard), then the goal (minimise TTK, or pack clear).
Supports and gear score candidates with it through the pool (keys already batched); the tree, whose optimiser is
PoB-side and takes only weighted goals, gets weights from the objective's linearisation (2.2), so all three stages pull
in the same direction. Ranking stays benchmark-only. This replaces I15 (defensive gear before the survival check).

### 2.2 Diagnosis: calibrated probes -> shadow prices

`data/probes.yaml`: ~15 generic levers as custom-modifier lines (more damage, crit chance, crit damage, speed, skill
level, added damage per type, penetration/exposure, life, ES, armour, evasion, resists, block), each with a unit cost
(tier points per unit, from `data/tiers.yaml` mod ranks where one exists) and a calibration case (reference build,
expected sign, tolerance). `diagnose(build)` evaluates every probe (~5 s), converts each delta to a change in the
objective, and returns shadow prices (objective gain per tier point), the binding constraint, and the probes that
failed calibration. Uncalibrated probes are excluded, never reported as zero.

### 2.3 Inner loop (numeric, no LLM)

```
seed -> [diagnose -> choose move -> search stage under Objective -> evaluate] repeat -> converged build + trace
```

- Moves: supports re-search, tree re-plan (warm or reset; weights from shadow prices), gear re-search per slot or
  budget reallocation. v1 = round-robin coordinate descent to convergence; v2 = diagnosis picks the move with the
  highest expected gain per second. v2 ships only if it beats v1 on the same budget across the benchmark builds.
- Stop: a full round gains < 1% of the objective, or the time budget (preflight-estimated) is spent.
- Trace: `trace.jsonl` (move, objective before/after, seconds, evals, shadow prices). The report shows the convergence
  curve; the slate's `deepen` continues the screen build's loop instead of restarting.

### 2.4 Outer loop (LLM client, via MCP)

The LLM stays outside the server (decided, docs/pipeline.md). Each slate candidate gains a **mechanism hypothesis**:
the probe(s) its key pieces should make the top shadow price, or the constraint it relieves. After the inner loop the
server returns a diagnosis in words (binding constraint, top levers, refuted hypotheses, unmodelled pieces) through a
`diagnose` tool and the run report; the client edits the spec (swap a key piece, add a condition, change ascendancy or
base) and re-runs. Verification gains a second test beside ablation: a hypothesis is confirmed when the named lever is
top-3 by shadow price, refuted otherwise.

### 2.5 Mechanics PoB does not compute

Revised after the advisor review (above). Three steps, cheapest and assumption-free first:

1. **Cause per zero-delta piece, engine-derived (L2)**: unparsed line / unset config state / metric blind to the effect /
   empty slots / no compute. Plus a whole-catalogue census by sweep, so the true no-model set is counted, not guessed.
2. **L5a, no assumptions**: a registry keyed by mechanic primitive, filled only from the top two rungs of a fidelity
   ladder: PoB config input > parameter-free algebra from the stat text. Invariant test per entry; the repin retires
   entries PoB now moves natively. Ablation on a modelled piece is circular, so it is counted as `modelled_confirmed`.
3. **L5b, uptime assumptions (owner card after the census)**: ranking stays on the pure PoB number; the report shows the
   ceiling and the break-even uptime, never a ranked band (uptime dominates, so a band would be false precision).
   Assumption 0 must reproduce the pure number. Cast on Critical Energy waits for the 1.0 repin.

## 3. Ranked plan

Order = quality gained per cost, with measurement before each change kept. Sizes target < 150k tokens each.

| id | task | why first | model | depends |
|---|---|---|---|---|
| L1 | `Objective` from benchmarks; supports + gear score with it; lexicographic constraints; golden + 5 eval candidates before/after (survival pass rate, TTK) | finding 1: largest quality loss; subsumes I15 | Sonnet | - |
| L2 | `data/probes.yaml` + calibration test + `diagnose` (CLI + MCP): shadow prices, binding constraint; fix or drop the lying probes; ablation EHP verdict fix; cause per zero-delta piece + catalogue census | findings 3, 4, 5; needed by L3-L5 | Sonnet | - |
| L3 | inner loop v1: round-robin to convergence, trace, tree weights from L2, warm-start tree measured vs reset, deepen continues screen | finding 2, 6, 7 | Sonnet | L1, L2 |
| L4 | inner loop v2: diagnosis-directed moves; keep only if it beats v1 at equal budget on golden + 4 builds | finding 3 | Sonnet | L3 |
| L5a | mechanic registry, assumption-free rungs only (2.5 step 2) | finding 4 | Opus design, Sonnet build | L2 census |
| L5b | uptime-assumption ceilings with break-even uptime (2.5 step 3) | finding 4 | Sonnet | owner card after census |
| L6 | outer loop: mechanism hypothesis in slate schema, `diagnose` text in report/MCP, ideate prompt rule; eval re-run (I13 protocol) measuring confirmation, survival, rank stability | finding 8 | Opus | L1-L4 |

Kept from STATE: I14 (cheap ablation re-run) can run any time. I15 folds into L1, I16 into L2 (cause labels).

Success measures (L6 eval, same 5 prompts): survival gate passes for a majority of boss-brief candidates and still
separates them; a loop's final objective beats today's single pass on every golden build; hypotheses confirmed or
refuted for every candidate (no silent zero).


## 4. L1 result (2026-11-23): benchmark objective in supports and gear

Built: `pos_pipeline/objective.py` (`Objective`), used by `search_supports(objective=)`, `GearSearcher(objective=)`,
`engine_stages(objective=True, hard_ttk=False)` (on whenever the spec/slate names benchmarks), `EngineRunner(objective=)`,
CLI `--no-objective` / `--hard-ttk`. Key = `(-deficit, goal)`: deficit = sum of fractional shortfalls (stat floors,
survive every named hit, optional TTK gate; floors unclamped so negative resists keep a gradient), goal = sum of ln
rate (-ln TTK per boss, -ln clear per pack). Tree stage unchanged (still metric; weights from the objective wait for L2/L3).
Ranking is unchanged. Scoring evaluates every candidate once per benchmark, so searches cost about 2x evals.
Scripts: `tools/measure_l1_stages.py` (paired, same input, common yardstick), `tools/measure_l1.py` (end to end).

Paired stages (same input build, scored by one common objective; lower deficit / higher goal is better):
| case | supports metric -> objective (deficit, goal) | gear metric -> objective (deficit, goal) | gear wall |
|---|---|---|---|
| golden | 6.60,-3.58 -> 6.07,-3.08 | 2.68,0.81 -> 2.45,0.81 | 35 -> 105 s |
| p1 | equal | 5.27,-12.71 -> 5.10,-12.63 | 25 -> 54 s |
| p2 | equal | 4.14,-1.61 -> 4.07,-1.22 | 23 -> 62 s |
| p3 | 6.37,-2.07 -> 6.07,-1.95 | 5.32,2.16 -> 5.23,2.16 | 29 -> 68 s |
| p4 | 6.04,-21.27 -> 6.04,-18.22 | 4.08,-17.47 -> 3.98,-17.75 | 25 -> 76 s |
| p5 | 6.36,-19.42 -> 6.36,-16.36 | 4.35,-13.44 -> 4.29,-13.38 | 25 -> 93 s |
Supports never lose on the objective (better in 4 of 6, equal in 2). Gear lowers the deficit in 6 of 6; the goal is
equal or better in 5 of 6 (p4 -0.28: the deficit was traded first, as designed).

End to end (supports, tree, gear, benchmark; golden + the rank-1 candidate of each I13 arm-B slate; metric -> objective):
| case | Arbiter survive | TTK s | pack clear s | wall s |
|---|---|---|---|---|
| golden | yes -> yes | 280 -> 299 | 67 -> 72 | 152 -> 305 |
| p1 | no -> no | 2861 -> 2269 | 116 -> 134 | 62 -> 128 |
| p2 | no -> no | 5254 -> 5254 | 14300 -> 4965 | 86 -> 142 |
| p3 | yes -> yes | 94 -> 71 | 133 -> 102 | 133 -> 254 |
| p4 | no -> yes | 181 -> 238 | 11035 -> 745 | 110 -> 189 |
| p5 | no -> yes | 221 -> 253 | 3104 -> 136 | 119 -> 140 |
Survival pass rate 2/6 -> 4/6. Pack clear improves in 4 of 6 (large where it was absurd). Boss TTK improves in 2, equal in
1 and is worse in 3 (golden, p4, p5): the objective spends boss damage on survival and clear, which is the intent, not a
free gain. Wall time 1.75x in total (662 -> 1158 s). Golden floors stay unmet in both arms (3 gear slots cannot cover
resists; G7b) and the single feed-forward pass remains order-dependent (L3). Limits: one run per cell (no variance
estimate), the 6 cases share one machine, and the golden TTK and clear get worse, so L1 is a constraint fix, not a DPS gain.
Engine note: `GearSearcher` scores whole-build keys through the pool, because each `load_build_xml` on the long-lived
engine leaks memory (p5 hit the 3.5 GB watchdog before this).

## 5. Acceptance test: the owner's end experience (cmsg_01RxGYnd78N9kMbbAJ5pWDhU1dnxqDdRaEYAuumsEdPHoc)

Player prompt (e.g. "Squire + Cyclone") -> several likely-competitive build ideas -> sim validates each -> several
rounds of creative improvement, each driven by sim deltas and failure causes -> results for the player. One entry point,
no manual steps between. The end-to-end Squire + Cyclone run is the acceptance eval; it passes when it runs unattended,
keeps the best build per round, stops on no gain, and reports the ranked builds with the sim evidence for each change.
Squire rows are ASSUMED until 1.0 data (K4). Gap map: ideas + validation exist (I-series); L1 makes validation judge
survival; L2 supplies failure causes (diagnose); L3 is the iteration (rounds, keep best, stop on no gain, trace);
L4 directs moves by diagnosis; L6 is the single entry point with the creative-improvement step and the final report;
the acceptance eval is the L6 eval re-run with this prompt.
