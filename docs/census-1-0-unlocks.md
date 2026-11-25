# Census of interactions unlocked by 1.0

Owner ask: cmsg_01RxGYnd78N9kMbbAJ5pWDhU7Qqen378nzgpqXb87gNg3i ("There are so many unlocked interactions that aren't
explored yet"). Scope rule: cmsg_01RxGYnd78N9kMbbAJ5pWDhU96GqofotvXXpnMvq2JcFH3 (an old piece plus a 1.0 piece counts).

Earlier passes searched by hand and found a handful. This pass is systematic:
- Every 1.0 addition is paired with every existing rule that touches the same mechanic.
- The pairs are scored, and the top of each list is triaged by hand.

**Everything below is untested.** Old-game quotes come from the pinned data (catalogue `601768b`, PoB skill files).
1.0 quotes come from poe2db, fetched 2026-11-25. Multipliers are estimates and probabilities are subjective.

## How the census works

- **1.0 side:** 105 entries in `tools/census/new_1_0.json`: the 65 gems, 16 uniques, their granted skills, the 13
  Knight nodes, and the Shade, Ambush and Blood Loss mechanics.
- **Old side:** 2,617 entries: keystones, all notables including ascendancy, uniques (newest variant), supports, skill
  descriptions.
- **Hooks:** 80 mechanic hooks (Frenzy Charge, Empower, Strike, Final Strike, warcry, Glory, Darkness, Shade, ignite,
  Blood Loss, Parry, Ready Stance, Wind, Remnant, minion, zombie, and so on) matched by regex.
- **Scoring:** a pair scores by the rarity of its shared hooks, boosted when the old line contains a compounding word
  ("more", "as extra", "per", "count as", "double", "instead", "additional").
- **Output:** 10,790 pairs, about 1,200 with strong wording. Run `python3 tools/census/pair_1_0.py`; it writes
  `tools/census/pairs_1_0.json` (2.5 MB, not committed).
- **Limit:** matching is lexical. It finds candidates, not verdicts. The triage below is the judgement step.

## New finds from the census (not in the earlier passes)

### 1. Olroth's Conviction x Echoing Strikes: one cast empowers three Strikes

| | Quote |
|---|---|
| Old | Olroth's Conviction (lineage support): "Supports skills that can Empower a specific number of other skills, causing them to apply to more skill uses"; PoB: `support_empowers_x_additional_other_skills = 2`; requires `EmpowersOtherSkill`, excludes `IndeterminateEmpowermentAmount` |
| New | Echoing Strikes: "Empower your next Strike to create afterimages that use that same Strike"; "2 afterimages and 1 additional afterimage per Frenzy Charge Consumed"; 12.8 s cooldown; "Empower duration is 10 seconds" |

**Effect.** Echoing names a fixed count ("your next Strike"), so it should qualify. One cast then gives afterimages to
three Strikes instead of one. The Frenzy Charges are spent once, so every empowered Strike gets the full count.
- For a normal Strike (about 1 s per use) this triples Echoing's coverage.
- With 8 Frenzy each empowered Strike has 6x bodies.
- The time-averaged multiplier goes from about x1.4 to about x2.2.
- For Infernal Step, Echoing becomes permanent at moderate flame counts, which closes the gap the sim named first.

**Decides it.** Whether the three empowered Strikes must all land inside the 10 s empower window. If they must,
Infernal Step at high flames cannot use all three, but faster Strikes can.

**Stacks with:**
- Perpetual Charge (old support): "chance not to remove each Charge while still gaining the benefits of consuming
  them", 25% in PoB. Frenzy is kept for the next cast.
- Murderous Intent (old support): "causing skills they Empower to Cull enemies".
- Deadeye Thrilling Chase (old ascendancy): afterimage count per Frenzy doubled half the time.

Recommendation: this is the strongest new lead. Add it to the sim before anything else.

### 2. Crescendo x 1.0 Final-Strike skills

| | Quote |
|---|---|
| Old | Crescendo I/II: "allowing you to use the Final Strike twice in succession"; Crescendo III: "causing the Final Strike to be Ancestrally Boosted" (Ancestrally Boosted counts as Empowered) |
| New | Haemorrhage Final Strike: "Ruptures Bleeding equal to 400% of Physical Hit damage dealt", performed immediately from Ready Stance. Perforate Final Strike: drill with "rapid additional Hits that inflict Bleeding". Shadow Assault Final Strike: creates a Shade and makes every other Shade repeat the dash |

**Effect.** Crescendo doubles the payoff half of a 1.0 combo Strike:
- Haemorrhage: two 400% ruptures per use.
- Shadow Assault: two Shades per use, so a Shade setup (3 or 4) is built in two uses instead of four.
- Crescendo III makes the Final Strike count as Empowered, which feeds the Knight's 20%.

**Estimate.** About x1.5-1.8 on the Final Strike half of each skill. It also cuts Shade setup time in half, which
matters for the Eclipse plus Shades layer below.

### 3. Volcanic Eruption x Infernal Step strikes (old support, new skill)

**Facts.** Volcanic Eruption (old support): "trigger Volcanic Eruption on Hit against Ignited Enemies"; triggered
skill has a 0.4 s cooldown and 4 projectiles. It excludes triggered and proxy skills. Oro's Sacrifice: "Hits with this
Weapon always Ignite targets that are on Full Life", and it deals fire damage.

**Effect.** Infernal Step makes 2+3F strikes per use, so the 0.4 s cooldown is always the limit: 2.5 eruptions per
second at no cost. That is a flat addition (about x1.1-1.2), not compounding. Listed because it is free on the leading
engine.

### 4. Vruun's Aftermath x Fangs of Agnar (old support, new unique)

**Facts.** Vruun's Aftermath: warcries "destroy Ice Crystals and Ice Fragments" and "empower additional Attacks if
they destroy enough". Fangs of Agnar (Agnar, 1.0 2H sword) builds two walls of Ice Crystals per use.
Intimidate (1.0 warcry) empowers 1 attack per 10 enemy Power, so 2 on a lone boss.

**Effect.** The crystal walls raise the empower count of any warcry above the Power limit. That makes Intimidate's
shockwave and the Knight's Empowered bonus available on a boss. Intimidate still caps its shockwave at the first 5
enemies per attack. Small on single target; listed as a lift of the 1.0 Power cap.

### 5. Manifest Weapon x 1.0 unique weapons (test only)

**Facts.** Smith of Kitava, Manifest Weapon: "Manifest a copy of your main hand Melee Martial Weapon as an immortal
Companion ... gains an additional Attack depending on its weapon type."

**Effect if it copies granted skills.** A copy of Oro's Sacrifice, Elysium or Benevolence would be a second body
using Infernal Step, Siege of Sands or Tear Through Reality. If it copies only base stats, it is a normal companion.
Test at 1.0: does the copy use the weapon's granted skill?

## Earlier finds, now placed in the same census

| Unlock | Old piece | 1.0 piece | Estimate | Doc |
|---|---|---|---|---|
| Darkness pool | Acolyte of Chayula maximum Darkness about 2,050 | Ambush, Eclipse, Whirling Blades | x60 per hit if one stat (subjective chance 0.1) | unlocked-by-1-0.md |
| Eclipse plus Shades on old melee | any melee ascendancy | Eclipse, Shades, dagger weapon set | x2.4-5 | unlocked-by-1-0.md |
| Frenzy doubling | Deadeye Thrilling Chase, Avidity | Echoing afterimages per Frenzy | x1.33 | unlocked-by-1-0.md |
| Empower not counted | Serle's Grit | Echoing | x1.1-1.25 coverage | unplanned-1-0-rerun.md |
| Cooldown reset | Chronomancer Time Snap | Echoing | x1.15 coverage | unlocked-by-1-0.md |
| Permanent link | Lich infinite curse | Whispers of the Damned | x pack size, Breach only | unlocked-by-1-0.md |
| Poison spread | Pathfinder double poisons | Pestilent Volley, longer poison | x pack size, Breach only | unplanned-1-0-rerun.md |

## Combined: the strongest build the census supports

Engine: Oro's Sacrifice x Infernal Step x Echoing Strikes ([sim-oro-infernal-step.md](sim-oro-infernal-step.md)).
On top of it:
- Echoing with Olroth's Conviction, Perpetual Charge and Murderous Intent: coverage x1.2-1.5 at high flames.
- Ascendancy: Deadeye (Thrilling Chase, Avidity) or Witchhunter (No Mercy): x1.33 either way.
- Eclipse plus Shades on a dagger weapon set, made faster with Crescendo on Shadow Assault: x1.25, or x2.5 if Shades
  also copy afterimage uses.
- Volcanic Eruption: x1.1.

Estimate: about x60-200 over a normal strike on a good rare when the engine's own tests pass. That compares with
x30-40 for the engine alone. Every add-on multiplies, so the spread is wide.

## What is still unexplored (honest gaps)

- **Undefined 1.0 keywords.** Sacrificial Flame, Leviathan Scales, Sand-Ingrained, Vampiric Boost and Chaos Incarnate
  have no text yet. Each is a hook the census cannot pair.
- **Ascendancy reworks.** Assassin, Infiltrator, Infernalist, Blood Mage, Acolyte and Mercenary text is unpublished.
  Every old-ascendancy pair here may change.
- **The 1.0 tree overhaul.** "Hundreds of new stats" are not in any public source. The old-tree side of the census is
  0.5 data.
- **Lexical blind spots.** Interactions with no shared word are missed, for example a stat that scales an unnamed
  quantity. The hand passes covered some of these.

## Next steps

1. Sim (a routine build task): add Olroth's Conviction (three empowered Strikes per cast, with and without the 10 s
   window), Perpetual Charge, Deadeye, Shades and Volcanic Eruption to `pos_pipeline/sim_oro.py`.
2. Rerun `tools/census/pair_1_0.py` on Dec 4 with the ascendancy text added to `new_1_0.json`. It is cheap to rerun.
