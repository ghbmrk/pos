# Calibrated probes, `diagnose`, cause triage and the zero-delta census (L2)

Design: docs/loop.md 2.2 and 2.5 step 1. Data: `data/probes.yaml`. Code: `pos_pipeline/diagnose.py`, `pos_pipeline/census.py`,
`classify_zero` in `pos_pipeline/sweep.py`. Tests: `pos_pipeline/tests/test_diagnose.py`.

## What a probe is

One PoB custom-modifier line applied on top of a build (`set_config(custom_mods=...)`), read back from the engine. Its change in
FullDPS, TotalEHP and in every named-benchmark constraint is that lever's marginal value on that build. 17 levers: more damage, increased
spell damage, crit chance, crit damage, cast speed, skill level, added fire/lightning to spells, penetration (fire, lightning, cold), enemy
resistance, life, energy shield, armour, evasion, all resistances.

A probe is usable only when both hold, else it is excluded and listed as `failed`, never shown as zero:

1. **PoB parsed the line.** PoB drops an unparseable custom line without a word (`ConfigTab:BuildModList` keeps only `mods and not extra`).
   `set_config` now returns `customMods.count`, the number of mods that came from the custom lines; 0 = dropped.
2. **It passes its calibration cases.** Each probe lists reference builds (built in-engine: a plain Fireball, Spark, Frost Bomb against a
   Pinnacle boss), the metric and a `[rel_min, rel_max]` window. `python -m pos_pipeline diagnose --calibrate` runs them (about 10 s);
   `diagnose` reads a cache keyed on probes.yaml, `pob_headless.lua` and the PoB pin, so a repin or an edit recalibrates by itself.
   Calibration already earned its keep once: it rejected the assumption "added fire damage to spells does nothing for a lightning skill"
   (it adds +48% on Spark), a wrong expectation of the author's, not of PoB.

A parsed, calibrated probe that moves nothing on a build is a real zero, marked `inert`.

## The three lying probe lines of L0, explained

| audit line | audit result | cause (measured) |
|---|---|---|
| `Enemies have -10% to Lightning Resistance` | 0 | **A true silent drop.** PoB has no parse for the sentence; `customMods.count` = 0. Now excluded by check 1. |
| `Damage Penetrates 10% Lightning Resistance` | 0 | **True for that build.** The golden Spark carries Rakiata's Flow ("hits treat enemy elemental resistances as inverted"). With inverted resistances penetration has nothing to remove. On a plain Spark the same line is +20% (calibrated). A plain Spark with only Rakiata's Flow added reproduces both numbers (0 and -6.7%); each of the other four supports of the golden group leaves +20% / +20%. |
| `Nearby Enemies have -10% to Lightning Resistance` | -6.5% | **True for that build, same cause.** Inverted resistance of -50% becomes -40%: less damage. +20% on a plain Spark. |

So two of the three were not lies but real mechanics the probe vector could not explain. `diagnose` now attaches a `notes` entry to the
`universal` levers (more damage, enemy resistance, added damage) when the sign reverses or the lever vanishes against its calibration, so a
client reads "a mechanism in this build flips the lever" instead of a bare number. `+10 to Intelligence` stays out: PoB damage does not
read Intelligence, so its zero is true and the lever only matters through requirements.

## `diagnose`

`python -m pos_pipeline diagnose BUILD.xml --metric FullDPS --bench arbiter_ash,breach_t15 [--json]`, MCP tool `diagnose(build, metric,
benchmarks, top)`. About 25 s with two benchmarks (each probe reloads the build so no option leaks between contexts).

- **Constraints** from the benchmarks, each as pressure = required / actual (> 1 violated): `ttk@<boss>` (TTK over its gate), `survive@<boss>`
  (1 / the smallest named-hit margin), `clear@<pack>` (clear time over its gate). A constraint whose gate or constants are unsourced is
  listed `unjudged`, never guessed.
- **Binding** = the highest pressure. With nothing judgeable it is `objective` and levers rank by relative metric gain.
- **Relief** of a probe on a constraint = share of its pressure removed. **Shadow price** = relief of the binding constraint per tier point.
  Cost = `affix_points(group, rank) x affixes` from `data/tiers.yaml` for the lever's affix group; `affixes` is an authored sizing (how
  many such affixes the probe step equals) and scales the price only, never the measured gain. Levers with no gear affix (`more_damage`,
  `enemy_res_all`) show relief but no price.

