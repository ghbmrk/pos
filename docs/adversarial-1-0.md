# Adversarial pass: breaking the 1.0 brakes

Owner ask (thread, 2026-11-25): "Act like this is PvP theorycrafting vs the devs and the goal is to scale beyond what
they intend to allow".

## Method

Earlier passes asked what combines well. This pass asks **where the designers put each brake, and how a player
removes it.**
- Every public 1.0 skill page on poe2db (fetched 2026-11-25) was read for its guards: caps, limits, cooldowns,
  per-target hit limits, "you use yourself", rate limits.
- A guard that appears on one skill but is missing from a sibling that does the same kind of thing is a lead. The
  devs knew the risk and did not close it everywhere.
- A brake priced in one unit while the payoff is priced in another is also a lead, for example a cost paid per use
  against a payoff per strike.
- Old-game quotes come from the pinned catalogue (`601768b`).

**Everything below is untested.** Multipliers are estimates and probabilities are subjective.

## The guards the devs did write (evidence of what they fear)

| Guard (quote) | Where | What it blocks |
|---|---|---|
| "Squall can Hit each target no more than once every 0.66 seconds" | Perfect Squall | many projectiles hitting one target |
| "Number of Projectiles cannot be modified" | Cluster Trap, Perfect Squall | projectile scaling |
| "Supports Strikes you use yourself" | Rending Blade, Impaling Blade II, Vampirism | copies (afterimages, Shades) triggering supports |
| "Lose Life ... at a rate of 10% of maximum Life per second" | Rending Dash (Blood Loss) | burst life loss |
| "counting up to 50 Power"; "up to the first 5 enemies Hit" | Whispers, Intimidate | Power and pack scaling |
| "A maximum of 5 Blades can affect each target" | Galvanising Blades | stacking |
| "damageable Minion" | Abyssal Pact | immortal minions as infinite fuel |
| Limits: 10 zombies, 12 Foul Eyes, 50 blades, 3 Shades, 9 stages, 3 stages | various | count scaling |

## Brakes that can be broken, ranked by ceiling

### 1. Infernal Step: the cost is per use, the payoff is per strike

**The brake.** "When you use this Skill, gain 1 Sacrificial Flame then take 400 Fire Damage per Sacrificial Flame."
Self-damage is clearly meant to cap how high the flame count F goes.

**The break.** One use makes 2 + 3F strikes, so the cost per strike stays flat while the payoff per strike grows with
F²:

