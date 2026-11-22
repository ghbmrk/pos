# Slate report

- Prompt: a tanky lightning build that deletes Arbiter on a budget
- Benchmarks: arbiter_ash, breach_t15. Brief tiers: budget. Screen tier: `budget`. Deepened: top 0.
- Preflight estimate: 7 candidate(s) screened, top 0 deepened: ~16.7 min wall (screen 13.8 min, ablation 2.8 min, deepen 0.0 min); cap 45 min
- successive halving: top 0 of 7 by screen rank deepened; the rest keep their screen numbers
- ranking basis: benchmark metrics only (boss time-to-kill with its survival check, pack clear proxy); a candidate missing a benchmark value ranks after those that have it. Per-skill DPS is shown but never ranks across archetypes.
- ablation measures the objective metric under the first benchmark's PoB options, not time-to-kill; a unique key piece is replaced by the best rare for its slot at the screen tier.
- Numbers are PoB outputs or benchmark formulas over them (`proxy` = density proxy, `ASSUMPTION` = owner-tunable constant). Mechanism claims are quoted from catalogue text; ablation tests whether they matter.

## Screen ranking

| # | candidate | source | archetype | arbiter_ash | breach_t15 | price | key pieces (ablation) | deepened |
|---|---|---|---|---|---|---|---|---|
| 1 | Titan Conduit Armour-Lightning | llm | titan / area_spell / Lightning / armour | TTK 965.9s FAIL; survives; EHP 1,695 | clear 48.3 proxy-s FAIL; coverage 100% | no price: missing anchors weapon:budget | Shockproof: possibly_unmodelled, Doryani's Prototype: confirmed | no |
| 2 | Shaman Nova Coil | llm | shaman / area_spell / Lightning / armour | TTK 689.0s FAIL; DIES; EHP 1,314 | clear 364.6 proxy-s FAIL; coverage 9% | no price: missing anchors weapon:budget | Lightning Coil: possibly_unmodelled, Frazzled: possibly_unmodelled | no |
| 3 | Stormweaver Arc Inoculated | llm | stormweaver / projectile / Lightning / energy_shield | TTK 464.3s FAIL; DIES; EHP 9 | clear 1234.7 proxy-s FAIL; coverage 2% | no price: missing anchors weapon:budget | Chaos Inoculation: not_load_bearing, Brain Storm: not_load_bearing | no |
| 4 | Invoker Power-Charge Thunder | llm | invoker / projectile / Lightning / evasion | TTK 2654.9s FAIL; DIES; EHP 949 | clear n/a; coverage 44% incomplete | no price: missing anchors weapon:budget | Resonance: possibly_unmodelled | no |
| 5 | Warbringer Storm Wave Imploding | llm | warbringer / melee / Lightning / armour | TTK 2711.3s FAIL; DIES; EHP 884 | clear n/a; coverage 100% incomplete | no price: missing anchors weapon:budget | Imploding Impacts: possibly_unmodelled, Anvil's Weight: possibly_unmodelled | no |
| 6 | Amazon Frenzy Spear | llm | amazon / projectile / Lightning / evasion | TTK 6699.3s FAIL; DIES; EHP 968 | clear n/a; coverage 69% incomplete | no price: missing anchors weapon:budget | Darkray Vectors: possibly_unmodelled | no |
| 7 | Mercenary Electrocute Armour-Break | llm | witchhunter / projectile / Lightning / armour | TTK 15914.1s FAIL; DIES; EHP 927 | clear n/a; coverage 16% incomplete | no price: missing anchors weapon:budget | Breachlord's Rift: not_load_bearing | no |

- Invoker Power-Charge Thunder: no value for breach_t15; survival check FAILED on arbiter_ash
- Stormweaver Arc Inoculated: survival check FAILED on arbiter_ash
- Amazon Frenzy Spear: no value for breach_t15; survival check FAILED on arbiter_ash
- Mercenary Electrocute Armour-Break: no value for breach_t15; survival check FAILED on arbiter_ash
- Warbringer Storm Wave Imploding: no value for breach_t15; survival check FAILED on arbiter_ash
- Shaman Nova Coil: survival check FAILED on arbiter_ash

## Candidates

### Titan Conduit Armour-Lightning

Source: `llm`. Archetype: titan / area_spell / Lightning / armour. Main skill: lightning conduit.

- Claim: Armour also mitigates lightning hits, so the lightning-heavy boss is blunted by the same layer the build stacks.
  - notable Shockproof: "+30% of Armour also applies to Lightning Damage"
- Claim: The body armour extends armour to lightning even further.
  - unique Doryani's Prototype: "+100% of Armour also applies to Lightning Damage"
