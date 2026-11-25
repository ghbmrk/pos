# Existing engines unlocked by 1.0

Owner ask: cmsg_01RxGYnd78N9kMbbAJ5pWDhU96GqofotvXXpnMvq2JcFH3 ("Doesn't have to be purely new just unlocked by new
things"). This widens the two earlier passes ([unplanned-1-0-first-principles.md](unplanned-1-0-first-principles.md),
[unplanned-1-0-rerun.md](unplanned-1-0-rerun.md)). Those looked mostly for new-with-new gaps, and set aside anything
where a piece was "as designed". Here a combination counts if **a 1.0 addition is what makes an existing engine
compound**, even when each piece works as designed on its own.

**Everything below is untested.** Old-game quotes come from the pinned data (catalogue `601768b`). 1.0 quotes come from
poe2db tooltips fetched 2026-11-25. Multipliers are estimates and probabilities are subjective.

## Answer

1. **Largest unlock: the Acolyte of Chayula's Darkness pool feeding the Shadow's Darkness payoffs.** The pool is an
   old engine: defensive Darkness of about 2,000, set by level and chaos resistance. The payoffs are new: Ambush,
   Eclipse and Whirling Blades, all tuned for 30. If they share one stat, an Ambush hit is about x60. Whirling Blades
   gains on two axes at once (knife count and damage per knife).
   - Under the earlier rule this was set aside as designed. Under this ask it is in scope and ranks first by ceiling.
   - Subjective chance: about 0.1, because the Acolyte rework (about Dec 4) decides it.
2. **Strongest by expected value: the Infernal Step x Echoing Strikes engine plus the Shadow kit as a copy layer,
   hosted by the old ascendancy whose bucket feeds Echoing.**
   - Old pieces: Giant's Blood, Deadeye Thrilling Chase and Avidity (or Witchhunter No Mercy), Serle's Grit.
   - Estimate: about x50-130 over a normal strike on a good rare when its tests pass, against x30-40 for the
     engine alone. Section 2.2 has the stack.
3. **Best for packs (Breach): Whispers of the Damned on a Lich, plus spread poison.**
   - Old pieces: Lich's infinite curse duration and Pathfinder's double poison count.
   - New pieces: Whispers' life-loss link, Pestilent Volley spread, and longer poison duration.
   - Damage multiplies by roughly the pack size. It does nothing on a lone boss.
4. **A portable result:** Eclipse plus three or four Shades is a gem-only layer worth about x5 at full uptime and
   about x2.4 on average, on any melee engine that can Ambush. That makes it the main thing 1.0 unlocks for old melee
   builds. Their old ascendancy buckets stay, because the layer needs no ascendancy.

## 1. Method

An existing engine is worth what its binding limit allows. A 1.0 addition unlocks it when it does one of three things:
- lifts that limit
- gives the engine's scalar a new multiplicative consumer
- removes the cost that kept two old pieces apart

For each old engine (meta-lesson patterns in `data/meta_lessons.yaml`, every ascendancy notable, keystones and
rule-changing uniques), the pass below names the binding limit and the 1.0 piece that acts on it.

## 2. Engines and their 1.0 unlocks

### 2.1 Defensive Darkness pool -> Shadow Darkness payoffs (ceiling)

