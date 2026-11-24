# Novel 1.0 build interactions (fresh pass)

Owner asks: cmsg_01RxGYnd78N9kMbbAJ5pWDhULuc2GJKp1KSZt3Y9ct6ygD (start fresh, maximally novel and powerful, unlocked
by 1.0), with the criteria in cmsg_01RxGYnd78N9kMbbAJ5pWDhUByrc4DczUo7dd2iiDhjN9P (novel = interactions the devs did
not plan for) and cmsg_01RxGYnd78N9kMbbAJ5pWDhUTGh3kC6JhvyMRVoGC7JEDZ (many multiplicative buckets on one quantity that
itself scales high). Everything here is **untested**; no figure below came from PoB (1.0 is not in PoB yet).

## Method

1. Corpus: poe2db's "Version 1.0.0" lists (`/us/Conquerors_of_Wraeclast_gems`, `_uniques`, the changed-unique list on
   the home page), each linked skill page, and the Knight page. Fetched 2026-11-24. Secondary sources (aoeah, expcarry,
   nextlevelguides) only where poe2db has nothing; marked "secondary".
2. Novelty filter: a combination counts only if its pieces come from different themes (item, class, skill family) and
   it relies on a general rule ("next Strike", "per enemy Power", "a damageable Minion") rather than a stated synergy.
   Pieces printed on the same item or skill are treated as designed.
3. Power filter: name the scalar, count the multiplicative buckets that act on it, and say how high the scalar goes.
4. Ruled out up front: Darkness, Shades, Eclipse, Stealth bank, Rage-Darkness bar (prior thread; owner judged as
   designed).

Not public yet: Assassin, Infiltrator and reworked ascendancy node text, new keystone text (Chaos Incarnate, Withering
Disintegration), and definitions of Sacrificial Flame, Vampiric Boost, Reaper's Touch, Redblade Ferocity. The ranking
below should be redone when those appear (the 2026-12-12 repin reminder already exists).

## Ranked candidates

### 1. Infernal Step: a single 10-second "use" that every per-use empowerment applies to

**Facts (poe2db, 1.0):**
- Oro's Sacrifice (2H sword, new) grants Infernal Step. It also has "Gain 12% of Damage as Extra Fire Damage per
  Sacrificial Flame" and "Gain 1 Frenzy Charge every 1 second while at maximum Sacrificial Flame".
- Infernal Step (Strike, 49% attack speed): "When you use this Skill, gain 1 Sacrificial Flame then take 400 Fire
  Damage per Sacrificial Flame". It has "15% more Damage per Sacrificial Flame" and "Teleports and Strikes 2 times,
  plus 3 additional times per Sacrificial Flame". "Additional Strikes have 113% more Attack speed".
- Echoing Strikes (sword spell, 12.8 s cooldown) consumes Frenzy Charges to "Empower your next Strike to create
  afterimages that use that same Strike in additional locations". It makes 2 afterimages plus 1 per Frenzy Charge,
  each with 50% less damage.
- Knight minor: "Empowered Attacks deal 20% increased damage". Whispers of the Damned "Empowers 1 Attack for every 10
  Power" (+42% of damage as extra chaos). Ancestral Boost counts as Empowered. Overchannel empowers the next
  non-channelling skill.

**Interaction.** Echoing Strikes and the other empowerments are priced per *use*: one empowered Strike every 12.8 s
reads as a burst. At F flames, one Infernal Step use is 2+3F strikes. At F=10 that is 32 strikes, about 15.6
base-strike times, which is roughly 10 to 20 s at plausible attack speed. So one empowerment covers the whole sequence,
and Echoing Strikes' cooldown is about as long as the use. The burst skill becomes a near-permanent copy multiplier. The
self-damage is also charged per use (400F once per 10+ s), so the cost grows linearly in F while the benefit grows
faster.

**Scalar F (Sacrificial Flames).** These buckets act on it:

