# Off-intent scaling inputs in 1.0 skills

Owner ask (thread, 2026-11-25): "What about all sub mechanics for scaling in new skills (eg block on that shadow skill) -
unconventional scaling different from Clear intention of devs".

Method:
- Every public 1.0 skill page on poe2db was read in full (fetched 2026-11-25), including hidden stats.
- Each skill's main scalar is the one its damage line names. Every other number the skill reads is a secondary input.
- A secondary input is **off-intent** when one of three things holds:
  - it is tuned for a small range, and old content or another 1.0 skill pushes it far past that range
  - it comes from a different system than the skill's damage, such as defence, a resource, or enemy count
  - a "count as" clause turns it on all the time
- Old-game quotes come from the pinned catalogue (`601768b`).

**Everything below is untested.** Multipliers are estimates and probabilities are subjective.

## Answer

1. **Impale count becomes Darkness.** Engulf in Darkness: "Inflicting Impale on an enemy Engulfed in Darkness also
   grants 1 Darkness". The design reads as a trickle of one per hit. Whirling Blades throws 20 knives, plus 1 per
   Darkness when Ambushing, x1.35 when dual wielding, and "Multiple knives can hit the same target". Each knife
   impales.
   - One throw at a boss refills the whole Darkness pool. Eclipse is "Build Glory by gaining Darkness", so the same
     throw also rebuilds Glory.
   - This turns a projectile-count stat into Eclipse uptime.
   - Estimate: Eclipse plus Shades rises from about x2.4 on average to about x4, about x1.7 on the Shadow layer.
     Subjective chance 0.4.
   - With the Acolyte pool from [unlocked-by-1-0.md](unlocked-by-1-0.md) it becomes a closed loop: more Darkness
     means more knives, which means more Darkness.
2. **Eclipse's "count as" clause makes every Ambush mode permanent.** "Attacks count as being used from Stealth and
   expending maximum Darkness."
   - Every other Shadow skill has an Ambush branch tuned as an occasional opener. Under Eclipse each use takes that
     branch.
   - Shadow Assault does the Final Strike on every use instead of every third. Every Final Strike makes a Shade and
     has each Shade repeat a 177% dash.
   - Estimate: about x2-3 on Shadow Assault while Eclipse runs. Subjective chance 0.6.
3. **Ethereal Knives stacks Impales without using them up.** From Stealth it "Does not Hit, but Impales as though
   Hitting" with 125% more magnitude. Under Eclipse it is always in that mode.
   - A skill that does not Hit cannot Extract, so Impales pile up for Blade Vortex and for item 1.
   - The impale limit per enemy decides it.
