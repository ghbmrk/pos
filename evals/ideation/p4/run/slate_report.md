# Slate report

- Prompt: Cyclone that builds up charges and dumps them with Elemental Discharge
- Benchmarks: arbiter_ash, breach_t15. Brief tiers: mid. Screen tier: `mid`. Deepened: top 0.
- Preflight estimate: 7 candidate(s) screened, top 0 deepened: ~20.8 min wall (screen 13.8 min, ablation 7.0 min, deepen 0.0 min); cap 45 min
- successive halving: top 0 of 7 by screen rank deepened; the rest keep their screen numbers
- ranking basis: benchmark metrics only (boss time-to-kill with its survival check, pack clear proxy); a candidate missing a benchmark value ranks after those that have it. Per-skill DPS is shown but never ranks across archetypes.
- ablation measures the objective metric under the first benchmark's PoB options, not time-to-kill; a unique key piece is replaced by the best rare for its slot at the screen tier.
- Numbers are PoB outputs or benchmark formulas over them (`proxy` = density proxy, `ASSUMPTION` = owner-tunable constant). Mechanism claims are quoted from catalogue text; ablation tests whether they matter.

## Screen ranking

| # | candidate | source | archetype | arbiter_ash | breach_t15 | price | key pieces (ablation) | deepened |
|---|---|---|---|---|---|---|---|---|
| 1 | Eye of Winter ground-boosted spell | llm | stormweaver / projectile / Cold / energy_shield | TTK 2796.4s FAIL; DIES; EHP 1,195 | clear 225.4 proxy-s FAIL; coverage 55% | no price: missing anchors weapon:mid | Catalysing Elements: not_load_bearing | no |
| 2 | Falling Thunder power dump | llm | invoker / projectile / Lightning / armour | TTK 1711.7s FAIL; DIES; EHP 972 | clear n/a; coverage 44% incomplete | no price: missing anchors weapon:mid | One with the Storm: possibly_unmodelled | no |
| 3 | Twister projectile discharge | llm | ritualist / projectile / unknown / energy_shield | TTK 5376.7s FAIL; DIES; EHP 1,016 | clear n/a; coverage 1% incomplete | no price: missing anchors weapon:mid | Catalysing Elements: not_load_bearing, Berek's Grip: not_load_bearing | no |
| 4 | Whirling Slash shocked-ground discharge | llm | amazon / melee / unknown / evasion | TTK 7205.5s FAIL; DIES; EHP 1,006 | clear n/a incomplete | no price: missing anchors weapon:mid | Catalysing Elements: not_load_bearing, Berek's Grip: not_load_bearing | no |
| 5 | Spiral Volley frenzy spin | llm | deadeye / projectile / unknown / evasion | TTK 8397.7s FAIL; DIES; EHP 872 | clear n/a; coverage 100% incomplete | no price: missing anchors weapon:mid | Perpetual Charge: not_load_bearing | no |
| 6 | Wind Serpent frenzy dump | llm | amazon / melee / unknown / evasion | TTK 100619.6s FAIL; DIES; EHP 872 | clear n/a; coverage 100% incomplete | no price: missing anchors weapon:starter | Perpetual Charge: not_load_bearing | no |
| 7 | Tornado storm discharge | llm | druid / area_spell / Physical / life | TTK n/a; DIES; EHP 878 | clear n/a; coverage 25% incomplete | no price: missing anchors weapon:starter | Catalysing Elements: not_load_bearing | no |

- Whirling Slash shocked-ground discharge: no value for breach_t15; survival check FAILED on arbiter_ash
- Twister projectile discharge: no value for breach_t15; survival check FAILED on arbiter_ash
- Eye of Winter ground-boosted spell: survival check FAILED on arbiter_ash
- Tornado storm discharge: no value for arbiter_ash, breach_t15
- Wind Serpent frenzy dump: no value for breach_t15; survival check FAILED on arbiter_ash
- Falling Thunder power dump: no value for breach_t15; survival check FAILED on arbiter_ash
- Spiral Volley frenzy spin: no value for breach_t15; survival check FAILED on arbiter_ash

## Candidates

