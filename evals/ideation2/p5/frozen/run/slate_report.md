# Slate report

- Prompt: use a keystone most players ignore to make a strong boss killer
- Benchmarks: arbiter_ash, breach_t15. Brief tiers: mid. Screen tier: `mid`. Deepened: top 0.
- Preflight estimate: 7 candidate(s) screened, top 0 deepened: ~13.9 min wall (screen 13.8 min, ablation 0.1 min, deepen 0.0 min); cap 45 min
- successive halving: top 0 of 7 by screen rank deepened; the rest keep their screen numbers
- ranking basis: benchmark metrics only (boss time-to-kill with its survival check, pack clear proxy); a candidate missing a benchmark value ranks after those that have it. Per-skill DPS is shown but never ranks across archetypes.
- ablation measures the objective metric under the first benchmark's PoB options, not time-to-kill, and also TotalEHP: a piece is confirmed when removal costs either at least the threshold; a unique key piece is replaced by the best rare for its slot at the screen tier.
- Numbers are PoB outputs or benchmark formulas over them (`proxy` = density proxy, `ASSUMPTION` = owner-tunable constant). Mechanism claims are quoted from catalogue text; ablation tests whether they matter.

## Screen ranking

| # | candidate | source | archetype | arbiter_ash | breach_t15 | price | key pieces (ablation) | deepened |
|---|---|---|---|---|---|---|---|---|
| 1 | Wildsurge firestorm caster | llm | chronomancer / area_spell / Fire / energy_shield | TTK 158.4s FAIL; DIES; EHP 941 | clear 35378.2 proxy-s FAIL; coverage 1% | no price: missing anchors weapon:mid | Wildsurge Incantation: confirmed | no |
| 2 | Chaos ignite flameblast | llm | infernalist / channel / Fire / energy_shield | TTK 64.4s FAIL; DIES; EHP 1,185 | clear n/a | no price: missing anchors weapon:mid | Blackflame Covenant: confirmed | no |
| 3 | Accurate hammer titan | llm | titan / melee / unknown / armour | TTK 792.9s FAIL; DIES; EHP 1,011 | clear n/a; coverage 16% incomplete | no price: missing anchors weapon:mid | Resolute Technique: not_load_bearing | no |
| 4 | Unarmed palm monk | llm | invoker / melee / Physical / evasion | TTK 1726.6s FAIL; DIES; EHP 949 | clear n/a incomplete | ~estimate, anchored on 0 samples, dated hand-set bands only | Hollow Palm Technique: confirmed | no |
| 5 | Empty offhand perfect strike | llm | warbringer / channel / Fire / armour | TTK 2777.6s FAIL; DIES; EHP 1,107 | clear n/a incomplete | no price: missing anchors weapon:budget | Dance with Death: confirmed | no |
| 6 | Aggravated spear bleeder | llm | amazon / melee / Physical / evasion | TTK 8920.2s FAIL; DIES; EHP 949 | clear n/a incomplete | no price: missing anchors weapon:mid | Crimson Assault: confirmed | no |
| 7 | Pure fire crossbow | llm | tactician / projectile / Fire / evasion | TTK n/a; DIES; EHP 1,059 | clear n/a; coverage 2% incomplete | no price: missing anchors weapon:starter | Avatar of Fire: possibly_unmodelled | no |

- Aggravated spear bleeder: no value for breach_t15; survival check FAILED on arbiter_ash
- Wildsurge firestorm caster: survival check FAILED on arbiter_ash
- Chaos ignite flameblast: no value for breach_t15; survival check FAILED on arbiter_ash
- Unarmed palm monk: no value for breach_t15; survival check FAILED on arbiter_ash
- Empty offhand perfect strike: no value for breach_t15; survival check FAILED on arbiter_ash
- Accurate hammer titan: no value for breach_t15; survival check FAILED on arbiter_ash
- Pure fire crossbow: no value for arbiter_ash, breach_t15

## Candidates

### Wildsurge firestorm caster

Source: `llm`. Archetype: chronomancer / area_spell / Fire / energy_shield. Main skill: firestorm.

- Claim: Firestorm is a Storm spell, so the keystone raises its damage and lowers its cost
  - skill FirestormPlayer: "Rain a storm of flaming bolts over the targeted area."
  - keystone Wildsurge Incantation: "deal 50% more damage"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| keystone: Wildsurge Incantation | confirmed | +33.3% | +0.0% |  |  |

### Chaos ignite flameblast

Source: `llm`. Archetype: infernalist / channel / Fire / energy_shield. Main skill: flameblast.

- Claim: Flameblast is a fire spell, so its fire damage turns into chaos and still feeds ignite
  - keystone Blackflame Covenant: "Chaos Damage from Fire Spells Contributes to Flammability and Ignite Magnitudes"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| keystone: Blackflame Covenant | confirmed | +53.4% | +0.0% |  |  |

### Accurate hammer titan

Source: `llm`. Archetype: titan / melee / unknown / armour. Main skill: hammer of the gods.

- Claim: The hammer hit is a slam that scales off the weapon, and the keystone boosts accuracy at the cost of critical hits
  - keystone Resolute Technique: "Accuracy Rating is Doubled"
  - skill HammerOfTheGodsPlayer: "dealing immense damage based on your weapon"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| keystone: Resolute Technique | not_load_bearing | -5.2% | +0.0% |  | removing it RAISES the metric |

### Unarmed palm monk

Source: `llm`. Archetype: invoker / melee / Physical / evasion. Main skill: killing palm.

- Claim: With both hands empty the monk still attacks as though holding a staff, and gets speed from evasion on armour
  - keystone Hollow Palm Technique: "Can Attack as though using a Quarterstaff while both of your hand slots are empty"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| keystone: Hollow Palm Technique | confirmed | +100.0% | +0.0% |  |  |

### Empty offhand perfect strike

Source: `llm`. Archetype: warbringer / channel / Fire / armour. Main skill: perfect strike.

- Claim: A single-hand weapon with nothing in the off hand grants extra skill speed to the strike
  - keystone Dance with Death: "a One-Handed Martial Weapon equipped in your Main Hand"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| keystone: Dance with Death | confirmed | +20.0% | +0.0% |  |  |

### Aggravated spear bleeder

Source: `llm`. Archetype: amazon / melee / Physical / evasion. Main skill: rake.

- Claim: Rake inflicts bleeding on everything it strikes, and the keystone makes that bleed aggravated
  - skill RakePlayer: "inflicting Bleeding on all enemies struck."
  - keystone Crimson Assault: "Bleeding you inflict is Aggravated"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| keystone: Crimson Assault | confirmed | +24.2% | +0.0% |  |  |

### Pure fire crossbow

Source: `llm`. Archetype: tactician / projectile / Fire / evasion. Main skill: molten blast.

- Claim: Molten Blast is already a fire attack, so converting damage to fire loses little
  - keystone Avatar of Fire: "Deal no Non-Fire Damage"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| keystone: Avatar of Fire | possibly_unmodelled | n/a | +0.0% |  |  |

## Across the slate

- Generators represented among screened candidates: llm.
- Ablation: 5 of 7 key pieces confirmed (removal costs at least the configured share of the metric).
