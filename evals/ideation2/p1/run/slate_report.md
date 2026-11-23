# Slate report

- Prompt: a tanky lightning build that deletes Arbiter on a budget
- Benchmarks: arbiter_ash, breach_t15. Brief tiers: budget. Screen tier: `budget`. Deepened: top 0.
- Preflight estimate: 8 candidate(s) screened, top 0 deepened: ~20.9 min wall (screen 18.7 min, ablation 2.1 min, deepen 0.0 min); cap 45 min
- successive halving: top 0 of 8 by screen rank deepened; the rest keep their screen numbers
- ranking basis: benchmark metrics only (boss time-to-kill with its survival check, pack clear proxy); a candidate missing a benchmark value ranks after those that have it. Per-skill DPS is shown but never ranks across archetypes.
- ablation measures the objective metric under the first benchmark's PoB options, not time-to-kill, and also TotalEHP: a piece is confirmed when removal costs either at least the threshold; a unique key piece is replaced by the best rare for its slot at the screen tier.
- Numbers are PoB outputs or benchmark formulas over them (`proxy` = density proxy, `ASSUMPTION` = owner-tunable constant). Mechanism claims are quoted from catalogue text; ablation tests whether they matter.

## Screen ranking

| # | candidate | source | archetype | arbiter_ash | breach_t15 | price | key pieces (ablation) | deepened |
|---|---|---|---|---|---|---|---|---|
| 1 | Thunder Monk Staff | llm | invoker / melee / Lightning / armour_evasion | TTK 2860.6s FAIL; DIES; EHP 1,308 | clear 116.2 proxy-s FAIL; coverage 100% | no price: missing anchors weapon:budget, body_armour:budget | I am the Thunder...: confirmed, ...and Protect me from Harm: possibly_unmodelled | no |
| 2 | Plated Thunder Titan | llm | titan / projectile / Lightning / armour | TTK 3916.9s FAIL; DIES; EHP 1,487 | clear 391.5 proxy-s FAIL; coverage 44% | no price: missing anchors weapon:budget, body_armour:budget | Stone Skin: possibly_unmodelled, Brinerot Ferocity: not_load_bearing | no |
| 3 | Gale-Surge Arc Weaver | sweep:probe1/Constant Gale | stormweaver / projectile / Lightning / energy_shield | TTK 694.4s FAIL; survives; EHP 2,032 | clear 1835.1 proxy-s FAIL; coverage 2% | no price: missing anchors body_armour:budget | Constant Gale: confirmed, Force of Will: confirmed | no |
| 4 | Evasion Arrow Pathfinder | llm | pathfinder / projectile / Lightning / evasion | TTK 4925.0s FAIL; DIES; EHP 1,241 | clear 752.0 proxy-s FAIL; coverage 28% | no price: missing anchors weapon:budget, body_armour:budget | Sustainable Practices: possibly_unmodelled, Electrocute: not_load_bearing | no |
| 5 | Mana-Shield Orb Oracle | llm | oracle / projectile / Lightning / mana_shield | TTK 458.2s FAIL; DIES; EHP 1,422 | clear 26584.8 proxy-s FAIL; coverage 4% | no price: missing anchors body_armour:budget | Harmony Within: possibly_unmodelled, The Lesser Harm: confirmed | no |
| 6 | Panther Spear Amazon | llm | amazon / projectile / Lightning / evasion | TTK 6699.3s FAIL; DIES; EHP 1,209 | clear 426.0 proxy-s FAIL; coverage 69% | no price: missing anchors weapon:budget, body_armour:budget | Stalking Panther: possibly_unmodelled | no |
| 7 | Frozen-Life Conduit Lich | llm | lich / area_spell / Lightning / energy_shield | TTK 17355.1s FAIL; DIES; EHP 1,229 | clear 829.4 proxy-s FAIL; coverage 100% | no price: missing anchors body_armour:budget | Eternal Life: possibly_unmodelled, Shock: not_load_bearing | no |
| 8 | Warded Crossbow Witchhunter | llm | witchhunter / attack / unknown / energy_shield | TTK 33483.7s FAIL; DIES; EHP 1,296 | clear n/a | no price: missing anchors weapon:budget, body_armour:budget | Obsessive Rituals: possibly_unmodelled, Ceremonial Ablution: possibly_unmodelled | no |

- Plated Thunder Titan: survival check FAILED on arbiter_ash
- Frozen-Life Conduit Lich: survival check FAILED on arbiter_ash
- Evasion Arrow Pathfinder: survival check FAILED on arbiter_ash
- Warded Crossbow Witchhunter: no value for breach_t15; survival check FAILED on arbiter_ash
- Thunder Monk Staff: survival check FAILED on arbiter_ash
- Panther Spear Amazon: survival check FAILED on arbiter_ash
- Mana-Shield Orb Oracle: survival check FAILED on arbiter_ash

## Candidates

### Thunder Monk Staff

Source: `llm`. Archetype: invoker / melee / Lightning / armour_evasion. Main skill: storm wave.

- Claim: A share of damage becomes extra lightning, converting the whole build to lightning scaling.
  - notable I am the Thunder...: "Gain 10% of Damage as Extra Lightning Damage"
