# Slate report

- Prompt: something nasty with ailments that is not a caster
- Benchmarks: arbiter_ash, breach_t15. Brief tiers: mid. Screen tier: `mid`. Deepened: top 0.
- Preflight estimate: 7 candidate(s) screened, top 0 deepened: ~20.7 min wall (screen 13.8 min, ablation 6.9 min, deepen 0.0 min); cap 45 min
- successive halving: top 0 of 7 by screen rank deepened; the rest keep their screen numbers
- ranking basis: benchmark metrics only (boss time-to-kill with its survival check, pack clear proxy); a candidate missing a benchmark value ranks after those that have it. Per-skill DPS is shown but never ranks across archetypes.
- ablation measures the objective metric under the first benchmark's PoB options, not time-to-kill; a unique key piece is replaced by the best rare for its slot at the screen tier.
- Numbers are PoB outputs or benchmark formulas over them (`proxy` = density proxy, `ASSUMPTION` = owner-tunable constant). Mechanism claims are quoted from catalogue text; ablation tests whether they matter.

## Screen ranking

| # | candidate | source | archetype | arbiter_ash | breach_t15 | price | key pieces (ablation) | deepened |
|---|---|---|---|---|---|---|---|---|
| 1 | Plague Grenadier | llm | witchhunter / projectile / Chaos+Fire / life | TTK 136.4s FAIL; DIES; EHP 1,281 | clear n/a; coverage 6% incomplete | no price: missing anchors weapon:mid | Bursting Plague: not_load_bearing, Fiery Death: confirmed | no |
| 2 | Shock Spirit Shaman | llm | shaman / melee / Lightning / life | TTK 2872.7s FAIL; DIES; EHP 947 | clear n/a incomplete | no price: missing anchors weapon:budget | Electrifying Nature: not_load_bearing | no |
| 3 | Blood Hunt Warbringer | llm | warbringer / melee / Physical / armour | TTK 3846.7s FAIL; DIES; EHP 992 | clear n/a incomplete | no price: missing anchors weapon:mid | Bleed III: not_load_bearing, Bleeding Out: possibly_unmodelled | no |
| 4 | Poison Stack Bow | llm | pathfinder / projectile / Chaos / evasion | TTK 5253.9s FAIL; DIES; EHP 872 | clear n/a; coverage 2% incomplete | no price: missing anchors weapon:budget | Arakaali's Lust: not_load_bearing, Overwhelming Toxicity: possibly_unmodelled | no |
| 5 | Ignited Ground Spear | llm | ritualist / projectile / Fire / evasion | TTK 6898.4s FAIL; DIES; EHP 1,057 | clear n/a; coverage 2% incomplete | no price: missing anchors weapon:budget | Flame Pillar: not_load_bearing, Firestarter: possibly_unmodelled | no |
| 6 | Aggravated Bleed Raker | llm | amazon / melee / Physical / evasion | TTK 10100.4s FAIL; DIES; EHP 949 | clear n/a incomplete | no price: missing anchors weapon:mid | Crimson Assault: possibly_unmodelled, Deep Cuts I: not_load_bearing | no |
| 7 | Gas Cloud Ignite Bow | llm | deadeye / projectile / Chaos+Fire / evasion | TTK 18531.7s FAIL; DIES; EHP 1,057 | clear n/a; coverage 9% incomplete | no price: missing anchors weapon:budget | Firestarter: not_load_bearing, Searing Flame I: not_load_bearing | no |

- Poison Stack Bow: no value for breach_t15; survival check FAILED on arbiter_ash
- Gas Cloud Ignite Bow: no value for breach_t15; survival check FAILED on arbiter_ash
- Plague Grenadier: no value for breach_t15; survival check FAILED on arbiter_ash
- Aggravated Bleed Raker: no value for breach_t15; survival check FAILED on arbiter_ash
- Blood Hunt Warbringer: no value for breach_t15; survival check FAILED on arbiter_ash
- Shock Spirit Shaman: no value for breach_t15; survival check FAILED on arbiter_ash
- Ignited Ground Spear: no value for breach_t15; survival check FAILED on arbiter_ash

## Candidates

### Plague Grenadier

Source: `llm`. Archetype: witchhunter / projectile / Chaos+Fire / life. Main skill: gas grenade.

