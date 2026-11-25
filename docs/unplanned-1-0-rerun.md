# Most powerful unplanned 1.0 interaction: blank-slate rerun over the whole game

Owner ask: cmsg_01RxGYnd78N9kMbbAJ5pWDhUBS3v1vxHTZYS5kLbVWjUXb ("Run this again from first principles blank slate").

This pass inherits no picks and no exclusions. The method is also different from
[unplanned-1-0-first-principles.md](unplanned-1-0-first-principles.md): that pass read only the new 1.0 text. This one
starts from every scaling rule already in the game and asks what the 1.0 additions do to each.

**Everything below is untested.** 1.0 is not in PoB. Quotes are from the pinned 0.5 data (catalogue `601768b`) or
poe2db 1.0 tooltips fetched 2026-11-25. Multipliers are estimates. Probabilities are subjective.

## Answer

1. **By ceiling, one interaction is far above everything else: the Shadow's Darkness payoffs reading a Darkness pool
   sized for defence.** The pinned data gives the Acolyte of Chayula about 2,000 maximum Darkness. The Shadow's payoffs
   are tuned for 30. If 1.0 keeps one Darkness stat, each Ambush hit is about x60 and Whirling Blades throws about
   100x the knives. Subjective probability that the two stay one stat with the old numbers: about 0.1.
2. **By expected value, the Infernal Step x Echoing Strikes engine is still first** (simulated mean x15 over a normal
   strike on a good rare). This pass found three old-game modifiers that extend it; together about x1.3 to x1.6.
3. **Two independent blank-slate passes now return the same set.** The public text is exhausted. A third pass before
   new text appears will not change the ranking. The next real input is the ascendancy text (about Dec 4), which
   settles item 1 directly.

## 1. Method

1. Extract every rule of the form "X per Y", "counts as", "equal to", "instead", "no limit", "chance to not consume"
   from the full pinned data: 10,023 parsed modifier lines, 1,193 notables, 33 keystones, 435 uniques, 966 gems.
   After removing regeneration and attribute boilerplate, 446 distinct "per Y" rules remain.
2. For each quantity Y, list what raises it and what multiplies from it. A quantity matters only if it has a "more"
   or "extra damage" consumer, or a count consumer (copies, projectiles, hits).
3. Lay the 1.0 additions (65 gems, 16 uniques, Knight, Shadow mechanics) over that graph. Keep only edges where a 1.0
   rule connects to an old rule from another system.
4. Score by: size the scalar can reach, number of multiplicative consumers, and whether the text shows a dev guard.

Result of step 2: nearly all old "per Y" rules are "increased" (additive) or capped ("up to #%"). The old game has few
unbounded multiplicative scalars. The ones that exist:

| Scalar | Old rule (quote) | Reach | 1.0 consumer |
|---|---|---|---|
| Maximum Darkness | Embrace the Darkness: "Base Maximum Darkness is 100", "+10 to Maximum Darkness per Level"; Deepening Shadows: "1% increased maximum Darkness per 1% Chaos Resistance"; Chayula's Gift: "Chaos Resistance is doubled" | about 2,000 at level 90 | Ambush 3% more per Darkness; Eclipse "expending maximum Darkness"; Whirling Blades "1 additional projectile for each Darkness spent" |
| Empowered uses | Serle's Grit: "Skills which Empower an Attack have (10-20)% chance to not count that Attack"; The Empty Roar: "All Attacks count as Empowered Attacks" | 1.25x uses; permanent state | Echoing Strikes, Whispers of the Damned, Intimidate, Knight "Empowered Attacks deal 20% increased damage" |
| Frenzy consumed | Deadeye Thrilling Chase: "Benefits from consuming Frenzy Charges for your Skills have 50% chance to be doubled"; The Fabled Stag: "10% chance to not remove Charges but still count as consuming them" | 1.5x per charge | Echoing Strikes "1 additional afterimage per Frenzy Charge Consumed"; Bloodied Blade; Sand Scour |
| Undead minion count | The Dark Defiler: "Gain 5% of Damage as Chaos Damage per Undead Minion" | 10 to 14 zombies | Hand of Weeping Black: free, permanent, always-empowered zombies |
| Linked enemy count | none (new) | pack size | Whispers of the Damned: every other linked target loses life equal to chaos damage dealt |
| Enemy Power | Way of the Mountain, Scarred Faith, Sacrifice of Loyalty | fixed, 2x with Redblade | Tasalio's Charge, Whispers, Lightless Stalker |

## 2. Ranked findings

### 2.1 Darkness pool reuse (highest ceiling; decided by one fact)

**Mechanism.** The Acolyte's Darkness is a defensive pool: damage is reserved from it before life. Its size is set by
level and chaos resistance, because it replaces Spirit. The Shadow's Darkness is an offensive charge: default maximum
30, 3% more damage per point expended. If both are one stat in 1.0, every Shadow payoff reads a pool about 60 times
larger than it was tuned for.

**Estimate.** 100 + 10 x 90 = 1,000 base. Two small nodes (10% each) and 85% chaos resistance give x2.05: about 2,050.
- Ambush: 1 + 0.03 x 2,050 = about x62 per hit.
- Whirling Blades: 20 + 2,050 knives per throw, each also carrying the x62, and "multiple knives can hit the same
  target". Two buckets on one scalar: quadratic.