### Eye of Winter ground-boosted spell

Source: `llm`. Archetype: stormweaver / projectile / Cold / energy_shield. Main skill: eye of winter.

- Claim: The eye takes on the effect of elemental ground, making its shards deal more damage of that type.
  - skill EyeOfWinterPlayer: "it will take on that surface's effect"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| support: Catalysing Elements | not_load_bearing | -1300.2% | Fiery Death | removing it RAISES the metric |

### Falling Thunder power dump

Source: `llm`. Archetype: invoker / projectile / Lightning / armour. Main skill: falling thunder.

- Claim: The slam turns stored power charges into forward lightning projectiles.
  - skill FallingThunderPlayer: "Consumes your Power Charges to fire Lightning Projectiles"
- Claim: The notable makes each charge-spending quarterstaff skill count an extra charge.
  - notable One with the Storm: "count as consuming an additional Power Charge"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| notable: One with the Storm | possibly_unmodelled | +0.0% |  |  |

### Twister projectile discharge

Source: `llm`. Archetype: ritualist / projectile / unknown / energy_shield. Main skill: twister.

- Claim: Twisters take on extra damage of the element of any ground they pass over.
  - skill TwisterPlayer: "Passing over Elemental Ground Surfaces or Consuming an elemental Whirlwind"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| support: Catalysing Elements | not_load_bearing | -107.4% | Fiery Death | removing it RAISES the metric |
| unique: Berek's Grip | not_load_bearing | -1.1% | best rare at mid [Two-Stone Ring]: IncreasedAccuracy r4, ColdResistance r1, FireResistance r1, LightningResistance r1 | removing it RAISES the metric |

### Whirling Slash shocked-ground discharge

Source: `llm`. Archetype: amazon / melee / unknown / evasion. Main skill: whirling slash.

- Claim: Catalysing Elements triggers a discharge when the skill is boosted by an elemental ground surface.
  - support SupportCatalysingElementsPlayer: "Triggering Catalysing Discharge of the corresponding type"
- Claim: The ring makes the whirlwind skill count as boosted by shocked ground, so the discharge needs no real ground.
  - unique Berek's Grip: "Wind Skills which can be boosted by Elemental Ground Surfaces count"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| support: Catalysing Elements | not_load_bearing | -50.2% | Zerphi's Infamy | removing it RAISES the metric |
| unique: Berek's Grip | not_load_bearing | -3.7% | best rare at mid [Two-Stone Ring]: LightningDamage r4, ColdResistance r1, FireResistance r1, LightningResistance r1 | removing it RAISES the metric |

### Spiral Volley frenzy spin

Source: `llm`. Archetype: deadeye / projectile / unknown / evasion. Main skill: spiral volley.

- Claim: Spending frenzy charges makes the volley deal more damage and chain.
  - skill SpiralVolleyPlayer: "Consumes Frenzy Charges to cause the arrows to deal more damage"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| support: Perpetual Charge | not_load_bearing | -167.8% | Fiery Death | removing it RAISES the metric |

### Wind Serpent frenzy dump

Source: `llm`. Archetype: amazon / melee / unknown / evasion. Main skill: wind serpent's fury.

- Claim: Each frenzy charge spent adds a serpent that follows the thrust.
  - skill WindSerpentsFuryPlayer: "For each Frenzy Charge consumed, a Wind Serpent follows"
- Claim: The support can keep charges while still granting the consume benefits.
  - support SupportPerpetualChargePlayer: "a chance not to remove each Charge"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| support: Perpetual Charge | not_load_bearing | -87.8% | Zerphi's Infamy | removing it RAISES the metric |

### Tornado storm discharge

Source: `llm`. Archetype: druid / area_spell / Physical / life. Main skill: tornado.

- Claim: A tornado overlapping elemental ground applies that debuff and deals extra damage of that element.
  - skill TornadoPlayer: "absorbs that surface's Debuff"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| support: Catalysing Elements | not_load_bearing | n/a | (socket left empty) |  |

## Across the slate

- Generators represented among screened candidates: llm.
- Ablation: 0 of 9 key pieces confirmed (removal costs at least the configured share of the metric).
