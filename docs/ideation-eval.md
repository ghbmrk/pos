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
4. **Sweeps cannot probe attack skills.** The probe seed has no gear, so an attack main skill fails ("probe seed failed to evaluate"; checked: a Spark probe runs, a Boneshatter probe fails). The one sweep in the eval failed, so the engine generator contributed nothing. Prompt now says to probe with a spell.
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
- I11: per-candidate config conditions (charges, enemy ailments, ground, corpses) declared in the slate and applied in screen and ablation, so conditional mods are measured instead of `possibly_unmodelled`.
- I12: sweep probe seed with a plain weapon base (spec or sweep argument), so attack skills can be probed; runner accepts candidates with no searched slot.
- Re-run this eval (same five prompts, `tools/eval_ideation.py`) after I8-I11; then tune `data/ideation.yaml`.
