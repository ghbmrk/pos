# Slate report

- Prompt: Cyclone that builds up charges and dumps them with Elemental Discharge
- Benchmarks: arbiter_ash, breach_t15. Brief tiers: mid. Screen tier: `mid`. Deepened: top 0.
- Preflight estimate: 8 candidate(s) screened, top 0 deepened: ~23.6 min wall (screen 20.5 min, ablation 3.1 min, deepen 0.0 min); cap 45 min
- successive halving: top 0 of 7 by screen rank deepened; the rest keep their screen numbers
- ranking basis: benchmark metrics only (boss time-to-kill with its survival check, pack clear proxy); a candidate missing a benchmark value ranks after those that have it. Per-skill DPS is shown but never ranks across archetypes.
- ablation measures the objective metric under the first benchmark's PoB options, not time-to-kill, and also TotalEHP: a piece is confirmed when removal costs either at least the threshold; a unique key piece is replaced by the best rare for its slot at the screen tier.
- Numbers are PoB outputs or benchmark formulas over them (`proxy` = density proxy, `ASSUMPTION` = owner-tunable constant). Mechanism claims are quoted from catalogue text; ablation tests whether they matter.

## Screen ranking

| # | candidate | source | archetype | arbiter_ash | breach_t15 | price | key pieces (ablation) | deepened |
|---|---|---|---|---|---|---|---|---|
| 1 | Infusion Orb Stormweaver | llm | stormweaver / projectile / Lightning / energy_shield | TTK 181.2s FAIL; DIES; EHP 1,636 | clear 11035.2 proxy-s FAIL; coverage 4% | no price: missing anchors weapon:mid, body_armour:budget | Refracted Infusion: possibly_unmodelled, Everlasting Infusions: possibly_unmodelled | no |
| 2 | Rainfall Deadeye | llm | deadeye / attack / unknown / evasion | TTK 874.6s FAIL; DIES; EHP 1,188 | clear 1041.7 proxy-s FAIL; coverage 36% | no price: missing anchors weapon:mid, body_armour:budget | Thrilling Chase: possibly_unmodelled, Avidity: possibly_unmodelled | no |
| 3 | Aftershock Titan | llm | titan / channel / unknown / armour | TTK 1247.3s FAIL; DIES; EHP 1,216 | clear 1674.1 proxy-s FAIL; coverage 7% | no price: missing anchors weapon:mid, body_armour:budget | Earthbreaker: possibly_unmodelled, Burgeon II: not_load_bearing | no |
| 4 | Charged Blast Chrono | llm | chronomancer / channel / Fire / energy_shield | TTK 92.2s FAIL; survives; EHP 2,433 | clear n/a | no price: missing anchors weapon:mid, body_armour:budget | Burgeon II: not_load_bearing, Phased Form: confirmed | no |
| 5 | Storm Teleport Monk | llm | invoker / melee / unknown / energy_shield | TTK 606.0s FAIL; DIES; EHP 1,334 | clear n/a | no price: missing anchors weapon:mid, body_armour:budget | One with the Storm: possibly_unmodelled, Overflowing Power: possibly_unmodelled | no |
| 6 | Bell Combo Artist | llm | martial artist / melee / unknown / energy_shield | TTK 3788.0s FAIL; DIES; EHP 1,201 | clear n/a | no price: missing anchors weapon:mid, body_armour:budget | Martial Master: possibly_unmodelled, Martial Adept: not_load_bearing | no |
| 7 | Combo Whirl Amazon | llm | amazon / melee / unknown / evasion | TTK 6427.8s FAIL; DIES; EHP 1,249 | clear n/a | no price: missing anchors weapon:mid, body_armour:budget | Culmination II: not_load_bearing, Predatory Instinct: possibly_unmodelled | no |

- Rainfall Deadeye: survival check FAILED on arbiter_ash
- Combo Whirl Amazon: no value for breach_t15; survival check FAILED on arbiter_ash
- Storm Teleport Monk: no value for breach_t15; survival check FAILED on arbiter_ash
- Bell Combo Artist: no value for breach_t15; survival check FAILED on arbiter_ash
- Infusion Orb Stormweaver: survival check FAILED on arbiter_ash
- Aftershock Titan: survival check FAILED on arbiter_ash
- Charged Blast Chrono: no value for breach_t15

## Candidates

### Infusion Orb Stormweaver

Source: `llm`. Archetype: stormweaver / projectile / Lightning / energy_shield. Main skill: ball lightning.

- Claim: The projectile consumes a Fire Infusion if possible to upgrade its behaviour.
  - skill Ball Lightning: "Consumes a Fire Infusion if possible"
- Claim: Collecting an infusion grants a different type, and a passive lets some infusions survive consumption.
  - notable Refracted Infusion: "When collecting an Elemental Infusion, gain another different Elemental Infusion"
  - notable Everlasting Infusions: "Skills have 10% chance to not remove Elemental Infusions but still count as consuming them"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Refracted Infusion | possibly_unmodelled | +0.0% | +0.0% |  |  |
| notable: Everlasting Infusions | possibly_unmodelled | +0.0% | +0.0% |  |  |

### Rainfall Deadeye