| | Quote | Source |
|---|---|---|
| Old pool | "Base Maximum Darkness is 100", "+10 to Maximum Darkness per Level" (Embrace the Darkness); "1% increased maximum Darkness per 1% Chaos Resistance" (Deepening Shadows); "Chaos Resistance is doubled" (Chayula's Gift) | pinned data |
| New payoff | Ambush 3% more damage per Darkness expended; Eclipse "Attacks count as being used from Stealth and expending maximum Darkness"; Whirling Blades "Fires 1 additional projectile for each Darkness spent when Ambushing" | poe2db 1.0 |

**Binding limit lifted.** Shadow payoffs assume a maximum of 30. The old pool reaches about 2,050 at level 90:
1,000 base, x2.05 from the nodes and 85% chaos resistance.
- Ambush: about x62 per hit.
- Whirling Blades: 20 + 2,050 knives, each also carrying the x62.
- Eclipse means the pool is never actually spent.

**Decides it.** Whether 1.0 keeps one Darkness stat. poe2db has separate "Darkness" and "NewDarkness" ids, and the
Acolyte is being reworked. Test on Dec 4: does "increased maximum Darkness" raise the Shadow's cap?

### 2.2 Infernal Step engine: old ascendancies and items as add-ons (expected value)

The engine is new: Oro's Sacrifice, Infernal Step, Echoing Strikes. Simulated in
[sim-oro-infernal-step.md](sim-oro-infernal-step.md): everything holds pre-ramped x30-40, weighted mean about x15.
Which old pieces act on its scalars:

| Old piece | Quote | Acts on | Estimate |
|---|---|---|---|
| Giant's Blood (keystone) | "You can wield Two-Handed Axes, Maces and Swords in one hand" | Two Oro's: per-flame extra fire twice, if the lines stack | in the sim (x1.5 when they stack) |
| Deadeye Thrilling Chase | "Benefits from consuming Frenzy Charges for your Skills have 50% chance to be doubled" | Echoing: "1 additional afterimage per Frenzy Charge Consumed" | Bodies 6 -> 8 at 8 Frenzy: x1.33 |
| Deadeye Avidity | "50% chance when you gain a Frenzy Charge to gain an additional Frenzy Charge" | Oro's frenzy per second at max flames; refills Echoing between casts | Uptime, small |
| Witchhunter No Mercy (sim baseline) | "Deal up to 40% more Damage to Enemies based on their missing Concentration" | Every strike | x1.33 average |
| Serle's Grit (2H mace, off hand via Giant's Blood) | "Skills which Empower an Attack have (10-20)% chance to not count that Attack" | Echoing empowerment kept for the next use | Echoing coverage x1.11-1.25; costs the second Oro's |
| Chronomancer Time Snap | "Manipulate time, resetting the cooldowns of your other Skills" (32 s at level 20) | Echoing's 12.8 s cooldown, which the sim found to be the main gap | Echoing coverage about x1.15 |
| Titan Crushing Impacts | "25% more Damage against Heavy Stunned Enemies" | 2+3F strikes per use build heavy stun fast | x1.25 while stunned |

**Ascendancy choice.** Deadeye and Witchhunter come out about equal, about x1.33 each. Deadeye's bucket grows with
max Frenzy, which 1.0's tree may raise. Witchhunter's is fixed. Recommendation: put both in the sim as options.

**New layer on top: Eclipse plus Shades (2.4).** It adds x1.25 if Shades copy only your use. It adds x2.5 if they
also copy afterimage uses (the copy chain from the first pass, subjective chance 0.25).

Total, everything holding: x30-40 x 1.33 x 1.25 to 2.5, so about x50-130 over a rare strike. The engine's two
deciders still gate all of it: afterimages replay the whole sequence, and the Sacrificial Flame cap.

### 2.3 Curse and poison engines -> Whispers of the Damned (packs)

| | Quote |
|---|---|
| Old | Lich Incessant Cacophony: "Curses you inflict have infinite Duration", "You can apply an additional Curse". Pathfinder Overwhelming Toxicity: "Double the number of your Poisons that targets can be affected by", "50% less Poison Duration" |
| New | Whispers of the Damned (curse, Spread tag): "Chaos damage dealt to one linked target causes every other linked targets to Lose Life equal to the Chaos damage dealt". Pestilent Volley: knives in a poisoned enemy make a gas cloud "Spreading the largest active Poison". Dev interview: poison base duration 2 s -> about 6 s |

**Binding limit lifted.** Old poison or curse builds scale per target. Whispers sums damage across the linked pack.
Each enemy loses the chaos damage dealt to every other linked enemy, so pack damage rises about N-fold. Spread gives
every enemy the largest poison first. On a Lich, the link no longer runs out after 8 s.

