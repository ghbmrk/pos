# Support search (G5)

`pos_pipeline/supports.py`; CLI `python -m pos_pipeline supports spec.yaml [workers]` (assembles each variant seed, searches, prints best set). Library: `search_supports(cat, pool, xml, skill_id, fixed, metric, slots=None, beam=5, top=12)` -> `SupportSearch` (baseline, `singles` deltas best first, `best`, `no_effect`, `outliers`, eval/cache/failure counts, notes). Independent of the MCP-vs-embedded-API decision.

## Method
1. Baseline: skill + `fixed` supports. Eligible candidates = catalogue supports that apply to the skill (type require/exclude, with `add_types` from the chosen set as an order-insensitive fixed point), are not already fixed, and share no `family` with the set.
2. Single deltas: one pool job per eligible support (`paste_skill` mutation on the seed XML replaces the main group; same metric/keys, so cache hits across variants and tiers).
3. Beam (width 5) over the best 12 positive singles, extending sets until the free slots (`max_supports` - fixed) are full or no extension beats its parent. Sets are scored and deduplicated as unordered.
4. Not enforced here: resist/EHP floors (they belong to the gear stage; supports can lower defences, so the report's re-check applies floors to the final build).

## Verified against PoB (pinned 601768b)
- **Duplicates, same-family and type-incompatible supports are silently ignored by PoB but still counted as socketed** (`check_build` shows `supports: 2` with identical DPS for one vs two Controlled Destruction; Abiding Hex on Spark counted but no effect). Hence the search enforces eligibility itself; otherwise such candidates look like free no-ops. Covered by a test.
- A gem name PoB does not recognise is dropped (reported in `unrecognisedGems`), not counted.
- Socket limit 5 is only a PoB warning (see docs/assemble.md); the search never exceeds the limit.

## Measured (Spark, Sorceress L90, no gear, 4 workers)
221 eligible supports, 370 evals, ~29 s wall including boot (pool general path, reload per candidate). 171 of 221 singles change nothing (conditions not met in the seed, or unmodelled); `no_effect` lists them. These are single-skill, no-gear numbers.

## Caveats (judgement)
- On this gearless seed `Fiery Death` alone shows +20x FullDPS on a lightning skill: implausible without an audit. The search flags any single worth more than 3x baseline in `outliers` and a note; the report must show the flag. Until audited, treat such supports as suspected PoB artefacts or condition effects of the fixed config profile, and re-check the final set on a geared build.
- Beam search over singles misses pairs whose value only appears together (conversion plus matching supports); `fixed.supports` forces them.
- Supports with effects only when a condition holds (charges, enemy state) read as no-effect unless the config profile sets that condition.