- Claim: Poisoned enemies build up Plague and explode when they die, spreading the damage.
  - support SupportBurstingPlaguePlayer: "explode in a Plague Burst on death"
- Claim: Burning effects turn the grenade cloud into a fiery blast.
  - skill ToxicGrenadePlayer: "Burning effects or Detonator skills will cause the cloud to explode"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| support: Bursting Plague | not_load_bearing | -21.4% | Fire Attunement | removing it RAISES the metric |
| support: Fiery Death | confirmed | +88.7% | Atziri's Impatience |  |

### Shock Spirit Shaman

Source: `llm`. Archetype: shaman / melee / Lightning / life. Main skill: primal strikes.

- Claim: Hits on Shocked enemies refresh Shock, and the finishing strike consumes it for a stampede.
  - skill PrimalStrikesPlayer: "refresh Shock duration"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| notable: Electrifying Nature | not_load_bearing | +5.7% |  |  |

### Blood Hunt Warbringer

Source: `llm`. Archetype: warbringer / melee / Physical / armour. Main skill: blood hunt.

- Claim: Bleed is guaranteed by the support so the lunge always has something to consume.
  - support SupportBleedPlayerThree: "causing it to inflict Bleeding"
- Claim: Blood Hunt consumes Bleeding on hit and explodes.
  - skill BloodHuntPlayer: "blood explosion and also Consume Bleeding"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| support: Bleed III | not_load_bearing | -49.9% | Zerphi's Infamy | removing it RAISES the metric |
| notable: Bleeding Out | possibly_unmodelled | +0.0% |  |  |

### Poison Stack Bow

Source: `llm`. Archetype: pathfinder / projectile / Chaos / evasion. Main skill: poisonburst arrow.

- Claim: Poison stacking is the damage multiplier: more Poisons on the target raise hit damage.
  - support SupportArakaalisLustPlayer: "the more Poisons are on the target"
- Claim: The tree lets targets carry far more Poisons at once.
  - notable Overwhelming Toxicity: "Double the number of your Poisons that targets can be affected by at the same time"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| support: Arakaali's Lust | not_load_bearing | -104.9% | Fiery Death | removing it RAISES the metric |
| notable: Overwhelming Toxicity | possibly_unmodelled | +0.0% |  |  |

### Ignited Ground Spear

Source: `llm`. Archetype: ritualist / projectile / Fire / evasion. Main skill: explosive spear.

- Claim: The detonated spear creates Ignited Ground that feeds Ignite.
  - skill ExplosiveSpearPlayer: "creating Ignited Ground"
- Claim: Flame Pillar converts Ignite into extra fire pillars.
  - support SupportFlamePillarPlayer: "Consume Ignite on Hit to create pillars of flame"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| support: Flame Pillar | not_load_bearing | -140.6% | Fiery Death | removing it RAISES the metric |
| notable: Firestarter | possibly_unmodelled | +0.0% |  |  |

### Aggravated Bleed Raker

Source: `llm`. Archetype: amazon / melee / Physical / evasion. Main skill: rake.

- Claim: The keystone makes bleeding aggravated and stronger at the cost of its duration.
  - keystone Crimson Assault: "Bleeding you inflict is Aggravated"
- Claim: Rake inflicts Bleeding on every enemy it strikes.
  - skill RakePlayer: "inflicting Bleeding on all enemies struck"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| keystone: Crimson Assault | possibly_unmodelled | +0.0% |  |  |
| support: Deep Cuts I | not_load_bearing | -100.0% | Zerphi's Infamy | removing it RAISES the metric |

### Gas Cloud Ignite Bow

Source: `llm`. Archetype: deadeye / projectile / Chaos+Fire / evasion. Main skill: gas arrow.

- Claim: The poison cloud explodes when an Ignited enemy touches it, so Ignite feeds the burst.
  - skill GasArrowPlayer: "if an Ignited enemy touches it"
- Claim: Ignite is made stronger and lowers enemy fire resistance.
  - notable Firestarter: "Enemies Ignited by you have -5% to Fire Resistance"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| notable: Firestarter | not_load_bearing | +0.0% |  |  |
| support: Searing Flame I | not_load_bearing | -410.7% | Fiery Death | removing it RAISES the metric |

## Across the slate

- Generators represented among screened candidates: llm.
- Ablation: 1 of 13 key pieces confirmed (removal costs at least the configured share of the metric).
