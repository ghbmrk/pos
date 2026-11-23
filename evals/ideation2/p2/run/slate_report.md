# Slate report

- Prompt: something nasty with ailments that is not a caster
- Benchmarks: arbiter_ash, breach_t15. Brief tiers: mid. Screen tier: `mid`. Deepened: top 0.
- Preflight estimate: 7 candidate(s) screened, top 0 deepened: ~24.8 min wall (screen 17.9 min, ablation 6.8 min, deepen 0.0 min); cap 45 min
- successive halving: top 0 of 7 by screen rank deepened; the rest keep their screen numbers
- ranking basis: benchmark metrics only (boss time-to-kill with its survival check, pack clear proxy); a candidate missing a benchmark value ranks after those that have it. Per-skill DPS is shown but never ranks across archetypes.
- ablation measures the objective metric under the first benchmark's PoB options, not time-to-kill, and also TotalEHP: a piece is confirmed when removal costs either at least the threshold; a unique key piece is replaced by the best rare for its slot at the screen tier.
- Numbers are PoB outputs or benchmark formulas over them (`proxy` = density proxy, `ASSUMPTION` = owner-tunable constant). Mechanism claims are quoted from catalogue text; ablation tests whether they matter.

## Screen ranking

| # | candidate | source | archetype | arbiter_ash | breach_t15 | price | key pieces (ablation) | deepened |
|---|---|---|---|---|---|---|---|---|
| 1 | Stacked poison archer | llm | pathfinder / projectile / Chaos / evasion | TTK 5253.9s FAIL; DIES; EHP 1,176 | clear 14300.0 proxy-s FAIL; coverage 2% | no price: missing anchors weapon:budget, body_armour:budget | Overwhelming Toxicity: possibly_unmodelled, Escalating Poison: not_load_bearing | no |
| 2 | Fire-only gas bomber | sweep:probe1/Avatar of Fire | deadeye / projectile / Chaos+Fire / energy_shield | TTK 17411.7s FAIL; DIES; EHP 1,433 | clear 6842.6 proxy-s FAIL; coverage 9% | no price: missing anchors weapon:budget, body_armour:budget | Avatar of Fire: not_load_bearing | no |
| 3 | Freeze then shatter monk | llm | invoker / melee / Cold / evasion | TTK 1460.3s FAIL; DIES; EHP 1,328 | clear n/a | no price: missing anchors weapon:mid, body_armour:budget | I am the Blizzard...: confirmed, Biting Frost II: not_load_bearing | no |
| 4 | Aggravated bleed lance | llm | amazon / melee / Physical / evasion | TTK 5201.2s FAIL; DIES; EHP 1,280 | clear n/a | no price: missing anchors weapon:mid, body_armour:budget | Crimson Assault: possibly_unmodelled, Incision: not_load_bearing | no |
| 5 | Electrocute pulse gunner | llm | tactician / attack / unknown / armour | TTK 5970.0s FAIL; DIES; EHP 1,187 | clear n/a | no price: missing anchors weapon:mid, body_armour:budget | Neural Overload: not_load_bearing | no |
| 6 | Stun-rupture bleeder | llm | warbringer / melee / unknown / armour | TTK 7418.5s FAIL; DIES; EHP 1,203 | clear n/a | no price: missing anchors weapon:mid, body_armour:budget | Rupture: not_load_bearing, Anvil's Weight: possibly_unmodelled | no |
| 7 | Ignite-extending forge blaster | llm | smith of kitava / projectile / Fire / armour | TTK 78.9s FAIL; DIES; EHP 1,608 | clear 566.0 proxy-s FAIL; coverage 3% | no price: missing anchors weapon:budget, body_armour:budget | Eternal Flame II: not_load_bearing, Fiery Death: confirmed | no |

- Aggravated bleed lance: no value for breach_t15; survival check FAILED on arbiter_ash
- Stacked poison archer: survival check FAILED on arbiter_ash
- Fire-only gas bomber: survival check FAILED on arbiter_ash
- Freeze then shatter monk: no value for breach_t15; survival check FAILED on arbiter_ash
- Electrocute pulse gunner: no value for breach_t15; survival check FAILED on arbiter_ash
- Stun-rupture bleeder: no value for breach_t15; survival check FAILED on arbiter_ash
- Ignite-extending forge blaster: survival check FAILED on arbiter_ash; ARTEFACT AUDIT: FullDPS 142,672 > 3x TotalDPS 18,738; time-to-kill rests on FullDPS, ranked after unflagged candidates

## Candidates

### Stacked poison archer

Source: `llm`. Archetype: pathfinder / projectile / Chaos / evasion. Main skill: poisonburst arrow.
Measured under declared conditions (assumed, not earned by the build): enemy_poisoned (Enemy is Poisoned; needs chaos/physical hits or a poison source).

- Claim: Pathfinder raises how many poisons a target can carry, at the cost of shorter poisons.
  - notable Overwhelming Toxicity: "Double the number of your Poisons that targets can be affected by at the same time"
- Claim: Escalating Poison adds an extra poison on each hit, filling those extra slots; the poisoned condition is sustained by the skill's own poison burst.
  - support Escalating Poison: "allowing it to inflict an extra Poison on enemies but shortening the duration of those Poisons"
  - skill Poisonburst Arrow: "Fire a virulent arrow that creates a burst of Poison on hit, affecting all enemies in an area."

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Overwhelming Toxicity | possibly_unmodelled | +0.0% | +0.0% |  |  |
| support: Escalating Poison | not_load_bearing | -40.0% | +0.0% | Hit and Run | removing it RAISES the metric |