| Bucket | Per use | Per second |
|---|---|---|
| Strike count 2+3F | linear | cancels (use gets longer) |
| 15% more per flame | 1+0.15F | 1+0.15F |
| Oro's 12% extra fire per flame | 1+0.12F | 1+0.12F |
| Frenzy at max F leads to afterimages | 1+0.5(2+charges) | same, if Echoing uptime is about 100% |
| Per-use empowerments (Knight +20%, Whispers extra chaos) | ×1 on the whole sequence | same |

Estimates, not measured:
- Per-strike multiplier vs F=0: F=5 gives ×2.8, F=10 ×5.5, F=20 ×13.6.
- Echoing Strikes adds ×3.5 with 3 Frenzy and ×4.5 with 5.
- At F=10 with 5 Frenzy that is about ×25 over the unstacked skill, before generic scaling.
- Per-use burst is cubic: ×88 at F=10.

**What makes it unplanned.** Echoing Strikes and the Infernal Step stack each make sense alone. Their per-use
accounting multiplies across a use that the stack makes about 15× longer. Oro's Frenzy output also feeds the
afterimage count, and nothing on either item points at the other.

**Risks and unknowns (tests at 1.0):**
- Maximum Sacrificial Flame and its decay. If flames expire faster than one long use, the engine stalls. The cap sets
  the whole ceiling.
- Whether afterimages repeat the full 2+3F sequence or one strike.
- Whether an afterimage "use" also adds flames and self-damage.
- Whether the sequence can be cancelled. Being locked in teleports for about 10 s against an uber slam is the main
  survival risk.
- Whether the self-damage is reduced by fire resistance or armour, and whether MoM/Eldritch Battery can absorb it.
  Molten Tenet (new belt) lets armour apply to fire and recoups 10% of prevented fire damage as life.

### 2. Double Power as a shared input (Redblade Banner) feeding new 1.0 Power consumers

**Facts.**
- Redblade Banner (changed in 1.0): "Enemies in your Presence count as having double Power".
- Monster Power: a unique enemy is always 20.
- Power consumers new or changed in 1.0:
  - Tasalio's Charge explosion (Riptide spear): "3% more Damage per Power of target".
  - Whispers of the Damned: 1 empowered attack per 10 Power, capped at 50.
  - Deathblow: Reaper's Touch per Power of slain rares and uniques.
  - Glory: "generate Glory equal to the monster's Power".
  - Lightless Stalker: 75% Surpassing chance per Power.
  - Scarred Faith (timeless keystone): "5% of Physical Damage prevented Recouped as Energy Shield per enemy Power".

**Interaction.** One shield doubles every Power-keyed input at once. The most novel effect is defensive. Against a
unique, Scarred Faith recoups 100% of prevented physical damage, and 200% with doubled Power. A heavy armour stack would
then turn each boss hit into an Energy Shield refill larger than the damage it prevented (ES is capped at your armour
value). Offensively:
- Tasalio's explosion goes from ×1.6 to ×2.2 against a unique.
- Whispers goes from 2 to 4 empowered attacks per boss.
- Glory-skill uptime doubles for Glory skills that generate from Power.

**Score.** This is breadth, not height. Power is fixed at 2×, so it does not meet the "scalar that scales high" bar on
its own. Its value is that one item slot serves both a survival loop and several offence buckets. Tests:
- Does "per enemy Power" use the attacker's Power?
- Does the doubled Power reach Scarred Faith and Glory?
- Is there a cap?

### 3. Minion maximum life as ammunition, using a body that the build already scales

**Facts.**
- Abyssal Pact (spell, repeatable): "Sacrifices 19% of a damageable Minion's maximum life to deal that much Physical
  damage".
- Dark Pact: 13% as chaos.
- Bunkerbuster (Siegebreaker): 12.2% of a reviving minion's life as fire.
- The Watcher in the Dark: death explosion at 11% of life.
- The Knight's Squire wears player-grade armour.
- The Fallen Formation gives allies 22% of your armour.
- Bind Spectre captures any defeated monster as a reviving minion.

