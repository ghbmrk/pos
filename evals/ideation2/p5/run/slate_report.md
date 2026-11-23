# Slate report

- Prompt: use a keystone most players ignore to make a strong boss killer
- Benchmarks: arbiter_ash, breach_t15. Brief tiers: mid. Screen tier: `mid`. Deepened: top 0.
- Preflight estimate: 7 candidate(s) screened, top 0 deepened: ~18.0 min wall (screen 17.9 min, ablation 0.1 min, deepen 0.0 min); cap 45 min
- successive halving: top 0 of 7 by screen rank deepened; the rest keep their screen numbers
- ranking basis: benchmark metrics only (boss time-to-kill with its survival check, pack clear proxy); a candidate missing a benchmark value ranks after those that have it. Per-skill DPS is shown but never ranks across archetypes.
- ablation measures the objective metric under the first benchmark's PoB options, not time-to-kill, and also TotalEHP: a piece is confirmed when removal costs either at least the threshold; a unique key piece is replaced by the best rare for its slot at the screen tier.
- Numbers are PoB outputs or benchmark formulas over them (`proxy` = density proxy, `ASSUMPTION` = owner-tunable constant). Mechanism claims are quoted from catalogue text; ablation tests whether they matter.

## Screen ranking

| # | candidate | source | archetype | arbiter_ash | breach_t15 | price | key pieces (ablation) | deepened |
|---|---|---|---|---|---|---|---|---|
| 1 | Wildsurge Thunderstorm | llm | stormweaver / area_spell / Lightning / energy_shield | TTK 220.7s FAIL; DIES; EHP 1,381 | clear 3103.7 proxy-s FAIL; coverage 7% | no price: missing anchors weapon:mid, body_armour:budget | Wildsurge Incantation: confirmed | no |
| 2 | Primal Hunger Bear Slam | llm | shaman / melee / unknown / armour | TTK 4661.6s FAIL; DIES; EHP 1,406 | clear 2112.2 proxy-s FAIL; coverage 11% | no price: missing anchors weapon:mid, body_armour:budget | Primal Hunger: possibly_unmodelled | no |
| 3 | Resolute Earthquake | llm | titan / melee / unknown / armour | TTK 183240.3s FAIL; DIES; EHP 1,243 | clear 103209.9 proxy-s FAIL; coverage 9% | no price: missing anchors weapon:starter, body_armour:budget | Resolute Technique: not_load_bearing | no |
| 4 | Avatar Forge Hammer | llm | smith of kitava / melee / Fire / armour | TTK 344412.3s FAIL; DIES; EHP 1,274 | clear 135877.5 proxy-s FAIL; coverage 9% | no price: missing anchors weapon:starter, body_armour:budget | Avatar of Fire: not_load_bearing | no |
| 5 | Blood Barbs Exsanguinate | llm | blood mage / spell / Physical / life | TTK 934.6s FAIL; DIES; EHP 1,382 | clear n/a | no price: missing anchors weapon:mid, body_armour:budget | Crimson Assault: confirmed, Blood Barbs: not_load_bearing | no |
| 6 | Ancestral Bond Shockwave | llm | warbringer / other / unknown / armour | TTK n/a; DIES; EHP 1,323 | clear n/a incomplete | no price: missing anchors weapon:starter, body_armour:budget | Ancestral Bond: possibly_unmodelled | no |
| 7 | Blackflame Flameblast | llm | infernalist / channel / Fire / energy_shield | TTK 55.1s pass; survives; EHP 1,738 | clear n/a | no price: missing anchors weapon:mid, body_armour:budget | Blackflame Covenant: confirmed | no |

- Blood Barbs Exsanguinate: no value for breach_t15; survival check FAILED on arbiter_ash
- Wildsurge Thunderstorm: survival check FAILED on arbiter_ash
- Blackflame Flameblast: no value for breach_t15; ARTEFACT AUDIT: FullDPS 102,859 > 3x TotalDPS 31,686; time-to-kill rests on FullDPS, ranked after unflagged candidates
- Primal Hunger Bear Slam: survival check FAILED on arbiter_ash
- Resolute Earthquake: survival check FAILED on arbiter_ash
- Avatar Forge Hammer: survival check FAILED on arbiter_ash
- Ancestral Bond Shockwave: no value for arbiter_ash, breach_t15

## Candidates

### Wildsurge Thunderstorm

Source: `llm`. Archetype: stormweaver / area_spell / Lightning / energy_shield. Main skill: thunderstorm.
Measured under declared conditions (assumed, not earned by the build): enemy_shocked (Enemy is Shocked; needs lightning hits or a shock source).

- Claim: The keystone boosts damage of Storm spells, and this main skill is a Storm spell.
  - keystone Wildsurge Incantation: "deal 50% more damage"