**Scope.** Raises the Breach T15+ benchmark, not the Arbiter. Tests: does poison count as "Chaos damage dealt"; does
the link persist under infinite curse duration; is there a cap on links.

### 2.4 Any old melee engine -> Eclipse plus Shades (portable layer)

| | Quote (poe2db 1.0) |
|---|---|
| Shades | Ambushing with a Melee Attack makes Shades perform it; Shade portion deals 50% less damage, dealt by you; limit 3, plus 1 with Golem Hunger |
| Eclipse | "every Attack you make counts as being used from Stealth", "Shades' durations are paused"; needs 100 Glory, built by gaining Darkness |
| Enablers | Grim Bargain "Gain 5 Darkness on Critical Hit"; Conceal "+10 Darkness when you enter Stealth"; Martial Master (old) "Skills can build and retain Combo regardless of Weapon Set" |

**Binding limit lifted.** Old melee engines had no copy layer that works without an ascendancy. This one needs only
gems plus a dagger weapon set (Shades are made by dagger skills). The Monk's old Martial Master removes the
weapon-swap cost for combo builds.

**Estimate.** Ambush at maximum 30 Darkness gives x1.99. Three Shades give x2.5. That is about x5 at full uptime. An
earlier model put it at about x2.4 average when Glory does not refill during Eclipse.

**Guard to test.** Old "you use yourself" effects probably do not carry to Shade copies, for example Titan
aftershocks and Ancestral Boost.

### 2.5 Checked, with no unlock

| Old engine | 1.0 piece | Why not |
|---|---|---|
| Warbringer "Ignore Warcry Cooldowns" | Intimidate shockwave on every Infernal Step strike | Intimidate prints "Shockwave on up to the first 5 enemies Hit": capped per attack (dev guard) |
| Warbringer armour break below 0 | Elysium "Hits Break 102 Armour", Eroding Sands, Shattering Parry | Faster to reach the same cap. PoB: fully broken = fixed 20% increased damage taken; below zero is bounded by the enemy's own armour |
| Infernalist Bringer of Flame | Tear Through Reality "Ignites targets as though Hitting them" at 974% | Infernalist is being reworked. Benevolence already prints the ignite support (212% ignite magnitude, Chaos Incarnate) |
| Gemling Legionnaire support stacking | Demon Magus "15% more per different socketed Skill" | Gemling's per-support lines are the player's; the Magus is a minion. Gemling is confirmed nerfed |
| The Dark Defiler (per undead minion) | Hand of Weeping Black permanent zombies | Both are sceptres |
| The Fallen Formation "Banners always have maximum Valour" | Knight Standards and Valour notables | Standard numbers are unpublished; recheck at 1.0 |

## 3. Ranking

| Rank | Unlock | Ceiling (x rare strike) | Subjective chance | Decided by |
|---|---|---|---|---|
| 1 by ceiling | Defensive Darkness pool -> Shadow payoffs | x60 per hit; quadratic on Whirling Blades | 0.1 | Acolyte and keystone text, about Dec 4 |
| 1 by expected value | Infernal Step engine + Deadeye or Witchhunter + Eclipse and Shades | x50-130 | 0.5 on the engine's two deciders | Afterimage replay, flame cap, Shade copy scope |
| Packs | Lich + Whispers + spread poison | x pack size on Breach | 0.4 | Poison counts as chaos damage dealt |
| Portable | Eclipse + Shades on any old melee engine | x2.4-5 | 0.6 | Glory refill during Eclipse |

## 4. Next steps

- Add Deadeye (Thrilling Chase, Avidity), Serle's Grit, Time Snap and a Shade layer as switches in
  `pos_pipeline/sim_oro.py`, so the host choice is measured rather than estimated. This is a Sonnet-sized build task.
- On Dec 4, check the Darkness question first.