- Eclipse makes every attack count as "expending maximum Darkness", so the pool is not actually spent.

**Why it would be unplanned.** No guard is visible in either text. It is the only gap type where the scalar is set by
a different system for a different purpose.

**Why the probability is low (about 0.1).** poe2db carries two keyword ids ("Darkness" and "NewDarkness"), the Acolyte
is confirmed reworked, and a secondary source says its Darkness moves to a tree keystone. A deliberate split or
renumbering is the likely outcome. Embrace the Darkness also removes Spirit, and Ambush spends the defensive pool.

**Status.** Known to the project since 2026-11-23 and set aside as "designed". A blank-slate ranking by ceiling puts it
first regardless; the honest position is unresolved, not rejected. Test: read the 1.0 Acolyte node text and the
keystone; check whether "increased maximum Darkness" moves the Shadow's cap.

### 2.2 Old modifiers that extend the Infernal Step x Echoing Strikes engine (highest expected value)

The engine and its tests are in [sim-oro-infernal-step.md](sim-oro-infernal-step.md). New from this pass:

| Addition | Effect on the engine | Estimate | Cost / condition |
|---|---|---|---|
| Serle's Grit in the off hand (Giant's Blood) | 10-20% chance the Echoing-empowered Strike is not counted, so the next use is also empowered | Echoing coverage x1.11-1.25; fixes part of the cooldown gap the sim found | Replaces the second Oro's (loses one 12%-per-flame line if those stack) |
| The Fabled Stag notable | 10% chance Frenzy Charges are kept but counted as consumed | Small; keeps Frenzy for the next Echoing | Passive points |
| Deadeye, Thrilling Chase | Afterimages per Frenzy doubled half the time: 2 + 1.5F on average | Bodies x1.3 at 8 Frenzy | Ranger ascendancy; loses Witchhunter (No Mercy x1.33) |

None of these is a new engine. They are "old rule meets new skill" edges: each was written for warcries or for
frenzy-spending bow skills, and none mentions sword skills.

### 2.3 Whispers of the Damned x spread poison (pack content only)

**Facts.** Whispers: "Chaos damage dealt to one linked target causes every other linked targets to Lose Life equal to
the Chaos damage dealt". Pestilent Volley: gas cloud "Spreading the largest active Poison". Pathfinder: double the
number of poisons. Dev interview: poison base duration rises from 2 s to about 6 s in 1.0.

**Interaction.** Spread gives every enemy in the pack the largest poison (a maximum). Whispers then makes each enemy
lose the sum of the others' chaos damage. Maximum then sum: with N linked enemies each loses about N times the
largest poison per second, and a rare inside the pack ignores its own chaos resistance for that part.

**Score.** The scalar (pack size) is large in Breach T15+ and zero on a lone boss. It raises the Breach benchmark, not
the Arbiter one. Tests: does damage over time count as "Chaos damage dealt"; is overkill counted; cap on links.

### 2.4 The Dark Defiler x Hand of Weeping Black (blocked)

Free permanent zombies would feed "5% of Damage as Chaos Damage per Undead Minion" (14 zombies: +70%). Both items are
sceptres, so they cannot be worn together, and zombies lose "infinite Duration" when the Hand is swapped out. Rejected
unless 1.0 lets the Squire or a second slot hold one of them.

## 3. Old rule-benders checked against 1.0 with no result

| Old rule | Why nothing |
|---|---|
| Tactician "no Limit on the number of Banners" | Knight Standards belong to another ascendancy; cannot combine |
| Warbringer "Ignore Warcry Cooldowns" + Intimidate | Intimidate already prints a cooldown bypass; designed |
| Titan aftershock nodes + Kaom's Roots Mountain's Wake | Nodes say "you use yourself"; Mountain's Wake is triggered |
| Chronomancer Time Snap + Echoing / Siege of Sands | About x2 on a cooldown, no compounding |
| Blood Mage Sanguine Tides ("per 2% Life spent") + Infernal Step | Self-damage is not life spent |
| Sacrifice of Loyalty (more per undead Power) | Minions are 1 Power each; about 7% |
| Warbringer negative armour + new armour break sources | Old engine, no new bucket |
| Infernalist "Demonflame has no maximum" | Ascendancy is being reworked; text unknown |

## 4. Comparison

| Candidate | Ceiling (x normal rare strike) | Subjective chance it works | Decided by |
|---|---|---|---|
| 2.1 Darkness pool reuse | x60 per hit; far more on Whirling Blades | 0.1 | 1.0 Acolyte and keystone text (about Dec 4) |
| Infernal Step x Echoing (sim), with 2.2 additions | x40-115 pre-ramped; mean about x15, x20-24 with additions | 0.5 on its two deciders | Afterimage replay; Sacrificial Flame cap |
| Copy chain (previous pass) | x2.5 on the engine | 0.25 | Shades copy afterimage uses |
| 2.3 Whispers x spread poison | x pack size, Breach only | 0.4 | DoT counts as chaos damage dealt |

## 5. Recommendation

- Stop re-running the search on the current text. Two passes with different methods agree; the remaining uncertainty
  is in unpublished text, not in unread text.
- On Dec 4, check the Darkness question first. It has the largest swing of any single fact.
- Keep the Infernal Step engine as the 1.0 test target. Add Serle's Grit to the sim as an option against the second
  Oro's.