Golden Spark pass-1 build, Arbiter of Ash (fixture `pos_pipeline/tests/fixtures/spark_golden_pass1.xml`): binding = TTK at 4.7x the gate,
survival 0.99 (one hit from death at 1.01 margin). Top levers by price: added lightning 0.083/pt, added fire 0.065/pt, crit chance 0.060/pt
(+21.8% FullDPS per +5%), crit damage 0.026/pt. Defence levers move survival (+23% to +27% relief for +500 life or ES) and have zero price
on TTK: the two constraints need different levers, which is the finding an objective that ignores survival cannot make (loop.md 1.2 #1).

## Ablation verdict fix

`possibly_unmodelled` required a zero damage delta but ignored EHP, so a piece whose removal raised EHP by 17% (Harmony Within) was labelled
unmodelled. Now (`sweep._verdict`): confirmed if damage or EHP loss reaches the threshold; `possibly_unmodelled` only if neither the metric
nor EHP moves; anything else is `not_load_bearing` with the EHP change in the note ("modelled: below the confirm threshold, or the piece
costs defence in this build").

## Cause of a zero delta (engine-derived)

`classify_zero(engine, xml, node, allocated=...)` runs on every `possibly_unmodelled` node entry of a sweep and on every ablation with that
verdict. It reads PoB's own parse of the node's stat lines (`get_passive(node, parse=True)`: parsed or not, mod names, gating tags) and
diffs EVERY output scalar (`get_stats("all")`) with and without the node:

| cause | meaning | what to do |
|---|---|---|
| `unparsed` | PoB could not parse a stat line | a true no-model: PoB drops it; count in the census |
| `gated_equipment` | every mod waits on weapon type, shield, dual wield | equip the enabling item, or it is the wrong build |
| `gated_state` | every mod waits on an unset condition or a multiplier at zero | declare the condition (data/config_profiles.yaml) if fair |
| `moves_other_output` | changes PoB outputs, not the metric nor EHP | the metric is blind to it: pick another metric or benchmark |
| `no_compute` | parsed, untagged, nothing changes | PoB parses it but has no compute: a true no-model |
| `no_text` / `not_classified` | no effect text / supports and uniques (not node data) | triaged by their own searches |

## Census

`python -m pos_pipeline census spec.yaml [--kinds keystone,notable,ascendancy] [--conditions none|all|a,b] [--out DIR]`: the existing sweeps
over the whole catalogue on one probe seed, once per condition profile (base, and every declared condition on), with cause counts and a
frequency-ranked list of the stat-line primitives behind `unparsed` and `no_compute`. Notables of other ascendancies cannot be allocated on
this seed; re-run with a spec of that ascendancy.

### Census result (golden Spark seed, FullDPS, pin 601768b; files in the project's census/spark_golden)

| profile | kind | entries | zero-delta | moves_other_output | unparsed (true no-model) |
|---|---|---|---|---|---|
| base | keystone | 33 | 12 | 8 | 4 |
| base | notable (non-ascendancy) | 984 | 322 | 263 | 59 |
| base | seed ascendancy | 10 | 6 | 4 | 2 |
| all declared conditions | notable | 984 | 307 | 251 | 56 |

Of 1,027 entries, 340 read zero on damage; 85% of those (279) are not unmodelled at all: PoB computes them and they move other outputs
(defence, recovery, utility), so the damage metric is blind to them. The true no-model set is the `unparsed` lines: 65 entries (6%), listed
by primitive in census.md (charge-conversion, companion reservation, Remnants, Infusions, Seal, Blind, DoT-taken timing). No entry was
`gated_*` or `no_compute` on this seed. Declaring every condition recovers only 15 notables. Against loop.md's decision boundary for L5b
(true no-model above about 15% of key pieces or blocking an owner target build): the catalogue-wide share is 6%, so the card turns on
the owner's target builds, not on breadth. Limits: one seed (Stormweaver), metric FullDPS; defensive pieces need an EHP or benchmark metric
to be judged, which is L1's job.