**Interaction.** Damage keys off *maximum* life, not current life, so a minion that regains life is a reusable battery.
Pacting the Squire, or a spectre of the highest-life monster that can be bound, puts the base damage under scaling that
spellcasters normally ignore:
- the monster's base life (it can vary by 10× or more between monster types)
- minion life increases
- minion life "more" (quality)
- the Squire's own gear

The player's spell multipliers then apply on top. Pairing Abyssal Pact with the immortal Lightless Stalker is printed on
one staff, so it counts as designed. The Squire and spectre versions are not.

**Score.** Abyssal Pact is meant to scale with minion life, so this is half-novel. It fits the owner's Knight ideas as a
use of the Squire that does not depend on the Squire's own damage (earlier exports measured that at 1 to 9%). Tests:
- Is the Squire "damageable" for Pacts?
- Squire life range.
- Can uniques or high-life monsters be bound?

### 4. Molten Forge anvil as a target for multi-hit skills (test only)

**Facts.** Molten Forge: "Striking the Anvil creates a damaging shockwave". An Ignited anvil has larger shockwaves with
extra fire.

**Interaction.** If every hit on the anvil makes a shockwave, the shockwave rate equals your hit rate, whatever the
enemy count. Candidates are a channelled Cyclone, Perforate's drill and Infernal Step. The anvil becomes an AoE
amplifier for single-target hit rate. Monk Bells work the same way and the devs capped those (hits-to-destroy, Ako's
Answer), so a cap is likely. Test: shockwaves per second against hit rate.

### 5. Whispers of the Damned as damage transfer that bypasses mitigation (speculative)

**Facts.** "Chaos damage dealt to one linked target causes every other linked targets to Lose Life equal to the Chaos
damage dealt". Secondary source: Withering Disintegration (new keystone) makes Wither raise chaos *hit* damage taken.

**Interaction.** Hitting a soft, Withered add makes the linked boss lose life. Life loss is not damage, so the boss's
resistances and damage reduction may not apply. With N linked enemies, damage is multiplied by N. For single bosses
this only works if the fight has adds. Tests:
- Does Life Loss bypass the boss's mitigation?
- Does poison or other chaos DoT count as "Chaos damage dealt"?
- Does the uber Arbiter have adds?

## Checked and rejected

| Idea | Why rejected |
|---|---|
| Abyssus "Every Rage also grants" + Primal Hunger (double max Rage) | Primal Hunger says "No Rage effect". PoB parses "every Rage also grants" as scaled by RageEffect and "no rage effect" as RageEffect = 0 (ModParser.lua 1422, 2847), so the flat damage is zeroed |
| Radiant Grief: light radius applies to Ignite magnitude | "Increases and reductions" only, which go into the same increased pool. Few sources. One bucket, not a multiplier |
| Hand of Weeping Black zombies + Sacrifice of Loyalty (1% more per 2 undead Power) | Zombie limit is 10, or 14 with quality, at about 1 Power each, so roughly 7% more |
| Windripper infinite penetration | Designed, and penetration floors resistance at 0: at most ×1.4 to ×2 on a high-resistance boss |
| Blueflame Bracers cold-to-ignite with freeze | Printed synergy (designed) |
| Darkness, Shades, Eclipse, Stealth bank, Detonate Ambush | Prior thread. The owner judged these as designed |

## Recommendation

Candidate 1 is the only one that meets both bars: a scalar with about 4 multiplicative buckets, a cubic per-use burst,
and a cross-theme accounting gap. It should be the first 1.0 test:
1. Find the Sacrificial Flame cap and decay.
2. Check whether afterimages copy the full sequence.
3. Check whether a use can be cancelled.

Candidate 2 is worth keeping as a defensive layer for any armour build. Candidates 3 to 5 depend on single unknowns, so
test them only after those unknowns are answered.
