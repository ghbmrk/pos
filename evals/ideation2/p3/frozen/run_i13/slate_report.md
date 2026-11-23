# Slate report

- Prompt: fast Breach clearing without a bow
- Benchmarks: breach_t15. Brief tiers: mid. Screen tier: `mid`. Deepened: top 0.
- Preflight estimate: 7 candidate(s) screened, top 0 deepened: ~18.7 min wall (screen 13.8 min, ablation 4.9 min, deepen 0.0 min); cap 45 min
- successive halving: top 0 of 7 by screen rank deepened; the rest keep their screen numbers
- ranking basis: benchmark metrics only (boss time-to-kill with its survival check, pack clear proxy); a candidate missing a benchmark value ranks after those that have it. Per-skill DPS is shown but never ranks across archetypes.
- ablation measures the objective metric under the first benchmark's PoB options, not time-to-kill, and also TotalEHP: a piece is confirmed when removal costs either at least the threshold; a unique key piece is replaced by the best rare for its slot at the screen tier.
- Numbers are PoB outputs or benchmark formulas over them (`proxy` = density proxy, `ASSUMPTION` = owner-tunable constant). Mechanism claims are quoted from catalogue text; ablation tests whether they matter.

## Screen ranking

| # | candidate | source | archetype | breach_t15 | price | key pieces (ablation) | deepened |
|---|---|---|---|---|---|---|---|
| 1 | Corpse Reuse Detonation | llm | infernalist / area_spell / Fire+Physical / life | clear 51.9 proxy-s FAIL; coverage 9% | no price: missing anchors weapon:mid | SupportCorpseConservationPlayer: not_load_bearing, Meat Recycling: possibly_unmodelled | no |
| 2 | Electrocute Staff Slam | llm | invoker / projectile / Lightning / evasion | clear 167.4 proxy-s FAIL; coverage 44% | no price: missing anchors weapon:mid | SupportEonyrsThunderPlayer: not_load_bearing, Resonance: possibly_unmodelled | no |
| 3 | Chain Spear Amazon | llm | amazon / projectile / Lightning / evasion | clear 460.5 proxy-s FAIL; coverage 69% | no price: missing anchors weapon:mid | SupportChainPlayer: not_load_bearing | no |
| 4 | Wildfire Fireball | llm | chronomancer / projectile / Fire / energy_shield | clear 620.8 proxy-s FAIL; coverage 2% | no price: missing anchors weapon:mid | SupportWildfirePlayer: not_load_bearing | no |
| 5 | Infusion Ball Lightning | llm | stormweaver / projectile / Lightning / energy_shield | clear 10750.0 proxy-s FAIL; coverage 4% | no price: missing anchors weapon:mid | Elemental Equilibrium: possibly_unmodelled | no |
| 6 | Frozen Cascade Chayula | llm | acolyte of chayula / melee / Cold / energy_shield | clear 20421.2 proxy-s FAIL; coverage 1% | no price: missing anchors weapon:mid | Shattering: possibly_unmodelled | no |
| 7 | Molten Fissure Titan | llm | titan / melee / Fire / armour | clear n/a | no price: missing anchors weapon:budget | Aftershocks: possibly_unmodelled, SupportReveberatePlayer: not_load_bearing | no |

- Molten Fissure Titan: no value for breach_t15

## Candidates

### Corpse Reuse Detonation

Source: `llm`. Archetype: infernalist / area_spell / Fire+Physical / life. Main skill: detonate dead.

- Claim: Skills that consume corpses can take effect without destroying them, keeping ammunition for the next blast.
  - support SupportCorpseConservationPlayer: "giving them a chance to take effect without destroying the Corpse"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| support: SupportCorpseConservationPlayer | not_load_bearing | -16.0% | +0.0% | Controlled Destruction | removing it RAISES the metric |
| notable: Meat Recycling | possibly_unmodelled | +0.0% | +0.0% |  |  |

### Electrocute Staff Slam

Source: `llm`. Archetype: invoker / projectile / Lightning / evasion. Main skill: falling thunder.

- Claim: Slain electrocuted enemies explode, spreading damage through a dense Breach pack.
  - support SupportEonyrsThunderPlayer: "Enemies slain while Electrocuted by Supported Skills explode"
- Claim: The slam consumes power charges, which this keystone favours, to throw projectiles forward.
  - skill FallingThunderPlayer: "Consumes your Power Charges to fire Lightning Projectiles forwards from the impact."
  - keystone Resonance: "Gain Power Charges instead of Frenzy Charges"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| support: SupportEonyrsThunderPlayer | not_load_bearing | -40.4% | +0.0% | Hit and Run | removing it RAISES the metric |
| keystone: Resonance | possibly_unmodelled | +0.0% | +0.0% |  |  |

### Chain Spear Amazon

Source: `llm`. Archetype: amazon / projectile / Lightning / evasion. Main skill: lightning spear.

- Claim: Chain adds further chains to the secondary bolts that spread across the pack.
  - support SupportChainPlayer: "Supports Projectile skills and any other skills that Chain"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| support: SupportChainPlayer | not_load_bearing | -99.9% | +0.0% | Hit and Run | removing it RAISES the metric |

### Wildfire Fireball

Source: `llm`. Archetype: chronomancer / projectile / Fire / energy_shield. Main skill: fireball.

- Claim: Ignites inflicted spread to nearby enemies after a delay.
  - support SupportWildfirePlayer: "Spreading Ignites it inflicts to nearby enemies after a delay"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| support: SupportWildfirePlayer | not_load_bearing | -15.0% | +0.0% | Considered Casting | removing it RAISES the metric |

### Infusion Ball Lightning

Source: `llm`. Archetype: stormweaver / projectile / Lightning / energy_shield. Main skill: ball lightning.

- Claim: The orb passes through enemies and repeatedly discharges at those nearby, suiting dense packs.
  - skill BallLightningPlayer: "repeatedly discharges bolts of Lightning at nearby enemies"
- Claim: The keystone changes which infusion remnants appear.
  - keystone Elemental Equilibrium: "Create Lightning Infusion Remnants instead of Fire"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| keystone: Elemental Equilibrium | possibly_unmodelled | +0.0% | +0.0% |  |  |

### Frozen Cascade Chayula

Source: `llm`. Archetype: acolyte of chayula / melee / Cold / energy_shield. Main skill: glacial cascade.

- Claim: Frozen enemies take heavy damage from the final spike, so freeze buildup feeds the damage.
  - skill GlacialCascadePlayer: "Frozen enemies hit by the final spike are dealt heavy damage"
  - notable Shattering: "increased Freeze Buildup"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Shattering | possibly_unmodelled | +0.0% | +0.0% |  |  |

### Molten Fissure Titan

Source: `llm`. Archetype: titan / melee / Fire / armour. Main skill: volcanic fissure.

- Claim: Slam skills you use gain wider aftershocks from this notable.
  - notable Aftershocks: "Slam Skills you use yourself have 30% increased Aftershock Area of Effect"
- Claim: Slower slams are more likely to aftershock.
  - support SupportReveberatePlayer: "have increased chance to cause Aftershocks the longer their Attack time"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Aftershocks | possibly_unmodelled | +0.0% | +0.0% |  |  |
| support: SupportReveberatePlayer | not_load_bearing | -40.0% | +0.0% | Hit and Run | removing it RAISES the metric |

## Across the slate

- Generators represented among screened candidates: llm.
- Ablation: 0 of 10 key pieces confirmed (removal costs at least the configured share of the metric).
