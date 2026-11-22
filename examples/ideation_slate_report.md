# Slate report

- Prompt: lightning, cold or fire caster that handles Arbiter of Ash on a mid budget
- Benchmarks: arbiter_ash. Brief tiers: mid. Screen tier: `mid`. Deepened: top 1.
- Preflight estimate: 3 candidate(s) screened, top 1 deepened: ~9.6 min wall (screen 5.5 min, ablation 0.4 min, deepen 3.6 min); cap 45 min
- successive halving: top 1 of 3 by screen rank deepened; the rest keep their screen numbers
- ranking basis: benchmark metrics only (boss time-to-kill with its survival check, pack clear proxy); a candidate missing a benchmark value ranks after those that have it. Per-skill DPS is shown but never ranks across archetypes.
- ablation measures the objective metric under the first benchmark's PoB options, not time-to-kill; a unique key piece is replaced by the best rare for its slot at the screen tier.
- Numbers are PoB outputs or benchmark formulas over them (`proxy` = density proxy, `ASSUMPTION` = owner-tunable constant). Mechanism claims are quoted from catalogue text; ablation tests whether they matter.

## Screen ranking

| # | candidate | source | archetype | arbiter_ash | price | key pieces (ablation) | deepened |
|---|---|---|---|---|---|---|---|
| 1 | Ice Nova power charges | llm | stormweaver / area_spell / Cold / life | TTK 287.1s FAIL; survival n/a (named hits unsourced); EHP 1,553 incomplete | no price: missing anchors weapon:mid, amulet:mid | Resonance: possibly_unmodelled | yes |
| 2 | Flameblast channel | llm | stormweaver / channel / Fire / life | TTK 292.3s FAIL; survival n/a (named hits unsourced); EHP 1,679 incomplete | no price: missing anchors weapon:mid, amulet:mid | Avatar of Fire: possibly_unmodelled | no |
| 3 | Spark with cold-immune ring | llm | stormweaver / projectile / Lightning / energy_shield | TTK 320.7s FAIL; survival n/a (named hits unsourced); EHP 1,691 incomplete | no price: missing anchors weapon:mid, amulet:mid | Dream Fragments: possibly_unmodelled, Eldritch Battery: possibly_unmodelled | no |


## Full run, tier `mid`

| # | candidate | arbiter_ash | EHP | price | floors |
|---|---|---|---:|---|---|
| 1 | Ice Nova power charges | TTK 231.9s FAIL; survival n/a (named hits unsourced); EHP 1,672 incomplete | 1,672 | no price: missing anchors weapon:mid, amulet:mid | NOT met |

## Candidates

### Ice Nova power charges

Source: `llm`. Archetype: stormweaver / area_spell / Cold / life. Main skill: ice nova.

- Claim: Power charges replace frenzy charges for the caster
  - keystone Resonance: "Gain Power Charges instead of Frenzy Charges"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| keystone: Resonance | possibly_unmodelled | +0.0% |  |  |

### Flameblast channel

Source: `llm`. Archetype: stormweaver / channel / Fire / life. Main skill: flameblast.

- Claim: Most damage is converted to fire
  - keystone Avatar of Fire: "Damage Converted to Fire Damage"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| keystone: Avatar of Fire | possibly_unmodelled | +0.0% |  |  |

### Spark with cold-immune ring

Source: `llm`. Archetype: stormweaver / projectile / Lightning / energy_shield. Main skill: spark.

- Claim: The ring makes the character immune to chill and freeze
  - unique Dream Fragments: "You cannot be Chilled or Frozen"
- Claim: Mana pool takes over from the energy shield pool
  - keystone Eldritch Battery: "Convert 100% of maximum Energy Shield to maximum Mana"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| unique: Dream Fragments | possibly_unmodelled | +0.0% | best rare at mid [Sapphire Ring]: ColdResistance r1, FireResistance r1, LightningResistance r1 |  |
| keystone: Eldritch Battery | possibly_unmodelled | +0.0% |  |  |

## Across the slate

- Tier `mid`: Ice Nova power charges (stormweaver / area_spell / Cold / life, source `llm`).
- Generators represented among screened candidates: llm.
- Ablation: 0 of 4 key pieces confirmed (removal costs at least the configured share of the metric).
