# Slate report

- Prompt: fast Breach clearing without a bow
- Benchmarks: arbiter_ash, breach_t15. Brief tiers: mid. Screen tier: `mid`. Deepened: top 0.
- Preflight estimate: 8 candidate(s) screened, top 0 deepened: ~20.6 min wall (screen 20.5 min, ablation 0.2 min, deepen 0.0 min); cap 45 min
- successive halving: top 0 of 8 by screen rank deepened; the rest keep their screen numbers
- ranking basis: benchmark metrics only (boss time-to-kill with its survival check, pack clear proxy); a candidate missing a benchmark value ranks after those that have it. Per-skill DPS is shown but never ranks across archetypes.
- ablation measures the objective metric under the first benchmark's PoB options, not time-to-kill, and also TotalEHP: a piece is confirmed when removal costs either at least the threshold; a unique key piece is replaced by the best rare for its slot at the screen tier.
- Numbers are PoB outputs or benchmark formulas over them (`proxy` = density proxy, `ASSUMPTION` = owner-tunable constant). Mechanism claims are quoted from catalogue text; ablation tests whether they matter.

## Screen ranking

| # | candidate | source | archetype | arbiter_ash | breach_t15 | price | key pieces (ablation) | deepened |
|---|---|---|---|---|---|---|---|---|
| 1 | Blood Mage Crit Bone Storm | llm | blood mage / channel / Physical / life | TTK 94.0s FAIL; survives; EHP 1,909 | clear 132.8 proxy-s FAIL; coverage 2% | no price: missing anchors weapon:mid, body_armour:mid | Sunder the Flesh: not_load_bearing | no |
| 2 | Stormweaver Shock Ball | llm | stormweaver / projectile / Lightning / energy_shield | TTK 135.1s FAIL; DIES; EHP 1,673 | clear 8276.4 proxy-s FAIL; coverage 4% | no price: missing anchors weapon:mid, body_armour:budget | Shaper of Storms: possibly_unmodelled | no |
| 3 | Shaman Bear Fissures | llm | shaman / channel / unknown / life | TTK 4475.5s FAIL; DIES; EHP 1,254 | clear 6459.4 proxy-s FAIL; coverage 3% | no price: missing anchors weapon:mid, body_armour:budget | Turning of the Seasons: confirmed | no |
| 4 | Titan Aftershock Earthquake | llm | titan / melee / unknown / armour | TTK 8999.3s FAIL; DIES; EHP 1,216 | clear 4984.1 proxy-s FAIL; coverage 9% | no price: missing anchors weapon:mid, body_armour:budget | Earthbreaker: possibly_unmodelled, Stone Skin: possibly_unmodelled | no |
| 5 | Amazon Whirlwind Lance | llm | amazon / projectile / unknown / evasion | TTK 163168.6s FAIL; DIES; EHP 1,188 | clear 472037.8 proxy-s FAIL; coverage 2% | no price: missing anchors weapon:starter, body_armour:budget | Predatory Instinct: possibly_unmodelled | no |
| 6 | Infernalist Ignite Blast | llm | infernalist / channel / Fire / life | TTK 211.3s FAIL; DIES; EHP 1,686 | clear n/a | no price: missing anchors weapon:mid, body_armour:budget | Bringer of Flame: possibly_unmodelled | no |
| 7 | Invoker Thunder Flurry | llm | invoker / melee / Lightning / evasion | TTK 1830.6s FAIL; DIES; EHP 1,188 | clear n/a | no price: missing anchors weapon:mid, body_armour:budget | I am the Thunder...: confirmed, Sunder my Enemies...: not_load_bearing | no |
| 8 | Tactician Ballista Battery | llm | tactician / projectile / unknown / armour | TTK 27177.6s FAIL; DIES; EHP 1,245 | clear n/a incomplete | no price: missing anchors weapon:mid, body_armour:budget | Cannons, Ready!: confirmed | no |

- Titan Aftershock Earthquake: survival check FAILED on arbiter_ash
- Invoker Thunder Flurry: no value for breach_t15; survival check FAILED on arbiter_ash
- Stormweaver Shock Ball: survival check FAILED on arbiter_ash
- Infernalist Ignite Blast: no value for breach_t15; survival check FAILED on arbiter_ash
- Amazon Whirlwind Lance: survival check FAILED on arbiter_ash
- Tactician Ballista Battery: no value for breach_t15; survival check FAILED on arbiter_ash
- Shaman Bear Fissures: survival check FAILED on arbiter_ash

## Candidates

### Blood Mage Crit Bone Storm

Source: `llm`. Archetype: blood mage / channel / Physical / life. Main skill: bonestorm.

- Claim: Bonestorm is channelled, then releases a swarm that explodes and impales.
  - skill Bonestorm: "Channel to conjure a swarm of bone spikes in the air, then release to fire them at enemies and explode."
- Claim: Sunder the Flesh gives spells a high base critical chance, which a no-gear screen would otherwise lack.
  - notable Sunder the Flesh: "Base Critical Hit Chance for Spells is 15%"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Sunder the Flesh | not_load_bearing | +9.0% | +0.0% |  |  |

### Stormweaver Shock Ball

Source: `llm`. Archetype: stormweaver / projectile / Lightning / energy_shield. Main skill: ball lightning.
Measured under declared conditions (assumed, not earned by the build): enemy_shocked (Enemy is Shocked; needs lightning hits or a shock source).