| F | Strikes per use | Multiplier per strike (Infernal Step x Oro's) | Self-damage per strike |
|---|---|---|---|
| 10 | 32 | x5.5 | 125 |
| 30 | 92 | x25 | 130 |
| 60 | 182 | x82 | 132 |

Self-damage per second is therefore about constant, near 130 fire per strike before mitigation. Max fire resistance,
fire taken as cold and Recoup erase it.
- The brake does not bind at all.
- The only real limit is whatever "Sacrificial Flame" does that poe2db does not define yet: a cap or decay.
- If neither exists, damage per strike grows without bound with play time. Echoing afterimages copy every strike, so
  bodies multiply on top.

Subjective chance there is no hard cap low enough to matter (below about 30): 0.3. This is still the highest-ceiling
engine in the 1.0 text.

### 2. Whispers of the Damned: an uncapped transfer of life loss that skips boss mitigation

**The guard that is missing.** Rending Dash rate-limits life loss to 10% of maximum life per second. Whispers prints no
rate, no link limit, and no guard against overkill: "Chaos damage dealt to one linked target causes every other linked
targets to Lose Life equal to the Chaos damage dealt."

**The break.**
- Life loss is not damage, so the boss's resistances, armour and damage reduction do not apply to it.
- Hit the weakest linked add, cursed and exposed, and the boss loses whatever you dealt to that add.
- If "damage dealt" includes overkill, as it does for leech, every add you one-shot passes the full hit to the boss.
- Old item that turns ignite into chaos: Blackflame (ring), "Ignite you inflict deals Chaos Damage instead of Fire
  Damage". Paired with it, Tear Through Reality ("Ignites targets as though Hitting them", 974%) and Oro's Sacrificial
  ignite pass across the link as well.

**Limit.** The boss needs other enemies in the 6 m curse radius. Breach and add-phase bosses: x (1 + adds x add
damage share). A lone boss: x1.

Subjective chance it works as worded: 0.5.

### 3. Monster life as base damage: Abyssal Pact and Bunkerbuster on a unique tamed beast

**The brake.** "Sacrifices 19% of a damageable Minion's maximum life to deal that much Physical damage" (0.7 s cast,
0 cost, no cooldown). Bunkerbuster: "Fire Damage equal to 12.2% of the Minion maximum Life". The brake is the
minion's own life pool and its recovery.

**The break.** Base damage is normally tuned in the tens to hundreds. Here it is a monster's life, which is tuned
against player damage. Then, if it is like other spells, every player spell multiplier and crit apply on top.
- The old Spirit Walker notable The Natural Order: "Tame Beast can capture Unique Beasts"; "Can have up to one Unique
  Tamed Beast summoned". Tamed beasts are Reviving companions.
- Fuel rate = minion life recovered per second: "Minions Regenerate 3% of maximum Life per second" plus one full bar
  per revive.
- Demon Magus can cast the Pact for you (socketed spell, 50% less cost), gaining "15% more per different socketed
  Skill".

**Deciders:**
- the life of a tamed unique beast as a minion
- whether Pact damage takes player spell modifiers
- whether the Pact refuses at low minion life

Subjective chance 0.25. Ceiling about x10-50 over a normal spell if the beast keeps monster-scale life.

### 4. "Count as" Darkness that is never spent

**The brake.** Ambush expends your Darkness. Eclipse drains at an accelerating rate.

**The break.**
- Eclipse: "Attacks count as being used from Stealth and expending maximum Darkness." Nothing is actually spent.
- Whirling Blades: "1 additional projectile for each Darkness spent when Ambushing". Every throw under Eclipse gets the
  full pool as knives. Whirling has no per-target guard of the kind Perfect Squall and Cluster Trap carry.
- Detonate: "all of the detonations count as Ambushing, and gain damage from your Darkness". One pool is applied to
  every trap at once. Contingency Plan refreshes every trap cooldown.
- Grim Bargain: "Skills that consume Darkness count as consuming 10% increased amount" adds to the count again.

**Effect.** Whirling knives per throw = (20 + max Darkness) x 1.35, each with x(1 + 0.03 x max Darkness). That is
quadratic in max Darkness. Max Darkness is the stat the devs tuned at 30 and the Acolyte pool may put at about 2,000.
Separately, each knife's Impale on an Engulfed target refunds 1 Darkness, which also builds Glory for the next Eclipse
(see [off-intent-scaling-1-0.md](off-intent-scaling-1-0.md)).

Subjective chance: 0.5 at 30 Darkness, about x2-3 on the Shadow kit. About 0.1 that the Acolyte pool counts, for x60
or more per hit.

### 5. Copies that the "you use yourself" guard does not cover

The devs put "you use yourself" on supports, but not on the skills that make the copies. Echoing afterimages "use that
same Strike", and Shades "perform" Ambushing melee attacks.
- If an afterimage's Infernal Step counts as a use, it adds Sacrificial Flame. The flame count would then rise by 1 +
  afterimages per cast, not 1.
- If afterimage uses made under Eclipse count as Ambushing, Shades copy afterimages: bodies = (1 + 0.5a)(1 + 0.5s).

Subjective chance 0.15-0.25 each. Both multiply break 1.

## Checked: the guard holds

| Idea | Guard |
|---|---|
| Perfect Squall chain through Whirlwinds | per-target 0.66 s hit limit |
| Intimidate cooldown bypass by Endurance Charge, infinite shockwaves | 5 enemies per attack; shockwave is small |
| Raise Zombie from Power Charges | limit 10 (+4) |
| Lightless Stalker Foul Eyes per enemy Power | limit 12 |
| Shroud kill resets chained by Volatile Shades | reset needs "not in Stealth" and Shroud enters Stealth |
| Rending Dash Blood Loss | rate capped at 10% of life per second |
| Rending Blade, Impaling Blade II, Vampirism on copies | "you use yourself" |

## What decides it (Dec 4 text, then in game)

1. Sacrificial Flame: is there a cap, decay or duration? This decides break 1.
2. Does Whispers transfer overkill, and is it rate-limited?
3. Tamed unique beast life as a minion; does Abyssal Pact take spell modifiers?
4. Does "count as expending" Darkness feed "for each Darkness spent"? Does the Acolyte pool share the stat?
5. Does an afterimage's use of Infernal Step add a Sacrificial Flame?

**The strongest combination if breaks 1 and 5 hold:** Infernal Step with flames gained per afterimage. Damage per
strike grows with F², F rises several times faster, and every afterimage copies every strike. The text sets no upper
bound. That is the single place where public 1.0 text, read adversarially, has no visible brake at all.
