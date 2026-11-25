# Most powerful unplanned 1.0 interaction: first-principles pass

Owner ask: cmsg_01RxGYnd78N9kMbbAJ5pWDhUTdnK1sP6Ww46M5phTBbftZ ("start again from fresh slate ... first principles goal
to find most powerful unplanned interaction post 1.0"). Criteria from project memory: strong DPS = many multiplicative
buckets on one quantity that itself scales high; novelty = interactions the devs did not plan.

Prior picks are used only as the baseline to beat: Oro's Infernal Step x Echoing Strikes
([novel-1-0-interactions.md](novel-1-0-interactions.md), simulated in [sim-oro-infernal-step.md](sim-oro-infernal-step.md):
weighted mean x15, median x6.6 over a normal strike on a good rare, 180 s boss).

**Everything below is untested.** 1.0 is not in PoB. "Fact" lines are poe2db 1.0 tooltip text fetched 2026-11-25.
Multipliers are estimates; probabilities are subjective and labelled as such.

## Answer

1. **No mechanism in the public 1.0 text beats the baseline on its own** by probability-weighted estimate. The best
   independent fresh candidate ("endless use", section 3.2) has a similar ceiling (about x20) but a lower expected value
   (about x9), because its key rule is the one the devs visibly guard.
2. **The highest-ceiling unplanned interaction found is the copy chain** (section 3.1): Echoing Strikes afterimages and
   Shades come from two different classes, and neither rule checks whether its source is already a copy. If an
   afterimage's use counts as your Ambushing melee attack, body count becomes a product, (1+0.5a)(1+0.5s), instead of
   a sum. On the baseline engine that is about x2.5 more when it holds (x40-60 over a rare in the good cases), x1.25 if
   Shades copy only you. Subjective probability that the chain holds: about 0.25.
3. **The decision boundary is three 1.0 tests**, in priority order (section 5). Until they run, the ranking is a
   ranking of bets, not of builds.
4. **The main unmined source is still the ascendancy text** (Assassin, Infiltrator, reworked Infernalist, Blood Mage,
   Acolyte, Mercenary; expected around Dec 4), plus the undefined keywords Sacrificial Flame, Leviathan Scales,
   Sand-Ingrained, Vampiric Boost and Chaos Incarnate. poe2db has no definition pages for them yet.

## 1. Model

Damage per second = base per hit x hits per second x product of multipliers. A build goes very high only when one
quantity (the scalar) can be pushed far and several independent multiplicative buckets are keyed to it. Additive
stacking of many small sources does not get there.

A designed system is normally bounded by the designer at its own scale: a cooldown, a cap, a duration, a "you use
yourself" clause. Unplanned power comes from a **gap between two rules written for different systems**, where one
rule's unit of accounting is made arbitrarily large by the other. Five gap types, each searched against the corpus:

| Gap type | What gets large | Dev guards seen in 1.0 text (evidence the devs think about this gap) |
|---|---|---|
| A. Per-use pricing on a use of unbounded length | One "use" of a Strike | Cyclone: "Blood and Sand enhancements last 8 seconds"; Echoing Strikes: "Empower duration is 10 seconds" |
| B. Copies that do not check whether the source is a copy | Number of bodies performing one use | Vampirism, Rending Blade, Impaling Blade: "Strikes you use yourself"; Gouge: "Attacks you use yourself"; Ancestral Boost: "Triggered Skills cannot be Ancestrally Boosted" |
| C. "Counts as maximum" reading a pool scaled for another purpose | The pool | Eclipse "expending maximum Darkness" (excluded: owner judged Darkness/Eclipse as designed) |
| D. An accumulator whose payoff feeds itself | Accumulated total | None seen for Blood Loss |
| E. Hit-triggered objects | Hits per second on the object | Tempest Bell "destroyed after 10 Hits" (Ako's Answer lifts it on purpose, 0.x item) |

The guard column matters: types A and B are exactly where the devs write limits, so a candidate in those types needs a
test before it counts. Type D has no visible guard.

## 2. Corpus

- poe2db "Conquerors of Wraeclast" lists: 65 gems, 16 uniques (`/us/Conquerors_of_Wraeclast_gems`, `_uniques`).
- Skill pages: Infernal Step, Echoing Strikes, Cyclone, Siege of Sands, Tear Through Reality, Fangs of Agnar, Demon
  Magus, Abyssal Pact, Lightless Stalker, Bunkerbuster, Perfect Squall, Raise Zombie, Tempest Bell, Molten Forge,
  Soul Extraction, Haemorrhage.
- Keyword pages: Ancestral Boost, Blood Loss, Decay, Rally (support). Knight page.
- Secondary: poe2db `Version_1.0.0` interview digest (dev statements: crit nerfed, Gemling/Martial Artist strength
  "wasn't intended", Squire "risky, fixes in 1.1", bleed support removed, one gas cloud per monster).

## 3. Ranked candidates

### 3.1 Copy chain: afterimages that trigger Shades (gap B on top of gap A)

**Facts.**
- Echoing Strikes: "Empower your next Strike to create afterimages that use that same Strike in additional locations";
  "Creates 2 afterimages and 1 additional afterimage per Frenzy Charge Consumed"; "50% less damage with Afterimages".
- Shade (poe2db Shade page, project memory): Ambushing with a Melee Attack makes Shades perform it; Shade portion deals
  50% less damage and is dealt by you; limit 3 (4 with Golem Hunger); 6 s duration.
- Eclipse: "Attacks count as being used from Stealth and expending maximum Darkness"; "Shades' durations are paused".
- Shades are made by dagger skills (Shroud, Shadow Assault, Duplicity); weapon swap is allowed, and a dev said traps
  are "made for the weapon swap".

**Interaction.** Under Eclipse every attack you make is an Ambush. If an afterimage's "use" of the Strike is one of
your attacks, each afterimage use is itself an Ambushing melee attack, and every Shade performs it. Copies then
multiply instead of adding:

| Bodies per use | a = 7 afterimages (5 Frenzy), s = 3 Shades | a = 10 (8 Frenzy), s = 3 |
|---|---|---|
| Sum (Shades copy only you): 1 + 0.5a + 0.5s | x6.0 | x7.5 |
| Product (chain holds): (1 + 0.5a)(1 + 0.5s) | x11.25 | x15.0 |

**Scalar and buckets.** The scalar is one Strike use. On Infernal Step it carries the baseline's buckets (strike count
2+3F, 15% more per flame, Oro's 12% extra fire per flame) and adds two more: afterimage count and Shade count, now
multiplicative with each other. That is five buckets on one use.

**Estimate.** The simulated baseline has no Shades. The chain adds x2.5 (x3 with 4 Shades) to it when it holds, x1.25
when Shades copy only you, x1.0 if Shades cannot be held across a weapon swap. With subjective weights 0.25 / 0.60 /
0.15 the expected gain is about x1.5, which lifts the baseline's weighted mean from about x15 to about x23 (estimate).

**Why it counts as unplanned.** The two copy systems belong to different classes (Duelist sword spell, Shadow dagger
mechanic) and each is written against a general rule ("that same Strike", "a Melee Attack"). Neither text mentions the
other.

**Why the probability is low.** The guard column above: the devs consistently restrict copies and supports with "you
use yourself", and afterimage uses may be flagged the same way.

### 3.2 Endless use: per-use empowerments on a channelled Strike (gap A, carrier-independent)

**Facts.**
- Cyclone: Strike, Sustained, Channelling; 330% attack speed, 78% attack damage; "Cannot be Knocked Back while
  Channelling"; cost per second.
- Per-use empowerments available to any Strike: Echoing Strikes (afterimages), Whispers of the Damned ("Empowered
  Attacks gain 42% of their damage as extra Chaos damage", 1 attack per 10 Power, dagger), Intimidate ("Empowering
  subsequent Melee Attacks to Trigger a damaging shockwave on Hit"), Knight minor ("Empowered Attacks deal 20%
  increased damage"), Infernal Empowerment (combust on kill), Overchannel (15% more after 1.5 s channelling).

**Interaction.** If one channel is one "use", an empowerment consumed at the start lasts as long as you keep
channelling. Every burst multiplier becomes permanent, with no ramp, no self-damage and no long cast lock: you can stop
to dodge at any moment and re-empower on the next cooldown.

**Estimate.** Raw Cyclone 0.78 x 3.3 = x2.6 a normal strike. Afterimages x3.8 (x4.5 discounted for overlap on a single
target), Whispers x1.42, Intimidate x1.3 (shockwave damage unpublished, a guess), Knight x1.1, Overchannel x1.15: about
x23, about x20 at 85% uptime with a dodge every 15 s. If the empowerment is consumed on the first hit, about x3.
Subjective probability that it persists: 0.35. Expected value about x9; median about x3.

**Why it is ranked below 3.1.** Cyclone's own text caps its stance enhancements at 8 s, and Echoing states a 10 s empower
duration. Both read like the devs anticipating exactly this gap. It is the better build if the baseline's ramp and
cast-lock problems (sim findings 1 and 3) prove fatal, and the copy chain applies to it too.

### 3.3 Abyssal Pact cast by the Demon Magus (minion life as base, minion damage as multiplier)

**Facts.**
- Abyssal Pact: 0.70 s cast, 0 Mana, no cooldown; "Sacrifices 19% of a damageable Minion's maximum life to deal that
  much Physical damage".
- Demon Magus (Infernalist rework): "casts socketed Spells in order"; "Cost of Spells cast by Minion are paid by you";
  "Minion deals 15% more Damage per different socketed Skill" (hidden stat: 20% per linked active skill).
- Hand of Weeping Black: Raise Zombie consumes no Corpse or Power Charge; Raised Zombies "always empowered" and
  "infinite Duration". Siegebreaker: minions 25% increased life, 1.2% regeneration per second.

**Interaction.** The Pact's base damage is keyed to minion maximum life, not to the caster's level. When the Magus casts
it, minion damage modifiers also apply. One investment axis (minion nodes) then feeds two buckets on the same hit:
life raises the base, damage raises the multiplier. Free zombies are reusable ammunition.

**Score.** Two linear buckets, not a compounding scalar. Minion life is a designed fuel for Abyssal Pact (it is printed
beside it on The Watcher in the Dark). Useful as a second damage stream for a minion build; not a ceiling-raiser.
Tests: can the Magus cast Abyssal Pact and whom it targets; does Pact damage use the caster's modifiers.

### 3.4 Blood Loss feedback (gap D, low probability, high payoff if real)

**Facts.**
- Blood Loss: "All Physical damage over time taken by a target (including Bleeding) is accumulated as Blood Loss."
- Rending Dash (4.5 s cooldown): "Consumes the target's Blood Loss to cause it to Lose Life equal to 70% of consumed
  Blood Loss at a rate of 10% of maximum Life per second".

**Interaction.** Blood Loss is an uncapped running total on the target. Rending Dash re-deals 70% of it. If that life
loss itself counts as physical damage over time taken, it re-accumulates, and the series sums to 1/(1-0.7) = x3.3 on
all physical DoT. If not, it is a designed x1.7.

**Score.** Life loss is usually not "damage", so the loop probably does not exist (subjective 0.1). One test settles
it: consume, wait, and check whether Blood Loss grows while the life loss ticks with no bleed active.

### 3.5 Copies hitting the Molten Forge anvil (gap E, test only)

**Facts.** "Striking the Anvil creates a damaging shockwave"; Ignited anvil shockwaves have more area and extra fire.
No hit limit is printed (Tempest Bell prints one: 10 hits).

**Interaction.** If every body's hit on the anvil makes a shockwave, shockwave rate = hits per second x bodies, so a
Cyclone with afterimages next to the anvil turns hit rate into extra hits on the boss. Shockwave damage is unpublished;
the bell precedent suggests a cap. Test: shockwaves per second against hit rate and body count.

## 4. Checked and rejected

| Idea | Why rejected |
|---|---|
| Siege of Sands (Elysium): up to 9 stages of Sand Mirages at 974% each | Large designed burst on a 5 s cooldown; tagged Melee/Channelling/Staged, not Strike, so no Echoing. Shades copying it is the same bet as 3.1 |
| Tear Through Reality (Benevolence): "Does not Hit, but Ignites targets as though Hitting them" at 974% | Printed on one item with 212% ignite magnitude and Chaos Incarnate, so designed; Chaos Incarnate text unpublished |
| Hand of Weeping Black self-damage (20% of life plus ES per Raise) as a trigger | No 1.0 effect found that turns damage taken into offence |
| Whispers of the Damned life-loss link | Zero on a lone boss; clear only |
| Soul Extraction | Removes Decay at the same rate it adds damage (334.5 per second each): a conversion, not a multiplier |
| Redblade double Power | Power is fixed (unique = 20); breadth, not height |
| Ako's Answer uncapped bells | 0.x item and printed on purpose |
| The Leviathan scales, Elysium Sand-Ingrained | Keywords undefined on poe2db; re-check when defined |
| Darkness, Shades-as-scalar, Eclipse max Darkness | Owner judged as designed; Shades appear above only as a copy count |

## 5. Comparison and tests

| Candidate | Ceiling (x normal rare strike) | Expected (subjective) | Floor | Survival profile |
|---|---|---|---|---|
| Baseline: Infernal Step x Echoing (sim) | x40-115 pre-ramped | x15 mean, x6.6 median | x1.9 | 10-15 s cast lock, 90 s ramp |
| 3.1 Copy chain on the baseline | about x2.5 x baseline | about x23 mean | baseline | Adds a dagger swap and Shade setup |
| 3.2 Endless use (Cyclone) | about x20 | about x9 mean, x3 median | x2.6 | No ramp, stop any time, no knockback |
| 3.3 Magus Abyssal Pact | second stream, linear | n/a | n/a | Minion screen |

Tests, in priority order (all at 1.0):
1. With Eclipse active and Shades held, use an Echoing-empowered Strike: do Shades perform each afterimage's use, or
   only yours? (Decides 3.1.)
2. Start an Echoing-empowered Cyclone and channel for 20 s: do afterimages persist past 10 s? Does Whispers' extra
   chaos persist? (Decides 3.2.)
3. Do the baseline's own deciders still hold: afterimages replay the full Infernal Step sequence, and the Sacrificial
   Flame cap.

Recommendation: keep the Infernal Step engine as the 1.0 test target and add test 1 to the same session, since it
reuses the same setup. Re-run this search when the ascendancy and keyword text appears (the Dec 4 reminder already
exists).