Source: `llm`. Archetype: deadeye / attack / unknown / evasion. Main skill: rain of arrows.
Measured under declared conditions (assumed, not earned by the build): frenzy_charges (Frenzy Charges at maximum; needs a way to gain Frenzy Charges).

- Claim: The area bow skill uses a Frenzy Charge to fire more arrows, and the Deadeye notable can double that benefit.
  - skill Rain of Arrows: "Consumes a Frenzy Charge to fire more arrows."
  - notable Thrilling Chase: "Benefits from consuming Frenzy Charges for your Skills have 50% chance to be doubled"
- Claim: Another Deadeye notable makes charge gain generous so the consumption never starves.
  - notable Avidity: "chance when you gain a Frenzy Charge to gain an additional Frenzy Charge"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Thrilling Chase | possibly_unmodelled | +0.0% | +0.0% |  |  |
| notable: Avidity | possibly_unmodelled | +0.0% | +0.0% |  |  |

### Aftershock Titan

Source: `llm`. Archetype: titan / channel / unknown / armour. Main skill: supercharged slam.

- Claim: Longer channelling raises damage, and the slam is followed by larger aftershocks.
  - support Burgeon II: "causing them to deal more damage the longer they have been Channelled."
  - skill Supercharged Slam: "followed by Aftershocks dealing damage in a larger area"
- Claim: The Titan notable adds a chance for another aftershock on slam skills.
  - notable Earthbreaker: "chance for Slam Skills you use yourself to cause an additional Aftershock"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Earthbreaker | possibly_unmodelled | +0.0% | +0.0% |  |  |
| support: Burgeon II | not_load_bearing | -30.5% | +0.0% | Concentrated Area | removing it RAISES the metric |

### Charged Blast Chrono

Source: `llm`. Archetype: chronomancer / channel / Fire / energy_shield. Main skill: flameblast.

- Claim: The explosion grows with channel time and the support multiplies damage by channel length.
  - skill Flameblast: "Releasing the energy causes a devastating explosion that is larger and more intense the longer you Channel for."
  - support Burgeon II: "causing them to deal more damage the longer they have been Channelled."
- Claim: The Chronomancer notable cuts damage taken, a defensive layer for a stationary channel.
  - notable Phased Form: "Take 30% less Damage"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| support: Burgeon II | not_load_bearing | -22.1% | +0.0% | Deliberation | removing it RAISES the metric |
| notable: Phased Form | confirmed | +0.0% | +30.0% |  | confirmed on survivability: removal costs 30% of EHP (damage metric moves +0.0%) |

### Storm Teleport Monk

Source: `llm`. Archetype: invoker / melee / unknown / energy_shield. Main skill: flicker strike.
Measured under declared conditions (assumed, not earned by the build): power_charges (Power Charges at maximum; needs a way to gain Power Charges).

- Claim: Each Power Charge spent adds a further teleporting strike, and the staff notable counts an extra spent charge.
  - skill Flicker Strike: "Consumes Power Charges to perform additional teleporting Strikes on nearby enemies."
  - notable One with the Storm: "Quarterstaff Skills that consume Power Charges count as consuming an additional Power Charge"
- Claim: A larger charge pool means longer chains per dump.
  - notable Overflowing Power: "+2 to Maximum Power Charges"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: One with the Storm | possibly_unmodelled | +0.0% | +0.0% |  |  |
| notable: Overflowing Power | possibly_unmodelled | +0.0% | +0.0% |  |  |

### Bell Combo Artist

Source: `llm`. Archetype: martial artist / melee / unknown / energy_shield. Main skill: tempest bell.

- Claim: The bell skill is a delayed dump of Combo built by other strikes.
  - skill Tempest Bell: "Build Combo by successfully Striking Enemies with other skills."
- Claim: Martial Artist notables speed up Combo gain from all attack hits.
  - notable Martial Master: "Gain Combo from all Attack Hits"
  - notable Martial Adept: "When you gain Combo, gain an additional Combo"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| notable: Martial Master | possibly_unmodelled | +0.0% | +0.0% |  |  |
| notable: Martial Adept | not_load_bearing | +3.7% | +0.0% |  |  |

### Combo Whirl Amazon

Source: `llm`. Archetype: amazon / melee / unknown / evasion. Main skill: whirling slash.

- Claim: The whirlwind skill is the literal spin; the support turns it into a build up and release skill.
  - skill Whirling Slash: "Perform a circular slash that kicks up a Whirlwind around you"
  - support Culmination II: "Supported Skills reset their Combo on use, dealing more Damage the higher Combo you had on use."
- Claim: The Amazon notable adds a damage multiplier against weakened rares and bosses.
  - notable Predatory Instinct: "50% more damage against enemies with an Open Weakness"

| key piece | verdict | worth (damage) | worth (EHP) | replaced by | note |
|---|---|---:|---:|---|---|
| support: Culmination II | not_load_bearing | -40.4% | +0.0% | Hit and Run | removing it RAISES the metric |
| notable: Predatory Instinct | possibly_unmodelled | +0.0% | +0.0% |  |  |

### Serpent Surge Amazon

Screen FAILED: assemble failed: could not allocate Prize of the Hunt: node not reachable from current tree; Prize of the Hunt not allocated after build

## Across the slate

- Generators represented among screened candidates: llm.
- Ablation: 1 of 14 key pieces confirmed (removal costs at least the configured share of the metric).