- Claim: Ball Lightning repeatedly discharges bolts at nearby enemies, so many small hits land on every pack member.
  - skill Ball Lightning: "repeatedly discharges bolts of Lightning at nearby enemies"
- Claim: Shaper of Storms lets every hit build shock, which is the declared source of the shocked condition.
  - notable Shaper of Storms: "All Damage from Hits Contributes to Shock Chance"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Shaper of Storms | possibly_unmodelled | +0.0% | +0.0% |  |  |

### Shaman Bear Fissures

Source: `llm`. Archetype: shaman / channel / unknown / life. Main skill: fury of the mountain.

- Claim: Fury of the Mountain pounds the ground repeatedly and the fissures spread in a wide arc, covering a pack in front of the player.
  - skill Fury of the Mountain: "creating Molten Fissures that travel randomly in a wide arc in front of you"
- Claim: Turning of the Seasons gives enemies near the player exposure and adds extra elemental damage.
  - notable Turning of the Seasons: "Enemies in your Presence have Exposure"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Turning of the Seasons | confirmed | +20.6% | +0.0% |  |  |

### Titan Aftershock Earthquake

Source: `llm`. Archetype: titan / melee / unknown / armour. Main skill: earthquake.

- Claim: Earthquake leaves patches that erupt later, so a Breach pack walking into the slam zone eats repeated eruptions.
  - skill Earthquake: "The Jagged Ground erupts in a powerful Aftershock after a duration."
- Claim: Titan adds extra aftershocks to slams, stacking more eruptions onto the same patch of ground.
  - notable Earthbreaker: "25% chance for Slam Skills you use yourself to cause an additional Aftershock"
- Claim: Stone Skin lifts body armour, which carries the defence layer while standing in melee.
  - notable Stone Skin: "50% more Armour from Equipped Body Armour"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Earthbreaker | possibly_unmodelled | +0.0% | +0.0% |  |  |
| notable: Stone Skin | possibly_unmodelled | +0.0% | +0.4% |  |  |

### Amazon Whirlwind Lance

Source: `llm`. Archetype: amazon / projectile / unknown / evasion. Main skill: whirlwind lance.

- Claim: The lance leaves a whirlwind that slows enemies and then collapses for damage, so it pairs a control layer with clear.
  - skill Whirlwind Lance: "Entering the Whirlwind collapses it, dealing damage and causing Knockback."
- Claim: Predatory Instinct reveals weaknesses on rare and unique enemies and boosts damage against them, which covers the boss and the rares in a Breach.
  - notable Predatory Instinct: "50% more damage against enemies with an Open Weakness"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Predatory Instinct | possibly_unmodelled | +0.0% | +0.0% |  |  |

### Infernalist Ignite Blast

Source: `llm`. Archetype: infernalist / channel / Fire / life. Main skill: flameblast.
Measured under declared conditions (assumed, not earned by the build): enemy_ignited (Enemy is Ignited; needs fire hits or an ignite source).

- Claim: Flameblast is channelled and releases a large area explosion, suited to a clumped Breach pack.
  - skill Flameblast: "Releasing the energy causes a devastating explosion that is larger and more intense the longer you Channel for."
- Claim: Bringer of Flame routes all damage into ignite, which is the declared source of the ignited condition.
  - notable Bringer of Flame: "contributes to Flammability and Ignite Magnitudes"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Bringer of Flame | possibly_unmodelled | +0.0% | +0.0% |  |  |

### Invoker Thunder Flurry

Source: `llm`. Archetype: invoker / melee / Lightning / evasion. Main skill: tempest flurry.
Measured under declared conditions (assumed, not earned by the build): enemy_shocked (Enemy is Shocked; needs lightning hits or a shock source).

- Claim: The combo finisher of Tempest Flurry calls a Shocking bolt, which is where the shocked-enemy assumption comes from.
  - skill Tempest Flurry: "calls down a powerful Shocking bolt"
- Claim: Invoker converts part of hit damage into extra lightning on top of the strikes.
  - notable I am the Thunder...: "Gain 10% of Damage as Extra Lightning Damage"
- Claim: Critical hits skip elemental resistance, which matters against a boss with high resistances.
  - notable Sunder my Enemies...: "Critical Hits ignore non-negative Enemy Monster Elemental Resistances"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: I am the Thunder... | confirmed | +10.3% | +0.0% |  |  |
| notable: Sunder my Enemies... | not_load_bearing | +2.8% | +0.0% |  |  |

### Tactician Ballista Battery

Source: `llm`. Archetype: tactician / projectile / unknown / armour. Main skill: siege ballista.

- Claim: Siege Ballista is a crossbow totem whose bolts explode after landing, so damage is delivered by the totems rather than the player.
  - skill Siege Ballista: "Deploy a Ballista Totem that fires bolts skyward, to explode a short time after landing."
- Claim: Cannons, Ready! adds totem capacity and totem speed.
  - notable Cannons, Ready!: "Skills used by Totems have 30% more Skill Speed"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Cannons, Ready! | confirmed | +23.1% | +0.0% |  |  |

## Across the slate

- Generators represented among screened candidates: llm.
- Ablation: 3 of 10 key pieces confirmed (removal costs at least the configured share of the metric).
