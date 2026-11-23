# Uptime ceilings for mechanics PoB cannot calculate (L5b)

Design: docs/loop.md 2.5 step 3. Data: `data/ceilings.yaml`. Code: `pos_pipeline/ceilings.py`. Tests: `pos_pipeline/tests/test_ceilings.py`.
CLI: `python -m pos_pipeline ceilings BUILD.xml [--metric FullDPS] [--ids a,b] [--required N] [--line id=STAT LINE] [--json]`. MCP tool `ceilings`.
Approval: owner card "Build ceilings for all five families" (cmsg_01RxGYnd78N9kMbbAJ5pWDhUT3u7Ydr6Vj62e7JeaWxzoL).

## What it reports

Ranking stays on the pure PoB number (the floor). For a mechanic the engine cannot time, `evaluate` adds the number with the mechanic ON 100%
of the time (the ceiling), built only from a PoB config option or a parseable custom line. No uptime is assumed and no ranked band is produced.

| field | meaning |
|---|---|
| floor | pure PoB metric of the build as given (assumption 0; `at_uptime(f, c, 0)` returns it) |
| ceiling | metric with the mechanic always on (`at_uptime(f, c, 1)`) |
| headroom | ceiling / floor: how much the mechanic can compound. `compounding` at or above 1.5 (`compounding_ratio`, unsourced reading aid) |
| break-even | with `--required N` (e.g. the runner-up piece's metric): the share of floor to ceiling the mechanic must be on to reach N, or "never even at 100%" |
| joint | all independent state ceilings on at once vs the sum of single gains; `synergy > 0` = the mechanics multiply (the owner's compounding principle). Entries that set the same option count once |

Statuses: `native` (PoB already computes it: modelled_confirmed, not a gap), `derived` (per-charge bonus read from PoB skill data, upper bound),
`evaluated`, `inert` (parsed and applied, nothing in this build reads the state: no value at any uptime), `no_model`, `no_own_damage`,
`needs_data`, `dropped` (PoB parsed 0 mods from the line: no ceiling is shown, never a zero).

## Measured: does PoB compute the per-charge bonus of charge spenders? (`tools/probe_charge_spenders.py`, `evals/l5b/charge_spenders.json`)

Pin 601768b. 26 non-hidden skills carry `SkillConsumes<Power|Frenzy|Endurance>ChargesOnUse`. 17 evaluate on a plain equipped weapon (9 do not:
Barrage, Flame Breath, Oil Barrage, Hollow Form, Pinnacle of Power, 3 totems/cries, Spell Totem). Setting charges to maximum (`use<Type>Charges`)
moves the damage metric for **one**: Spiral Volley (47.8 to 199.7, x4.2). It does not for 12 other skills that deal damage (Falling Thunder,
Flicker Strike, Bonestorm, Lightning Spear, Rain of Arrows, ...). Reasons found: Falling Thunder's per-charge damage mod carries the Projectile
flag but its hit is not a projectile hit in PoB (a plain "150% more Projectile Damage" also reads zero on it); the others scale projectile count,
splits, area or duration, which PoB does not turn into DPS. So the consumer is a gap for most spenders, not a rate-only gap: rate lines (Frenetic,
Fabled Stag, Resonance) would scale a number PoB does not compute.

**Derivation, calibrated on the one native spender.** `spender_data` reads each skill's per-charge stats from PoB's own skill data and applies
`<per-charge x charges>% more Damage` plus the "once charged" multiplier as custom lines; the engine computes the rest. On Spiral Volley with charges
off, the derived lines give 199.689 and PoB's native figure with charges on is 199.689 (test `test_derivation_reproduces_pobs_native_figure`).
On Falling Thunder (Monk, Aegis Quarterstaff, level 90) the derived ceiling is 597 against a floor of 97 (x6.2). Treat that as an upper bound: all
damage of the skill is counted, PoB's own gating would exclude part of it. A spender whose per-charge stats are not damage-shaped is `no_model`
(no ceiling without an assumption about what a projectile or an area is worth).

## The five families, as registered

| family | census lines (15 unparsed, plus Anticipation) | entry | what the ceiling is |
|---|---|---|---|
| charges: income, retention | Frenetic, Resonance (3 lines), The Fabled Stag | `frenzy_charges_max`, `power_charges_max`, `endurance_charges_max`, `charges_kept` | `use<Type>Charges`: charges always at maximum. Shown only as far as the build reads charges (`inert` otherwise) |
| charges: spenders | any skill that consumes charges | `charge_spenders` | native, derived or no_model per the main skill |
| charges: Conduit | "Allies in your Presence gain that Charge instead" | `charges_to_allies` | `no_own_damage`: the player falls to the no-charge floor, the value is on the ally (K4; actor effects `*_charges` in data/actor_effects.yaml) |
| Seal | Anticipation ("Sealed Skills have #% increased Seal gain frequency") | `seal_frequency` | rewritten to the wording PoB parses (`Skills supported by Unleash have {n}% ...`, `SealGainFrequency`) plus `waitForMaxSeals`; `inert` unless an Unleash-supported skill is in the build |
| Infusion | Refracted Infusion | `infusion_consumed` | `conditionInfusionConsumedRecently` always on; PoB has no timing for infusions |
| Companion | Trusted Kinship, Hunting Companion, Lead by Example, Lifelong Friend, Nurturing Guardian, Thirsting Ally, reservation lines | `second_companion` (`needs_data`), `companion_side` (`no_own_damage`) | none on the player's damage: ally sustain or structure. The second Companion needs the actor model (K4, 1.0) |
| Remnants | Remnant Attraction, Storm's Recollection | `remnant_rate` (`no_own_damage`) | PoB computes recovery per Remnant for generating skills but has no creation or collection rate: no ceiling without an unsourced rate |

Of the five families only charges and (when the build has the consumer) Seal and Infusion yield numbers; Companion and Remnants are classified
with the reason, not given a number. That is the finding, stated rather than hidden: a ceiling needs a PoB lever and these have none yet.

## Limits

- Linear blend: `at_uptime` and `break_even` assume the metric is linear in uptime (true for damage averaged over time; not for EHP or survival).
- The registry is data, not a census of the target builds: Knight, Squire and Cyclone are absent from the pinned data (K4, 1.0 repin 2026-12-12), so no
  Cyclone ceiling exists. The charge entries run unchanged on any build once the data lands; the spender derivation covers Cyclone the day PoB's skill
  data has its per-charge stats.
- Seal and Infusion entries were exercised on fixtures with a custom per-state line (Seal: parsed, `inert` on a build with no Unleash support).
- Entries are retired at the repin when PoB moves the metric natively (the `native` status already shows it per spender).