- Claim: The storm drenches enemies so shock lands more easily, which is where the shocked condition comes from.
  - skill Thunderstorm: "Enemies in the area are Drenched, causing them to become Shocked or Frozen more easily"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| keystone: Wildsurge Incantation | confirmed | +33.3% | +0.0% |  |  |

### Primal Hunger Bear Slam

Source: `llm`. Archetype: shaman / melee / unknown / armour. Main skill: furious slam.

- Claim: The keystone enlarges the rage pool and refunds rage as it is spent, feeding a rage-spending slam.
  - keystone Primal Hunger: "Regenerate 1 Rage per second per 4 Rage spent Recently"
- Claim: The slam spends rage for larger shockwaves.
  - skill Furious Slam: "Can spend Rage to create larger shockwaves that leave behind Jagged Ground"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| keystone: Primal Hunger | possibly_unmodelled | +0.0% | +0.0% |  |  |

### Resolute Earthquake

Source: `llm`. Archetype: titan / melee / unknown / armour. Main skill: earthquake.

- Claim: The keystone doubles accuracy and removes crits, so all investment goes to base hit damage and multipliers.
  - keystone Resolute Technique: "Accuracy Rating is Doubled"
- Claim: The slam leaves a ground patch that erupts later, a second damage instance that needs no crit.
  - skill Earthquake: "The Jagged Ground erupts in a powerful Aftershock after a duration"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| keystone: Resolute Technique | not_load_bearing | +3.6% | +0.0% |  |  |

### Avatar Forge Hammer

Source: `llm`. Archetype: smith of kitava / melee / Fire / armour. Main skill: forge hammer.

- Claim: The keystone converts most damage to fire and removes non-fire damage, matching a fire skill.
  - keystone Avatar of Fire: "75% of Damage Converted to Fire Damage"
- Claim: The skill hurls a fiery hammer that slams the ground.
  - skill Forge Hammer: "Hurl a fiery hammer that Slams into the ground and lodges there"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| keystone: Avatar of Fire | not_load_bearing | -184.1% | +0.0% |  | removing it RAISES the metric |

### Blood Barbs Exsanguinate

Source: `llm`. Archetype: blood mage / spell / Physical / life. Main skill: exsanguinate.
Measured under declared conditions (assumed, not earned by the build): enemy_bleeding (Enemy is Bleeding; needs physical hits or a bleed source).

- Claim: The keystone makes every bleed this spell inflicts aggravated and stronger, which is the boss damage source.
  - keystone Crimson Assault: "Bleeding you inflict is Aggravated"
- Claim: The ascendancy notable lets elemental damage add to bleed magnitude.
  - notable Blood Barbs: "Elemental Damage also Contributes to Bleeding Magnitude"
- Claim: The skill itself inflicts the bleed on every enemy its tendrils hit, so the bleed condition is sustained by the build.
  - skill Exsanguinate: "Enemies Hit by the tendrils take Physical damage and are inflicted with Bleeding"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| keystone: Crimson Assault | confirmed | +13.3% | +0.0% |  |  |
| notable: Blood Barbs | not_load_bearing | +3.4% | +0.0% |  |  |

### Ancestral Bond Shockwave

Source: `llm`. Archetype: warbringer / other / unknown / armour. Main skill: shockwave totem.

- Claim: The keystone doubles how many totems can stand, multiplying totem damage on a boss.
  - keystone Ancestral Bond: "Your Totem Limit is doubled"
- Claim: The totem repeatedly slams nearby enemies.
  - skill Shockwave Totem: "Slams the ground around it, repeatedly damaging nearby enemies"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| keystone: Ancestral Bond | possibly_unmodelled | n/a | +0.0% |  |  |

### Blackflame Flameblast

Source: `llm`. Archetype: infernalist / channel / Fire / energy_shield. Main skill: flameblast.
Measured under declared conditions (assumed, not earned by the build): enemy_ignited (Enemy is Ignited; needs fire hits or an ignite source).

- Claim: The keystone turns fire spell damage into chaos damage, sidestepping fire resistance on a boss.
  - keystone Blackflame Covenant: "Fire Spells Convert 100% of Fire Damage to Chaos Damage"
- Claim: Ignite from the spell deals chaos damage and the converted damage still scales ignite.
  - keystone Blackflame Covenant: "Chaos Damage from Fire Spells Contributes to Flammability and Ignite Magnitudes"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| keystone: Blackflame Covenant | confirmed | +39.9% | +0.0% |  |  |

## Across the slate

- Generators represented among screened candidates: llm.
- Ablation: 3 of 8 key pieces confirmed (removal costs at least the configured share of the metric).
