# Ideation evaluation (I7)

Status: 2026-11-22, data 601768b. Owner requirement cmsg_01RxGYnd78N9kMbbAJ5pWDhU6o4n9NQafMk2fcJq7WYpEm (think creatively from a high-level prompt). Design: `docs/ideation.md`. Harness: `tools/eval_ideation.py`; inputs and outputs: `evals/ideation/<prompt>/` (round*.yaml = every slate submitted to the gate, notes.md = the client's own log, run/ = `slate run` output); table: `evals/ideation/results.md`.

## Method

- Five prompts chosen to stress different parts: p1 the design example with a budget tier ("tanky lightning build that deletes Arbiter on a budget"), p2 a mechanic theme with a negative constraint ("something nasty with ailments that is not a caster"), p3 the mass-mob benchmark ("fast Breach clearing without a bow"), p4 a prompt naming skills absent from the pinned data, taken from the owner's own target build ("Cyclone that builds up charges and dumps them with Elemental Discharge"), p5 an explicitly non-obvious ask with an engine sweep ("use a keystone most players ignore to make a strong boss killer").
- Client: one fresh Sonnet session per prompt, given only the rendered `ideate` text and the CLI equivalents of the MCP tools, told to stop after the gate. Sonnet rather than Opus because it is the cheaper client an owner may run headless; an Opus client was not tested.
- Engine: each final slate screened with `slate run --workers 2 --deepen-k 0` (screen + ablation, no deepening), sequentially (4 vCPU / 16 GB).
- Scoring is deterministic: the harness re-runs the gate on every saved round and reads `slate_run.json`. "Non-obvious" is a judgement (below), not a metric.

Confound: clients used the CLI, not the MCP server. CLI `explain` needed gem ids and `search` printed full JSON; the MCP tools already accept names and return compact cards. Friction reports that are CLI-only are marked so below; the CLI `explain` now accepts names too.

## Results

| prompt | client tokens / wall / tool calls | gate r1 kept | rounds | distinct class / delivery / damage / defence / skill (of 7) | engine screen wall | ablation verdicts | screen rank 1 |
|---|---|---|---|---|---|---|---|
| p1 tanky lightning, budget | 83k / 2.6 min / 22 | 7/7 | 2 (client revised weak claims itself) | 7/3/1/3/7 (damage fixed by prompt) | 10.4 min | confirmed 1, not_load_bearing 3, possibly_unmodelled 7 | Titan Conduit (llm) |
| p2 ailments, not a caster | 79k / 1.9 min / 16 | 7/7 | 1 | 7/2/5/3/7 | 13.7 min | confirmed 1, not_load_bearing 8, possibly_unmodelled 4 | Plague Grenadier (llm): rests on the Fiery Death FullDPS artefact |
| p3 Breach without a bow | 74k / 1.9 min / 22 | 7/7 | 1 | 7/3/4/4/7 | 9.2 min | possibly_unmodelled 5, not_testable 5 (id-form key pieces, bug fixed here) | Corpse Reuse Detonation (llm) |
| p4 Cyclone + Elemental Discharge | 73k / 1.7 min / 16 | 7/7 | 1 | 6/3/4/4/7 | 10.8 min | not_load_bearing 8, possibly_unmodelled 1 | Eye of Winter (llm) |
| p5 ignored keystone | 78k / 2.2 min / 21 | 7/7 | 1 | 7/4/3/3/7 | 10.1 min (amulet slot added for the unarmed candidate) | confirmed 3, not_load_bearing 1, possibly_unmodelled 2, not_testable 1 (unarmed) | Wildsurge Firestorm (llm) |

Totals: 35/35 candidates passed the gate on the first submission; 0 PoE1 names reached the gate; 0 candidates came from sweeps (the only sweep attempted failed, below). Client cost about 78k tokens and 2 minutes per slate; engine screen 9-14 min per 7-candidate slate on 2 workers (preflight estimated ~17 min without deepening, so the estimate is conservative).

### What worked

- **Divergence.** Every slate kept 7 candidates with 7 distinct classes/ascendancies and 7 distinct main skills; mean pairwise difference 4.3-5.3 of 6 archetype fields. No slate collapsed onto one popular build.
- **PoE1 contamination is caught, but upstream of the gate.** Rule 1 ("every remembered name is a guess until resolve says exact") made clients resolve before submitting. Names rejected at resolve: Cyclone (absent from pinned pre-1.0 data; announced for 1.0, so this is a data-version miss, not PoE1 contamination), Elemental Discharge (as a skill), Viper Strike, Caustic Arrow (suggestion Gas Arrow used), Cobra Lash, Wild Strike, plus PoE1-style base names (Expert Ashen Staff, Crude Maul, Warstaff). On p4 the client found the PoE2 mechanic behind the name (Catalysing Elements triggers "Catalysing Discharge") and kept the idea's intent. The gate's resolve and quote checks therefore measured 0 catches; they are the backstop, not the filter.
- **Non-obvious ideas (judgement).** At least one per slate that a typical player would not try first: Berek's Grip making a wind skill count as on shocked ground to trigger Catalysing Discharge without real ground (p4); gas cloud detonated by ignite (p2); corpse reuse detonation for Breach (p3); unarmed Hollow Palm Technique on Invoker (p5); Chaos Inoculation on a lightning Stormweaver (p1). Claims spot-checked against catalogue text were grounded; none described PoE1 behaviour.

### What did not work

1. **The engine half barely verifies the ideas.** Across p1-p4, 2 of 38 testable key pieces were `confirmed` (Doryani's Prototype; Fiery Death, a known artefact). The contrast is p5, whose key pieces are damage keystones: 3 of 6 confirmed (Wildsurge Incantation, Blackflame Covenant, Dance with Death). Ablation works when the claim is about unconditional hit damage; causes of the rest, in order of weight:
   - **Ailment and DoT damage is outside the metric.** `data/metrics.yaml` scores melee/attack skills on `TotalDPS` (one hit). Checked on the p2 Rake build with a plain weapon: TotalDPS 1.9, BleedDPS 12.1, FullDPS 14.1. An ailment prompt is ranked on the part of the damage it does not care about, and ailment supports read as harmful ("removing it RAISES the metric" on 6 of the 7 p2 support ablations).
   - **Conditional mods read as zero.** Notables and keystones whose text depends on a condition (charges, shocked/frozen enemy, ground surfaces, corpses) come out `possibly_unmodelled` (17 of 38), because the benchmark config profile does not turn those conditions on.
   - **Defensive key pieces are measured on damage.** A "tanky" prompt's key pieces (Shockproof, Chaos Inoculation) cannot be `confirmed` by a DPS ablation.
2. **Screens are weapon-only builds.** Clients gave only a weapon base, so screened builds had ~1-2k life and -50% resistances; every p1 candidate failed the Arbiter survival check and times-to-kill were 900-16,000 s. Ranking is relative at best. Prompt now asks for a body armour base too.
3. **Ranking trusts a known artefact.** p2's rank 1 has FullDPS 96,948 against TotalDPS 2,732 (Fiery Death, flagged as an artefact since G5); the slate ranking does not carry the >3x audit flag.
4. **Sweeps cannot probe attack skills.** The probe seed has no gear, so an attack main skill fails ("probe seed failed to evaluate"; checked: a Spark probe runs, a Boneshatter probe fails). The one sweep in the eval failed, so the engine generator contributed nothing. Prompt now says to probe with a spell. (I12: `weapon=BASE` on the sweep fixes this; prompt updated.)
5. **Gate is easy to pass.** First-pass rate 100% means the gate shaped nothing in this run. It does not check that a claim supports the candidate's engine, that a quote keeps its qualifier (p4 quoted "Wind Skills which can be boosted by Elemental Ground Surfaces count" and dropped the rest), or that a support fits the skill beyond type rules. Ablation was meant to catch weak claims; with finding 1 it cannot yet.
6. **Runner bugs.** Support key pieces written as gem ids were `not_testable` (the gate accepts ids, ablation resolved names only; fixed). A candidate with no gear slot (unarmed p5 candidate) makes `slate run` refuse the whole slate; worked around with `amulet=` on the command line.

## Fixes made in this task (cheap)

- `ideate` prompt: say when a name in the user's own idea is not in PoE2 data and name the substitute; quote the clause carrying the condition; ascendancy passives via `search(kind='notable', ascendancy=...)`; quotes may contain numbers; sweep probes need a spell main skill; give a body armour base, not only a weapon.
- `pos_catalogue explain` CLI accepts a name as well as an id (matches the MCP tool).
- `ablate`: support key pieces resolve by gem id or name.
- Thresholds in `data/ideation.yaml` left unchanged: with a 100% first-pass rate and verification dominated by measurement gaps, there is no evidence to tune them on.

## Open (in STATE.md, in priority order)

- I8: ailment/DoT-aware damage metric (TotalDPS + the build's ailment DPS, or FullDPS with the overlap caveat) for attack and ailment skills; re-run p2.
- I9: carry the G5 >3x audit flag into slate ranking (demote or label rank on an artefact).
- I10: ablation measures EHP as well as damage; a defensive key piece is confirmed on EHP loss.
- I11 (done): per-candidate config conditions declared as `conditions: [...]` in the spec (table `conditions` in `data/config_profiles.yaml`), applied at assembly on top of the config profile and therefore in screen, ablation and the full run; conditional mods are measured instead of `possibly_unmodelled`. Declared conditions are assumptions and are printed per candidate in the slate report. Which conditions are fair per fight is for I13 to review.
- I12: sweep probe seed with a plain weapon base (spec or sweep argument), so attack skills can be probed; runner accepts candidates with no searched slot.
- Re-run this eval (same five prompts, `tools/eval_ideation.py`) after I8-I11; then tune `data/ideation.yaml`.

## I13 re-run (2026-11-23, after I8-I12)

Inputs and outputs: `evals/ideation2/` (`CLIENT_BRIEF.md` = the client protocol, `<p>/prompt.md` = rendered `ideate` text,
`<p>/round*.yaml`, `final.yaml`, `notes.md`, `run/` = fresh slates; `<p>/frozen/` = the I7 final slates re-screened;
`results.md` = gate table from `tools/eval_ideation.py`; `compare.py` = the table below; `runs.txt` = walls).

Four arms, so engine changes and client changes can be told apart:
- **I7**: the baseline above.
- **A**: the I7 final slates, unchanged, screened on the I8-I12 engine (engine-only effect).
- **A2**: the same slates on the I8-I13 engine (adds the fixes below).
- **B**: five fresh Sonnet clients (same protocol as I7, `ideate` text after I11/I12: rule 6 conditions, sweep `weapon=`),
  screened on the I8-I13 engine.
Screens as in I7: `slate run --workers 2 --deepen-k 0`, sequential, 4 vCPU / 16 GB, 8.3-15.3 min per slate.

| arm | candidates | key pieces confirmed (p1-p4) | confirmed (p5) | possibly_unmodelled / not_load_bearing / not_testable (all) | pack value present | rank 1 rests on a confirmed piece | rank 1 on an unlabelled >3x artefact | sweep-sourced | with declared conditions |
|---|---|---|---|---|---|---|---|---|---|
| I7 (baseline) | 35 | 2/43 (5%) | 3/7 | 19 / 20 / 6 | 8/35 | 3/5 | 1/5 | 0 | 0 |
| A: I7 slates, I8-I12 engine | 35 | 3/43 (7%) | 5/7 | 17 / 25 / 0 | 8/35 | 1/5 | 0/5 | 0 | 0 |
| A2: I7 slates, I8-I13 engine | 35 | 3/43 (7%) | 5/7 | 17 / 25 / 0 | 24/35 | 0/5 | 0/5 | 0 | 0 |
| B: fresh slates, I8-I13 engine | 38 | 10/51 (20%) | 3/8 | 27 / 19 / 0 | 22/38 | 2/5 | 0/5 | 2 | 16 |

Columns: share of all ablated key pieces that are `confirmed` (I7's "2 of 38" excluded 5 not_testable; here they count);
"pack value present" = Breach clear proxy computed; "rank 1 rests on a confirmed piece" = the screen's top candidate has
at least one `confirmed` key piece; "unlabelled artefact" = rank 1 with FullDPS > 3x TotalDPS and no audit label.

Client side (B): 81-101k tokens, 2.1-3.4 min, 25-30 tool calls per slate (I7: 73-83k, 1.7-2.6 min, 16-22). Gate first
pass 35/38: rejections were a number word in a claim (p3) and two ascendancy names typed squashed by the client
("BloodMage", p5; resolve returns "Blood Mage", the error was the client's). Divergence held (7-8 distinct classes and
main skills per slate, mean 4.8-5.4 differing fields of 6). 16 of 38 candidates declared conditions (ailments and
charges only; none declared a trash condition).

### Findings

1. **Confirmation rate rose from 5% to 20% (p1-p4), but mostly through the client, not the engine.** On the frozen I7
   slates the I8-I13 engine moved p1-p4 only from 2 to 3 confirmed (A, A2); p5 from 3/7 to 5/7 (ailment-aware metric:
   Rake bleed). Fresh slates (B) reached 10/51: clients now pick key pieces with measurable stat text, give body armour,
   and declare conditions. Declared conditions did not lift confirmation by themselves (6/25 with conditions, 7/34
   without).
2. **The largest remaining bucket is mechanics PoB does not compute** (27 `possibly_unmodelled` in B, all with
   exactly zero damage and EHP change): charge consumption doubling (Thrilling Chase, One with the Storm), aftershock
   chance (Earthbreaker), combo rules (Martial Master), infusion handling (Refracted Infusion, Everlasting Infusions),
   minion/ally keystones (Ancestral Bond). The verdict is honest; the gap is engine coverage, not thresholds.
3. **Ablation compared key supports with stand-ins that look free in PoB.** A: 20 key pieces read "removing it RAISES
   the metric"; the stand-in was Fiery Death (10, triggered FullDPS artefact) or Zerphi's Infamy (5, a Glory requirement
   PoB-PoE2 does not model). Fixed (I13): ablation gates triggered supports as the support search does, and supports
   with an unmodelled use cost (Glory requirement; "can only be used after/while"; "cannot be used until": Hit and Run,
   Ancestral Aid, Catharsis, Zerphi's Infamy) are left out of both. A2 and B ran before the use-condition half of this
   fix: Hit and Run was still the stand-in for 8 (A2) and 4 (B) of the "RAISES" verdicts, so those 12 are undetermined,
   not `not_load_bearing`.
4. **Attacks had no Breach value.** PoB keeps `AverageHit` per hand for attacks and combines only `AverageDamage`
   (CalcOffence `combineStat`), so every attack main skill had no pack value (8/35 present in A). Fixed (I13): attacks
   use `AverageDamage` (expected damage per attack, misses included), labelled in the flags: 24/35 (A2), 22/38 (B).
   Still missing: skills without an AoE radius (no coverage) and one candidate that failed to evaluate.
5. **Ranking: artefacts are now labelled and ranked last** (I9): no rank 1 rests on an unlabelled artefact in A, A2 or
   B (I7: p2's rank 1). Rank 1 still rests on an unconfirmed claim in 3 of 5 slates in B, and the Arbiter survival check
   fails for most screened builds (32 of 38 in B; most of the rest are Breach-only briefs) because screens search weapon + body only, so the survival
   gate does not discriminate and the boss rank is a DPS rank.
6. **Engine sweeps now contribute**: 3 of 5 clients ran a sweep, 2 candidates came from sweep leads (p1 Constant Gale,
   ranked 3/8 with both key pieces `confirmed`; p2 Avatar of Fire, ranked 2/7). Two keystone sweeps crashed (engine code
   -9 in `_tree_alloc`): the retry on a fresh engine only ran when the sweep owned its engine, and the MCP job passes
   its own. Fixed (I13): the dead engine is replaced either way. A direct re-run of the reproducer (Boneshatter, plain
   mace, every keystone) peaked at 0.83 GB per allocation, so the runaway stays intermittent and run-dependent.

### Declared conditions: which are fair per fight (judgement)

Before I13 a declared condition held in every benchmark of the build, so a corpse or kill condition also lifted the lone
Arbiter fight. Rule applied (I13): a condition is credited in a fight only where it can be near-permanent there.
`data/config_profiles.yaml` gives each condition `fights` (absent = both); `benchmarks.evaluate` and the slate
ablation switch the rest off (booleans false, numbers 0) and the result's flags name them.

| condition | Arbiter of Ash (lone boss) | Breach T15+ (packs) | reason |
|---|---|---|---|
| power / frenzy / endurance charges, onslaught | yes, if the build has a generator | yes | depends on the source; the client must name it (rule 6) |
| enemy shocked / chilled / ignited / bleeding / poisoned | yes, if the build applies it | yes | reapplied by the build's own hits |
| ground shocked / chilled / scorched / brittle / sapped | yes, if the build creates it | yes | the boss stands in it as often as packs do |
| hit_recently, crit_recently | yes | yes | continuous hitting |
| corpses_nearby, killed_recently | **no** | yes | needs trash; Arbiter has none |
| enemy_frozen, enemy_electrocuted, enemy_heavy_stunned (added I13) | **no** | yes | buildup states with short windows on a pinnacle boss; always-on overstates them |

No client in B declared a pack-only condition, so this rule changed no B number; it closes the path for later slates.
The fight's own condition stays the client's argument: nothing checks that a declared ailment is actually applied.

### Thresholds (`data/ideation.yaml`): unchanged

- `ablation_threshold` 0.10: confirmed deltas cluster from 0.103 upward, not-confirmed ones at 0.028-0.09; four pieces
  sit within 0.03 of the line on each side and nothing marks which of them are truly load-bearing. No evidence for a move.
- Gate thresholds: rejections were all genuine (number word, unresolved name); `max_kept` 8 was reached by three slates
  but clients submitted 7-8, so it did not cut anything.

### Remaining gaps (STATE.md)

- I14: re-screen A2/B ablations after the use-condition gate (12 undetermined verdicts), cheap: ablation only.
- I15: screens need defensive gear (or the standard floors) before the Arbiter survival check means anything.
- I16: label `possibly_unmodelled` by cause where PoB has no model (charge consumption, aftershock, combo, infusions),
  so the client is told to choose a measurable key piece instead.
- Pack value for skills without an AoE radius; minion/ally keystones still unrankable.