- Claim: The main skill hits harder against shocked targets, rewarding the shock-focused setup.
  - skill LightningConduitPlayer: "dealing significantly more damage to Shocked enemies"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| notable: Shockproof | possibly_unmodelled | +0.0% |  |  |
| unique: Doryani's Prototype | confirmed | +32.7% | best rare at budget [Scale Mail]: ColdResistance r1, FireResistance r1, LightningResistance r1 |  |

### Shaman Nova Coil

Source: `llm`. Archetype: shaman / area_spell / Lightning / armour. Main skill: enervating nova.

- Claim: The body armour converts part of incoming physical hits into lightning and raises armour and evasion.
  - unique Lightning Coil: "of Physical damage from Hits taken as Lightning damage"
- Claim: The notable strengthens shock the nova inflicts.
  - notable Frazzled: "30% increased Magnitude of Shock you inflict"
- Claim: The nova electrocutes enemies it hits.
  - skill EnervatingNovaPlayer: "Enemies Hit can be Electrocuted by all Lightning damage for a short duration."

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| unique: Lightning Coil | possibly_unmodelled | +0.0% | best rare at budget [Ancestral Mail]: ColdResistance r1, FireResistance r1, LightningResistance r1 |  |
| notable: Frazzled | possibly_unmodelled | +0.0% |  |  |

### Stormweaver Arc Inoculated

Source: `llm`. Archetype: stormweaver / projectile / Lightning / energy_shield. Main skill: arc.

- Claim: Chaos immunity is the tankiness plan: the keystone makes the character immune to the damage type that bypasses shield.
  - keystone Chaos Inoculation: "Immune to Chaos Damage and Bleeding"
- Claim: A cheap notable adds lightning damage.
  - notable Brain Storm: "20% increased Lightning Damage"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| keystone: Chaos Inoculation | not_load_bearing | +4.1% |  |  |
| notable: Brain Storm | not_load_bearing | +3.2% |  |  |

### Invoker Power-Charge Thunder

Source: `llm`. Archetype: invoker / projectile / Lightning / evasion. Main skill: falling thunder.

- Claim: The keystone swaps the charge types so power charges accrue where frenzy charges normally would.
  - keystone Resonance: "Gain Power Charges instead of Frenzy Charges"
- Claim: The slam spends power charges to throw lightning projectiles.
  - skill FallingThunderPlayer: "Consumes your Power Charges to fire Lightning Projectiles forwards from the impact."

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| keystone: Resonance | possibly_unmodelled | +0.0% |  |  |

### Warbringer Storm Wave Imploding

Source: `llm`. Archetype: warbringer / melee / Lightning / armour. Main skill: storm wave.

- Claim: Fully broken armour on the enemy raises all damage it takes from hits, including lightning.
  - notable Imploding Impacts: "Fully Broken Armour you inflict increases all Damage Taken from Hits instead"
- Claim: Hits themselves wear the enemy armour down.
  - notable Anvil's Weight: "Break Armour equal to 10% of Hit Damage dealt"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| notable: Imploding Impacts | possibly_unmodelled | +0.0% |  |  |
| notable: Anvil's Weight | possibly_unmodelled | +0.0% |  |  |

### Amazon Frenzy Spear

Source: `llm`. Archetype: amazon / projectile / Lightning / evasion. Main skill: lightning spear.

- Claim: The boots raise the frenzy charge ceiling.
  - unique Darkray Vectors: "+1 to Maximum Frenzy Charges"
- Claim: The spear throw spends a frenzy charge to multiply into several bursting copies.
  - skill LightningSpearPlayer: "Consumes a Frenzy Charge if possible to cause the main spear to split"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| unique: Darkray Vectors | possibly_unmodelled | +0.0% | best rare at budget [Braced Sabatons]: ColdResistance r7, FireResistance r2, LightningResistance r1 |  |

### Mercenary Electrocute Armour-Break

Source: `llm`. Archetype: witchhunter / projectile / Lightning / armour. Main skill: voltaic grenade.

- Claim: Electrocuted enemies lose armour, so the boss becomes easier to hurt after the grenade setup.
  - support SupportBreachlordsRift: "Break Armour of enemies it Freezes or Electrocutes"
- Claim: The grenade makes all lightning hits build electrocution.
  - skill ShockGrenadePlayer: "contribute to Electrocution buildup for a duration"

| key piece | verdict | worth | replaced by | note |
|---|---|---:|---|---|
| support: Breachlord's Rift | not_load_bearing | -317.4% | Fiery Death | removing it RAISES the metric |

## Across the slate

- Generators represented among screened candidates: llm.
- Ablation: 1 of 11 key pieces confirmed (removal costs at least the configured share of the metric).