- Claim: Armour mitigation scales from combined armour and evasion, so hybrid gear covers physical hits.
  - notable ...and Protect me from Harm: "Physical Damage Reduction from Armour is based on your combined Armour and Evasion Rating"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: I am the Thunder... | confirmed | +11.5% | +0.0% |  |  |
| notable: ...and Protect me from Harm | possibly_unmodelled | +0.0% | -0.6% |  |  |

### Plated Thunder Titan

Source: `llm`. Archetype: titan / projectile / Lightning / armour. Main skill: falling thunder.

- Claim: Armour from the body piece is boosted, making the armour layer the tank.
  - notable Stone Skin: "50% more Armour from Equipped Body Armour"
- Claim: The same armour also applies against lightning hits, so it is a lightning-specific mitigation.
  - notable Brinerot Ferocity: "+30% of Armour also applies to Lightning Damage"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Stone Skin | possibly_unmodelled | +0.0% | +0.7% |  |  |
| notable: Brinerot Ferocity | not_load_bearing | +3.8% | +2.0% |  |  |

### Gale-Surge Arc Weaver

Source: `sweep:probe1/Constant Gale`. Archetype: stormweaver / projectile / Lightning / energy_shield. Main skill: arc.

- Claim: The surge buff is always on without needing a trigger, which is the damage lever.
  - notable Constant Gale: "You have Arcane Surge"
- Claim: Part of all damage is paid from mana first, and missing mana strengthens the surge, so mana is both defence and offence.
  - notable Force of Will: "of Damage is taken from Mana before Life"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Constant Gale | confirmed | +16.9% | +19.3% |  |  |
| notable: Force of Will | confirmed | +0.0% | +19.3% |  | confirmed on survivability: removal costs 19% of EHP (damage metric moves +0.0%) |

### Evasion Arrow Pathfinder

Source: `llm`. Archetype: pathfinder / projectile / Lightning / evasion. Main skill: lightning arrow.

- Claim: Evasion rating doubles as elemental damage reduction, a direct answer to lightning-heavy boss hits.
  - notable Sustainable Practices: "50% of Evasion Rating also grants Elemental Damage reduction"
- Claim: Lightning damage can electrocute instead of shock.
  - support Electrocute: "Lightning Damage from Supported Skills can inflict Electrocute"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Sustainable Practices | possibly_unmodelled | +0.0% | +2.1% |  |  |
| support: Electrocute | not_load_bearing | -40.0% | +0.0% | Hit and Run | removing it RAISES the metric |

### Mana-Shield Orb Oracle

Source: `llm`. Archetype: oracle / projectile / Lightning / mana_shield. Main skill: ball lightning.

- Claim: Mana acts as a second health pool for hits, under a condition on current mana versus life.
  - notable Harmony Within: "Hit damage is taken from Mana before Life if your current Mana is higher than your current Life"
- Claim: Enemy damage rolls are unlucky, so big hits are statistically smaller.
  - notable The Lesser Harm: "Damage of Enemies Hitting you is Unlucky"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Harmony Within | possibly_unmodelled | +0.0% | -17.0% |  |  |
| notable: The Lesser Harm | confirmed | +23.3% | +1.2% |  |  |

### Panther Spear Amazon

Source: `llm`. Archetype: amazon / projectile / Lightning / evasion. Main skill: lightning spear.

- Claim: Evasion is concentrated in the small armour slots, trading body armour for them.
  - notable Stalking Panther: "Evasion Rating from Equipped Helmet, Gloves and Boots is doubled"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Stalking Panther | possibly_unmodelled | +0.0% | -3.2% |  |  |

### Frozen-Life Conduit Lich

Source: `llm`. Archetype: lich / area_spell / Lightning / energy_shield. Main skill: lightning conduit.
Measured under declared conditions (assumed, not earned by the build): enemy_shocked (Enemy is Shocked; needs lightning hits or a shock source).

- Claim: Life is protected for as long as shield lasts, so the build treats shield as the only health bar.
  - notable Eternal Life: "Your Life cannot change while you have Energy Shield"
- Claim: The cone is built around shocked targets, and the shock support is the declared source of that condition.
  - skill Lightning Conduit: "dealing significantly more damage to Shocked enemies"
  - support Shock: "making it more likely to Shock"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Eternal Life | possibly_unmodelled | +0.0% | +0.4% |  |  |
| support: Shock | not_load_bearing | -25.0% | +0.0% | Extraction | removing it RAISES the metric |

### Warded Crossbow Witchhunter

Source: `llm`. Archetype: witchhunter / attack / unknown / energy_shield. Main skill: galvanic shards.

- Claim: The ascendancy trades away armour and evasion for the ward skill.
  - notable Obsessive Rituals: "Grants Skill: Sorcery Ward"
- Claim: The ward barrier then also soaks physical and chaos hits, not just elemental.
  - notable Ceremonial Ablution: "Sorcery Ward's Barrier can also take Physical and Chaos Damage from Hits"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Obsessive Rituals | possibly_unmodelled | +0.0% | +1.7% |  |  |
| notable: Ceremonial Ablution | possibly_unmodelled | +0.0% | +0.0% |  |  |

## Across the slate

- Generators represented among screened candidates: llm, sweep.
- Ablation: 4 of 15 key pieces confirmed (removal costs at least the configured share of the metric).