4. **Block on Duplicity (the owner's example) is a trigger gate, not a damage axis.** At most about x1.1. Section 3
   gives the reasons.

Ranked by expected value, the strongest combination is items 1 to 3 together: Eclipse up most of the time, with
Shadow Assault and Whirling Blades in their Ambush modes all the time. On top of that comes the Shades layer from
earlier passes.
- Estimate: about x8-12 over a normal rare strike on a dagger engine.
- Every link is a guess at one undefined rule (section 5).

## 1. The Darkness economy (items 1 to 3)

| Piece | Quote (poe2db 1.0) |
|---|---|
| Engulf in Darkness | "Explodes, dealing Attack damage if the target dies, or is Immobilised while Engulfed. The explosion leaves behind a Remnant that grants 5 Darkness"; "Impaling an Engulfed enemy also grants 1 Darkness"; lasts 6 s |
| Engulf sources | Blade of Night (on Hit), Duplicity (on trigger), Null Trap (each target hit) |
| Whirling Blades | "Fires 20 projectiles"; "1 additional projectile for each Darkness spent when Ambushing"; "35% more projectiles while Dual Wielding"; "Multiple knives can hit the same target"; "Inflicts Impale on Hit"; 250% more Impale magnitude; +0.6 s added attack time |
| Eclipse | "Build Glory by gaining Darkness"; needs 100 Glory; "Attacks count as being used from Stealth and expending maximum Darkness"; "After the first 4 seconds, drains 6 Darkness per second, increasing by 40% each second" |
| Shrapnel Trap | "Impales 3 times on Hit", 200% more Impale magnitude, 4 uses per 3 s |

### How long Eclipse lasts

The drain after the first 4 s adds up to 17.8 x (1.4^t - 1) Darkness.
- Pool of 30 with no refill: about 7 s.
- Pool of 30, refilled each Whirling throw (about 27 Darkness per second): about 9.5 s. The cap at maximum Darkness
  limits the refill, so it only extends Eclipse a little.
- Pool of 2,050 (Acolyte, if one Darkness stat): about 18 s with no refill. With refill, Eclipse runs until the drain
  is above 1,800 per second, about 21 s.

### Where the gain comes from: Glory

Gaining Darkness builds Glory. One throw on an Engulfed boss gains up to 67 Darkness in impales.
- If the Glory rate is near 1 per Darkness, Eclipse can be recast after two throws once it ends.
- Uptime rises from about 0.4 to about 0.8.
- The earlier model gave x2.4 on average for the Eclipse plus Shades layer. At 0.8 uptime it is about x4.

### Deciders
- Does Glory build while Eclipse is active?
- How much Glory does one Darkness give?
- Does Darkness gained above maximum still count toward Glory?
- Does each knife's Impale count as "inflicting Impale" when the target already has Impales?

### Upkeep
Engulf lasts 6 s, so Blade of Night must hit the boss again every 6 s. Null Trap is the alternative.
Immobilising the boss (Heavy Stun, Freeze) makes Engulf explode, which leaves a 5-Darkness Remnant.

Old Remnant notables may apply to that Remnant, since Engulf is tagged Remnant:
- Remnant Attraction: "10% chance to create an additional Remnant"
- Empowering Remnants: "15% chance for Remnants you create to grant their effects twice"

## 2. Shadow skills under Eclipse (item 2)

| Skill | Ambush branch (quote) | Rate without Eclipse | Under Eclipse |
|---|---|---|---|
| Shadow Assault | "When Ambushing, dash to target and immediately perform the Final Strike" | 1 Final Strike per 3 uses | 1 per use: a Shade each use, every Shade repeats the 177% dash |
| Viper Strike | "Ambushing an enemy Empowers your next 3 Melee Attacks to Trigger Virulent Burst on Hit" | after each Ambush | refreshed every use, so every melee Hit triggers Virulent Burst |
| Whirling Blades | knives per Darkness expended | after Stealth | always 20 + 30 knives (x1.35 dual wield, about 67) |
| Blade of Night | "dash to your target and Hit all enemies within a wide swathe" | after Stealth | always |
| Ethereal Knives | Impale as though Hitting, 125% more magnitude | after Stealth | always |

Stacks with:
- Nightmare: 13 Glory per Shade created. Shadow Assault under Eclipse makes a Shade every use, so Nightmare is ready
  after about eight uses.
- Crescendo: Final Strike twice, as in the census.
- Olroth's Conviction: Viper Strike names a fixed count ("next 3"), so it likely qualifies, which makes it 5.

**Guard seen.** "Counts as being used from Stealth" may not count as *being in* Stealth. Shroud's cooldown reset needs
"not in Stealth". That probably still works under Eclipse.

## 3. Block on Duplicity (owner's example)

| | Quote |
|---|---|
| Duplicity | "Requires: Dagger & Parrying Shield, Dual Daggers"; "Can Block Damage from enemies within 2 metres"; "Can Block Projectile Damage from enemies within 4 metres"; "Avoiding damage in this way causes you to accumulate Heavy Stun buildup, and none of this Skill's other effects will occur if the Hit Heavy Stuns you" |
| Old block payoffs | Doomgate "Enemies are Culled on Block"; Lycosidae "Blocking Damage Poisons the Enemy as though dealing 200 Base Chaos Damage"; Wulfsbane "Permanently Intimidate enemies on Block"; all **tower shields**. Bloodbarrier (Iron Buckler) "Inflict Corrupted Blood for 5 seconds on Block, dealing 50% of your maximum Life as Physical damage per second" |

Reading:
- Block here is a range-limited defensive gate: it decides whether Duplicity fires. It is not a number that
  multiplies damage.
- The best old block payoffs are on tower shields, which Duplicity's Parrying Shield requirement excludes.
- The one buckler payoff, Bloodbarrier, scales with your maximum life, not your weapon. That is truly off-intent, but
  it is a single Corrupted Blood debuff.
- Stun Threshold is an input, but only as a cost. It keeps the Shade and Engulf from being cancelled.
- Remnant notables may add a second Darkness Remnant, as in section 1.

Verdict: at most about x1.1.

## 4. Every 1.0 skill: secondary inputs

Off-intent marks: **yes** (meets the test above), weak (meets it with a small payoff), no.

| Skill | Secondary inputs | Off-intent? | Pushed by |
|---|---|---|---|
| Whirling Blades | Darkness spent; projectiles per target; impales per knife | **yes** | Eclipse (always max); Acolyte pool; impale -> Darkness (section 1) |
| Engulf in Darkness | impales inflicted; immobilise events | **yes** | Whirling Blades, Shrapnel Trap (3 per hit), Ethereal Knives |
| Eclipse | Darkness pool size; Glory per Darkness | **yes** | impale -> Darkness; Acolyte pool |
| Shadow Assault | Shade count; Ambush state | **yes** | Eclipse; Golem Hunger +1 Shade limit |
| Ethereal Knives | Stealth state; impales without Hit | **yes** | Eclipse |
| Blade Vortex | "100% more damage for each additional Impale Extracted"; impale supply (max 50 blades, 5 Hits each); poisoned/spectral/electrified blade variants | weak | Freezing Trap "+1 Impale Extracted" is the only source found; blade count is fed by Whirling Blades and Ethereal Knives. Upside if the 1.0 tree adds "Impales Extracted" |
| Viper Strike | Ambush state; empower count 3 | **yes** | Eclipse; Olroth's Conviction |
| Nightmare | Shades created (13 Glory each) | weak | Shadow Assault under Eclipse |
| Duplicity | block range; Stun Threshold; enemy hit rate | weak | section 3 |
| Volatile Shades | Shade deaths; "Modifiers to Shade Damage also apply" | weak | Shade turnover at the limit (does replacing a Shade count as death?) |
| Shroud | kill resets cooldown "While not in Stealth" | no | the guard holds: Shroud itself enters Stealth |
| Infernal Empowerment | "10% more Fire Damage per 1 Power of exploding Corpse" | weak | unique and rare corpses; packs only, nothing raises corpse Power in old data |
| Raise Zombie | Power Charges consumed | weak | Perpetual Charge; "25% chance when you gain a Power Charge to gain an additional"; capped by limit 10 (+4 quality) |
| Whispers of the Damned | enemy Power in range (cap 50) | no | cap printed |
| Intimidate | enemy Power (1 per 10) | weak | Fangs of Agnar crystals with Vruun's Aftermath (census) |
| Rending Dash | Blood Loss stored on target | weak | covered in the first pass (x3.3 if it re-accumulates, chance 0.1) |
| Perforate, Sand Scour | fixed 0.15 s hit interval, independent of attack speed | weak | on-hit triggers with their own cooldown (Volcanic Eruption 0.4 s); small |
| Tear Through Reality | ignite "as though Hitting" at 974% | weak | Fire Trap 400% more Flammability; Infernalist rework pending |
| Concussive, Fire, Poison Traps | frozen state; Flammability; poison "as though Hitting" | no | as designed for traps |
| Worldcutter | stages (3, 200% more each) | no | no old "maximum Stages" lines |
| Siege of Sands | stages (9) | no | fixed |
| Fangs of Agnar | crystal life 10,118 | no | life is a durability cost; the old "lower Life" support points the other way |
| Engage | 200% more Knockback | no | no old payoff on knockback distance |
| Soul Extraction | Decay on target | no | fixed removal rate; only Decaying Hex makes Decay |
| Fan the Flames | 5 uses per 0.5 s cooldown | no | not weapon-based |
| Blade Plunge | blades (10), channel 4 s | no | fixed caps |

## 5. What decides it, and when to check

At 1.0 (Dec 4 text, or in game):
1. Glory per Darkness gained. Does Glory build during Eclipse? Does gain above the cap count?
2. Does each knife's Impale on an Engulfed target grant Darkness? Is there an Impale limit per enemy?
3. Does the Eclipse Ambush clause trigger other skills' Ambush branches? Test with Shadow Assault: a Final Strike on
   every use.
4. Can Ethereal Knives' Impale "as though Hitting" stack without extracting?

Next step: add a Darkness economy to the sim. The state would be Darkness, Glory, Eclipse, Engulf and Shades, with
switches for deciders 1 and 2. This is a Sonnet-sized build task next to `pos_pipeline/sim_oro.py`.