### Fire-only gas bomber

Source: `sweep:probe1/Avatar of Fire`. Archetype: deadeye / projectile / Chaos+Fire / energy_shield. Main skill: gas arrow.
Measured under declared conditions (assumed, not earned by the build): enemy_ignited (Enemy is Ignited; needs fire hits or an ignite source).

- Claim: Avatar of Fire converts damage to fire so the fire-heavy arrow and its ignites scale together; the sweep showed it as the top lead for this skill.
  - keystone Avatar of Fire: "75% of Damage Converted to Fire Damage"
- Claim: The gas cloud explodes when an ignited enemy touches it, so the ignited condition is declared and sustained by the arrow's own fire.
  - skill Gas Arrow: "The cloud will detonate if hit by a Detonator skill or if an Ignited enemy touches it, creating a fiery explosion."

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| keystone: Avatar of Fire | not_load_bearing | -34.3% | +0.0% |  | removing it RAISES the metric |

### Freeze then shatter monk

Source: `llm`. Archetype: invoker / melee / Cold / evasion. Main skill: ice strike.
Measured under declared conditions (assumed, not earned by the build): enemy_chilled (Enemy is Chilled; needs cold hits or a chill source); ground_chilled (Enemy stands on Chilled Ground; needs a chilled-ground source).

- Claim: Freezing enemies leaves chilled ground behind, which is where the ground condition comes from.
  - notable I am the Blizzard...: "On Freezing Enemies create Chilled Ground"
- Claim: Biting Frost turns frozen enemies into extra damage and leaves them chilled afterwards.
  - support Biting Frost II: "causing them to deal more damage to Frozen enemies but consume their Freeze, leaving them Chilled"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: I am the Blizzard... | confirmed | +12.8% | +0.0% |  |  |
| support: Biting Frost II | not_load_bearing | -40.0% | +0.0% | Hit and Run | removing it RAISES the metric |

### Aggravated bleed lance

Source: `llm`. Archetype: amazon / melee / Physical / evasion. Main skill: blood hunt.
Measured under declared conditions (assumed, not earned by the build): enemy_bleeding (Enemy is Bleeding; needs physical hits or a bleed source).

- Claim: Crimson Assault makes the bleed stronger and aggravated, which feeds the consume on Blood Hunt.
  - keystone Crimson Assault: "50% more Magnitude of Bleeding you inflict"
  - skill Blood Hunt: "Hitting an enemy that has suffered Blood Loss will cause a blood explosion and also Consume Bleeding."
- Claim: Incision raises the bleed chance on every hit, so enemies are bleeding for the payoff; the bleeding condition is declared and comes from Incision plus the keystone.
  - support Incision: "which causes Enemies to be increasingly more likely to be inflicted with Bleeding"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| keystone: Crimson Assault | possibly_unmodelled | +0.0% | +0.0% |  |  |
| support: Incision | not_load_bearing | -34.6% | +0.0% | Uhtred's Exodus | removing it RAISES the metric |

### Electrocute pulse gunner

Source: `llm`. Archetype: tactician / attack / unknown / armour. Main skill: shockburst rounds.

- Claim: Neural Overload applies electrocute to marked enemies, giving the crossbow ammunition its lightning ailment to pay off.
  - support Neural Overload: "hitting a marked enemy with a supported skill will Electrocute them"
  - skill Shockburst Rounds: "release damaging pulses upon Hitting an enemy affected by a Lightning Ailment"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| support: Neural Overload | not_load_bearing | -41.7% | +0.0% | Fresh Clip II | removing it RAISES the metric |

### Stun-rupture bleeder

Source: `llm`. Archetype: warbringer / melee / unknown / armour. Main skill: boneshatter.
Measured under declared conditions (assumed, not earned by the build): enemy_bleeding (Enemy is Bleeding; needs physical hits or a bleed source).

- Claim: Rupture aggravates bleeding whenever the strike lands on a heavily stunned enemy, which is exactly what Boneshatter causes.
  - support Rupture: "Supported skills Aggravate Bleeding on Hitting Heavily Stunned Enemies."
  - skill Boneshatter: "The Strike will cause a Heavy Stun on enemies that are Primed for Stun."
- Claim: Breaking armour off each hit raises later hits; bleeding is assumed present from bleed sources in the tree.
  - notable Anvil's Weight: "Break Armour equal to 10% of Hit Damage dealt"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| support: Rupture | not_load_bearing | -44.5% | +0.0% | Brutality III | removing it RAISES the metric |
| notable: Anvil's Weight | possibly_unmodelled | +0.0% | +0.0% |  |  |

### Ignite-extending forge blaster

Source: `llm`. Archetype: smith of kitava / projectile / Fire / armour. Main skill: molten blast.
Measured under declared conditions (assumed, not earned by the build): enemy_ignited (Enemy is Ignited; needs fire hits or an ignite source).

- Claim: Eternal Flame lengthens the ignites, so more damage accumulates before the target dies.
  - support Eternal Flame II: "causing its Ignites to last longer"
- Claim: Fiery Death makes ignited enemies explode on death, a chain effect in packs.
  - support Fiery Death: "causing enemies it Ignites to have a chance to explode on death"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| support: Eternal Flame II | not_load_bearing | -21.0% | +0.0% | Fire Attunement | removing it RAISES the metric |
| support: Fiery Death | confirmed | +55.9% | +0.0% | Hit and Run |  |

## Across the slate

- Generators represented among screened candidates: llm, sweep.
- Ablation: 2 of 12 key pieces confirmed (removal costs at least the configured share of the metric).
