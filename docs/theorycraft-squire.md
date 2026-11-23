# Theorycraft: what the Knight's Squire unlocks

Status: theorycraft for PoE2 1.0 (launch 2026-12-11), written 2026-11-22; sections 2.9 to 2.11 (and the S ideas,
C13 to C16 and the reverse-channel gap) added 2026-11-23 from owner follow-ups. No engine numbers and no invented
values: every game number below is quoted from a source, the pinned catalogue or PoB data at the same commit.

- Owner asks: target builds cmsg_01RxGYnd78N9kMbbAJ5pWDhU91siC64a4kvoveU2FoJ95E; this exploration
  cmsg_01RxGYnd78N9kMbbAJ5pWDhUXBdt1E1AEWrTthjU1sog6S; follow-ups cmsg_01RxGYnd78N9kMbbAJ5pWDhURuQsbp1xd2mVwRb6SLfg4Q,
  cmsg_01RxGYnd78N9kMbbAJ5pWDhUAC5GVTWyocZczA6Z6yoUGo, cmsg_01RxGYnd78N9kMbbAJ5pWDhUBUVT6jMPQX21ZJzPPgWj5Z,
  cmsg_01RxGYnd78N9kMbbAJ5pWDhULDDyGePmZhKfckt39s6SiR, cmsg_01RxGYnd78N9kMbbAJ5pWDhUBsXA8kfFPvTNvep5sCDPmY.
- Baseline (owner, cmsg_01RxGYnd78N9kMbbAJ5pWDhUKXYJyC5hSBnTQELRB8Csqz): content confirmed for 1.0 plus current game data.
- Cyclone is a confirmed 1.0 Duelist skill (owner, cmsg_01RxGYnd78N9kMbbAJ5pWDhURa2nYrS6YKpHK3nHuv9Fkf; sources F9 to F11).
  It is missing from the pinned data only because the Duelist is not in it yet.
- The Squire gets one skill plus its supports (owner, cmsg_01RxGYnd78N9kMbbAJ5pWDhUBsXA8kfFPvTNvep5sCDPmY, 2026-11-23).
  This conflicts with F6, where the demo Squire used two skills, so C2 re-checks it at 1.0. Section 2.11 and the
  one-skill note in section 3 follow the owner's statement.

Labels used on every claim:

| Label | Meaning |
|---|---|
| **[dev]** | a developer's own words, as quoted by the source |
| **[report]** | live report of the ExileCon 2026 keynote, demo or Q&A, or a hands-on preview |
| **[guide]** | third-party guide or aggregator (lower confidence; paraphrase unless quoted) |
| **[data]** | quoted from the pinned catalogue `data/catalogue/601768b.json` (PoE2 0.5 tree), via `python -m pos_catalogue explain KIND NAME` |
| **[inference]** | reasoning from the labelled facts above it |
| **[speculation]** | plausible, but nothing published supports it |

Current-data text can change at 1.0. Per ExileCon reports, "Support Gems were rebalanced across the board" and 1.0
"adds over 40 new Unique Items and reworks more than 70 existing ones" [report, pathofexile.gg Day 1]. Every **[data]**
quote below is therefore a candidate, not a promise.

## Bottom line

1. **The strongest bet is the Squire as an enemy debuffer, at no cost in player actions.** Shock, Exposure, Armour Break,
   Intimidate and Heavy Stun all come from skills, supports or items that a melee Squire can carry **[data]**.
   They are states on the enemy, so the player's hits benefit whoever applied them **[inference]**. Rank 1.
2. **Build 1 (Squire makes ground, player uses Cyclone) works in principle.** Cyclone "sucks up blood (and elemental) ground"
   **[report]**. Two things are open. First, whether ground the Squire makes is picked up like the player's own. Second,
   whether the Squire beats cheaper ground sources: the Duelist's own Blade Conduit and Vaal Standard, or a ring (The Taming)
   that lets Wind skills count as boosted with no ground at all **[data]**. Rank 3.
3. **Build 2 (Squire makes charges, Elemental Discharge on Cyclone) fails as written on current text.** Elemental Discharge
   supports Spells only and "Cannot support the skills of Minions" **[data]**, and charges a Squire gains stay on the Squire
   unless an item shares them. Three real PoE2 versions exist (section 4).
4. **The biggest swing is "in your Presence" items worn by the Squire.** If they work, The Coming Calamity ("Enemies in
   your Presence have no Elemental Resistances") and Leer Cast ("Allies in your Presence deal 50% increased Damage") turn
   the second gear set into one of the strongest multipliers available **[data]**. Non-player entities already have a
   Presence in current data: the Watchtowers notable reads "Enemies in their Presence" for totems **[data]**. Nothing confirms
   this for the Squire, so it is the first thing to check at 1.0 (section 5).
5. **Two engine gaps found.** PoB's Exposure config only takes effect when the player's own build can inflict that
   Exposure, so `separate_build` would read a Squire-only Exposure as zero. And nothing carries the player's minion,
   companion or ally buffs into a separate Squire build (section 6). Other Squire effects map to verified PoB keys.
6. **The owner's follow-ups add the strongest new idea: split setup and payoff (2.10).** Six payoff supports forbid their
   own setup (Exploit Weakness, Immolate, Flame Pillar, Haemocrystals, Battershout, Undermine), and Brink builds Heavy
   Stun but "cannot themselves Heavy Stun" **[data]**. A Squire that only sets up lets every player hit be a payoff
   **[inference]**. Giant's Blood lets the player hold two two-handed maces while the Squire holds a third, and Chober
   Chaber makes minion damage scale both actors (2.9). Ideas S1 to S6 in section 3.
7. **From first principles, the Squire's weapon picks the maximum (2.11).** Persistent states (Shock, Exposure, Ignite
   for Immolate) pay on every hit, so they go on Cyclone. Consumed states pay once per application, so they go on a
   slow, heavy hit, and Exploit Weakness turns out to consume **[data]**. With one Squire skill (owner), a Mark would
   stop the Squire hitting, so the Mark moves to the player **[inference]**. A mace Squire with Brain Rattler
   electrocutes to activate the player's Voltaic Mark (the elemental version: more multipliers, hinges on C16). A spear
   Squire's Blood Hunt detonates the player's bleeds while the player's Bloodhound's Mark builds Heavy Stun (the blood
   version: GGG's demo chain, fewer unknowns). Giant's Blood costs either version's mace finisher 30% (dual wielding)
   **[data]**.

## 1. What is confirmed for 1.0

| # | Fact | Label, source |
|---|---|---|
| F1 | "The Knight's first point recruits a squire." | [report] Output Lag, 2026-11-06 |
| F2 | Knight nodes as listed by poe2db (values are preview values). Esteemed Mentor: "Grants Skill: Summon Squire". Minor: "Companions deal 15% increased Damage". Bannerlord: "Select one option to allocate", then one of five lines: "Grants Skill: Maraketh Standard", and the same for Karui, Vaal, Ezomyte and Kalguuran Standard. Minor: "Banner Skills have 25% increased Duration". Glorious Entrance: "Grants Skill: Liberator's Chariot". Minor: "Skills which require Glory generate 1 Glory every 2 seconds". Honourbound: "Grants Skill: Honourbound Blade", "Gain 5 Valour every 2 seconds while a Rare or Unique monster is in your Presence", "Gain 5 Valour per 10 Glory consumed". Righteous Bastion: "Gain Guard for 4 seconds equal to 25% Damage Blocked". Minors: "15% increased Armour and Evasion Rating", "8% increased Block chance" | [guide] poe2db.tw/us/Knight (undated) |
| F3 | "The squire gets gear on its own equipment screen, takes any melee weapon and can be taught your skills through the gem screen." | [report] Output Lag |
| F4 | "you can summon a Squire that can be equipped with any of your extra melee gear" | [report] MMORPG.com hands-on, 2026-11-09 |
| F5 | "The Knight's squire is a companion, so it scales as a minion and also works as support." | [report] pathofexile.gg Day 2 (Q&A answer, speaker not named), 2026-11-09 |
| F6 | The demo Squire carried a spear with Blood Hunt and Bloodhound's Mark. The presenter: "Once you've got someone under your command it's your responsibility to feed and equip them" | [report] Output Lag |
| F7 | "War Banners raise attack speed and damage for everyone nearby." The demo banner also buffed the Squire | [report] Output Lag; [guide] expcarry, 2026-11-13 |
| F8 | "The Vaal standard leaves blood ground that Cyclone pulls in." | [report] Output Lag |
| F9 | "I'll tell you, thing number one was there had to be Cyclone." On combining mechanics: "add the Blood, add the Sand, add the Lightning" | [dev] Jonathan Rogers (Game Director), PCGamesN Gamescom 2026 interview |
| F10 | "Cyclone sucks up blood (and elemental) ground and sends out waves of blood that Bleed." Also: "Rending Dash, Cyclone and both Ready Stance skills move you." | [report] pathofexile.gg Day 2 |
| F11 | "Cyclone counts as a storm and can pick up elemental ground effects." In Rogers' demo, lightning ground from Blade Conduit carried into Cyclone, and effects combined rather than replacing each other | [guide] elyxir.gg, 2026-08-29; [report] kekbur.net Rogers interview, 2026-11-08 (paraphrase) |
| F12 | Blade Conduit (Duelist sword skill) leaves Shocked Ground | [guide] allthings.how, 2026-08-29 (paraphrase); consistent with F11 |
| F13 | "Combat Frenzy grants a Frenzy Charge, and Sand Scour can spend it to enter Sand Stance". A developer-made Cyclone build used Echoing Strikes, described as consuming Frenzy Charges to create extra cyclones | [report] pathofexile.gg Day 2; [guide] elyxir.gg (paraphrase, low confidence) |
| F14 | "Support Gems were rebalanced across the board"; "1.0 adds over 40 new Unique Items and reworks more than 70 existing ones" | [report] pathofexile.gg Day 1, 2026-11-07 |

**Not published by any source read** (each is a check in section 5): the Squire's slot list (jewellery? which armour?),
its skill count, support gems, AI or command behaviour, whether it can die, whether it has its own Presence, and
whether it gains charges or Glory.

**One conflict.** poe2db's prose says the Squire "can use any melee Skill Gems". But the demo's Bloodhound's Mark has no
Melee type in current data (types include Mark, Duration, Cooldown) **[data]**. So the Squire's gem pool is probably
wider than Melee-tagged skills, at least for Marks **[inference]**.

**Transcripts.** The ExileCon keynote video (YouTube `yul3Bt_irNY`) could not be read from this environment, because
YouTube is blocked by its network policy. Developer wording therefore comes from the written reports above. A transcript
would sharpen F3 to F8, but none of the unknowns in section 5 has a published answer in any report read.

## 2. Channels a second actor can use

### 2.1 Ground for Cyclone (owner build 1)

Current-data models for ground pickup **[data]**:
- Whirling Slash has types `Wind` and `InteractsWithElementalGround`.
- Tornado "absorbs that surface's Debuff, applying it to enemies inside the Tornado and causing the Tornado to deal
  extra damage of that element".
- PoB models Whirling Slash the same way (section 6).

So a 1.0 Cyclone pickup most likely means extra damage of the ground's element plus that element's ailment on enemies
hit **[inference]**.

Ground the Squire could make:

| Source | Text | What the Squire needs |
|---|---|---|
| Blade Conduit (1.0) | leaves Shocked Ground [guide, F12] | a sword, and the ability to use Duelist skills (F3 "taught your skills") |
| Wake of Destruction (boots) | "Drop Shocked Ground while moving, lasting 8 seconds"; "Adds 1 to (30-50) Lightning damage to Attacks" [data] | a boots slot |
| Birth of Fury (boots) | "Drop Ignited Ground while moving, which lasts 8 seconds and Ignites as though dealing Fire Damage equal to 10% of your maximum Life" [data] | a boots slot; the ignite scales with the Squire's life |
| Frost Nexus (support) | "Supports any skill that Hits enemies, causing it to create patches of Chilled Ground around Frozen enemies." [data] | support gems, and frozen targets |
| Charged Mark (support) | "Supports Mark Skills, causing them to Trigger Charged Mark when they are Activated. Charged Mark creates Shocked Ground at the target's location." [data] | support gems and a Mark (the demo Squire used a Mark, F6) |
| Fangs of Frost (spear) | "Hitting a Parried target Consumes the Debuff to cause an explosion of frost and leave Chilled Ground." [data] | a spear; targets Parried by the player [speculation: that the Squire can consume the player's Parried] |
| Shocking Leap, Holy Descent (supports for Jumping skills) | Shocked Ground "the first time they Critically Hit an enemy"; Consecrated Ground "when you land" [data] | support gems and a leap skill, e.g. Thunderous Leap (spear) |
| Gifts from Above (ring) | "You have Consecrated Ground around you while stationary" [data] | a ring slot. Consecrated Ground is not elemental |

What the player gets from elemental ground **[data]**:
- Stormwalker: "Gain 15% of Damage as Extra Lightning Damage while on Shocked Ground". Frostwalker and Flamewalker do
  the same for Chilled and Ignited Ground.
- Desert's Scorn: "Enemies standing on Chilled Ground take 25% increased Fire Damage" and "Enemies standing on Ignited
  Ground take 25% increased Cold Damage".
- Catalysing Elements (support, needs `InteractsWithElementalGround`): "Triggering Catalysing Discharge of the
  corresponding type when they are boosted by an allied Elemental Ground Surface".

**What the Squire has to beat.** This challenges the build's core assumption.
- The Duelist makes ground without a Squire: Blade Conduit (F12), the Vaal Standard banner (F8), and Blade Plunge,
  which in Sand or Blood Stance can create sandstorms or blood pools around each blade [guide, elyxir, paraphrase].
- The Taming (ring) needs no ground at all **[data]**: "Wind Skills which can be boosted by Elemental Ground Surfaces
  can be boosted by multiple Elemental Ground Surfaces" and "count as being boosted by Ignited, Shocked, and Chilled
  Ground". Berek's Grip, Pass and Respite do the same for one element each.
- So if 1.0 Cyclone is such a Wind skill, one ring gives the element boost with no ground. (F11 confirms "storm", not
  Wind; unknown.)
- Real ground still adds what a ring cannot: the ailment on enemies standing in it, the -walker notables, blood ground,
  and Catalysing Elements' "allied Elemental Ground Surface" trigger. Whether a ring's "count as being boosted" satisfies
  that trigger is unknown.
- The Squire's own edge is parallelism: ground appears where the Squire fights, without spending the player's actions
  or boots slot.

### 2.2 Enemy debuffs a Squire can apply

All of these are **[data]**:

| Debuff | Sources a Squire could carry |
|---|---|
| Exposure | Cold, Fire and Lightning Exposure supports ("inflict Exposure when it inflicts Freeze", "when Igniting", "when inflicting Shock"). Primal Strikes: "The third attack is a large swipe that inflicts Elemental Exposure". Blessed Bonds (gloves) |
| Armour Break | Armour Break I to III supports. Breachlord's Rift: "Break Armour of enemies it Freezes or Electrocutes". Armour Breaker: "weakening their Armour". Sunder applies "Sundered Armour, making it take additional increased Physical damage" |
| Intimidate | Blackheart (ring): "25% chance to Intimidate Enemies for 4 seconds on Hit" |
| Shock | any lightning hit, e.g. through Wake of Destruction's added lightning |
| Heavy Stun | Marohi Erqi (Totemic Greatclub): "Heavy Stuns Enemies that are on Full Life". Bloodhound's Mark: "making them suffer Heavy Stun build up from Blood Loss" |
| Freeze, Electrocute | cold and lightning hits; Freezing Mark and Voltaic Mark. Both stop enemies acting **[inference]**, which matters for the survival benchmark |
| Parried | Parry: "leaves enemies off balance, causing them to take massively increased Attack damage" (needs a buckler) |

These states sit on the enemy, so the player's hits benefit whoever applied them **[inference]**. Two kinds of wording
count only the player's own applications: "you inflict" (e.g. Blackflame's "Withered you inflict") and "your Marked
targets" (Sylvan's Effigy) **[inference]**.

### 2.3 The Squire as payoff (GGG's own demo pattern)

GGG's demo shows the player applying bleed and the Squire consuming it:
- The player bleeds enemies: in Blood Stance "every hit makes enemies bleed" [report, Day 1].
- The Squire's Blood Hunt: "Hitting an enemy that has suffered Blood Loss will cause a blood explosion and also Consume
  Bleeding" **[data]**.
- The Squire's Bloodhound's Mark: "The Mark will Activate, Consuming itself to Trigger Blood Explosion, when they are
  Heavy Stunned, or when they are killed if they suffered enough Blood Loss" **[data]**.
- That is two Squire skills. With the owner's one-skill rule, one of them moves to the player (2.11, blood version).

An elemental twin of that demo **[inference]**:
- The player's Cyclone picks up elemental ground and applies the matching ailment.
- A spear Squire's Elemental Sundering "Consumes Freeze, Shock and Ignite on a number of nearby enemies, Allies and
  Corpses ... each Ailment Consumed causes an explosion of the corresponding elemental damage type" **[data]**.
- Siphoning Strike (quarterstaff) consumes Shock for a shockwave **[data]**.
- This is the closest real PoE2 shape to "Elemental Discharge": the Squire is the discharge.

### 2.4 Presence gear: items that only matter on another wearer

Worn by the player, "Allies in your Presence" lines help only minions and party members. Worn by the Squire, the player
would be the ally **[inference]**. All lines below are **[data]**.

**Lines that buff allies (the player):**

| Item (slot) | Line |
|---|---|
| Leer Cast (helmet) | "Allies in your Presence deal 50% increased Damage" (it also has "25% reduced Damage" for the wearer) |
| Fixation of Yix (amulet) | Allies in your Presence get "(30-50)% increased Critical Hit Chance", "(30-50)% increased Critical Damage Bonus" and "(10-20)% increased Attack Speed"; also "50% reduced Presence Area of Effect" |
| Merit of Service (shield) | "Allies in your Presence have Block Chance equal to yours" |
| Corona of the Red Sun (helmet) | "Leeching Life from your Hits causes Allies in your Presence to also Leech the same amount of Life" |
| Lochtonial Caress (gloves) | "Share Charges with Allies in your Presence" |

**Lines that debuff enemies:**

| Item (slot) | Line |
|---|---|
| The Coming Calamity (body) | "Enemies in your Presence have no Elemental Resistances" |
| Xoph's Blood (amulet) | "Enemies in your Presence have -25% to Fire Resistance" |
| Perfidy (body) | "Enemies in your Presence are Intimidated" |
| Sandstorm Visage (helmet) | "Enemies in your Presence are Blinded"; "Every second, inflicts Critical Weakness on enemies in your Presence for (15-20) seconds" |
| Radiant Grief (helmet) | "Enemies in your Presence are Ignited as though dealt 200 Base Fire Damage" |

Notes on this channel:
- **Precedent:** Watchtowers reads "Each Totem applies 2% increased Damage taken to Enemies in their Presence" **[data]**,
  so the game already gives non-player entities a Presence.
- **Amplifiers** if the Squire does have a Presence **[data]**: Atziri's Contempt (spear, "(60-80)% increased Presence
  Area of Effect") and Alpha's Howl ("Presence Radius is doubled").
- **If the Squire has no amulet slot** **[speculation]**: Necromantic Talisman reads "All bonuses from Equipped Amulet
  apply to your Minions instead of you" **[data]**. That could route the player's Fixation of Yix to the Squire, at the
  cost of the player's own amulet.
- **Slot relief:** a Squire carrying The Coming Calamity also frees the player's body armour slot.

### 2.5 Charges (owner build 2)

Actions that grant "you" a charge, where "you" would be the Squire **[data]**:
- Disengage consumes Parried and grants a Frenzy Charge.
- Sniper's Mark grants a Frenzy Charge when it activates.
- Siphoning Strike consumes Shock and grants a Power Charge.
- Combat Frenzy grants a Frenzy Charge on Freeze, Electrocute or Pin.
- Enduring Impact can grant an Endurance Charge on Heavy Stun.

Getting those charges to the player:
- The only route that moves a charge the Squire gained is Lochtonial Caress on the Squire **[data]**. That needs gloves,
  a Presence and a Squire that holds charges.
- A second route skips the move: the Squire's crit activates the player's own Sniper's Mark, which grants the player the
  charge (2.10, build 2d) **[inference]**.
- The Conduit keystone goes the wrong way: "If you would gain a Charge, Allies in your Presence gain that Charge
  instead" **[data]**.
- Gravebind on the player, "Enemies in your Presence killed by anyone count as being killed by you instead" **[data]**,
  turns Squire kills into player kills. But current data has few generic on-kill charge sources.

Uses of Frenzy in 1.0: Echoing Strikes (extra cyclones) and Sand Scour (Sand Stance) (F13).

### 2.6 Banners and Glory

- War Banner grants "you and nearby Allies Attack damage, Attack speed and Accuracy", and banners build Glory from
  "Attacking enemies" **[data]**. The Squire is buffed by banners (F7).
- Lead by Example reads "Allies in your Presence have 30% increased Glory generation" **[data]**, so allies can generate
  Glory, at least for their own skills.
- Unknown: whether the Squire can plant a banner of its own, and whether its attacks feed the player's Glory and Valour.
- Knight-only synergy: Liberator's Chariot, reported as "Mounted Charge", "acts as a moving banner that pushes and
  stuns any enemy it hits" [report, Output Lag].
  Stuns lead into Sand Stance, and Bloodhound's Mark activates on Heavy Stun.

### 2.7 Defence: the second gear set as the player's buffer

Lines that move damage onto a companion **[data]**:
- Starkonja's Head: "15% of Damage from Hits is taken from your Damageable Companion's Life before you".
- Trusted Partner and Captivating Companionship: 5% each.
- Forgotten Warden: for Deflected hits.
- Supports Loyalty and Romira's Requital: "take a portion of Hit Damage you would otherwise have taken"; Romira's also
  Recoups.

Lines that reward having the companion nearby **[data]**: Captivating Companionship, "20% increased Armour, Evasion and
Energy Shield while your Companion is in your Presence".

If the Squire is a "Damageable Companion", its armour and life gear becomes a buffer for the player **[inference]**.

### 2.8 Companion passives that reach the player

All **[data]**:
- Inspiring Ally: "Increases and Reductions to Companion Damage also apply to you". This pairs with the Knight's
  "Companions deal 15% increased Damage" (F2).
- Sturdy Ally: "Companions gain your Strength".
- Yriel's Fostering and Trusted Kinship: "You can have two Companions of different types".

### 2.9 Three two-handed uniques: Giant's Blood plus the Squire

Owner follow-up (cmsg_01RxGYnd78N9kMbbAJ5pWDhURuQsbp1xd2mVwRb6SLfg4Q, cmsg_01RxGYnd78N9kMbbAJ5pWDhUAC5GVTWyocZczA6Z6yoUGo):
the player wields two two-handed uniques through Giant's Blood, and the Squire holds a third.

**Rules that bound it:**
- Giant's Blood reads "You can wield Two-Handed Axes, Maces and Swords in one hand", "Triple Attribute requirements of
  Martial Weapons" and "Inherent Life granted by Strength is halved" **[data]**. PoB accepts a Two Hand Sword, Axe or
  Mace in the off hand with it (`CalcSetup.lua` line 1233) **[data]**. Quarterstaves and talismans do not qualify.
- Current data has 12 unique two-handed maces, 6 unique quarterstaves, 6 unique talismans and no unique two-handed
  swords or axes **[data]**. So today the player's pair is two maces. Whether 1.0's new uniques (F14) include
  two-handed swords or axes is unknown.
- The Squire "takes any melee weapon" (F3), so maces and quarterstaves fit; talismans are unconfirmed (C13).
- Weapon swap adds no fourth weapon at the same time: PoB skips every item in the inactive weapon set (`CalcSetup.lua`
  line 1255) **[data]**. A swapped-in weapon still counts for debuffs that outlast the swap **[inference]**.
- Many unique lines cover only their own weapon's hits. PoB scopes Trephina's "Always deals Critical Hits against Heavy
  Stunned Enemies" and Shyaba's "Always Hits" to the hand holding them (`ModParser.lua` lines 3845 and 3500), and models
  dual-wield attacks as alternating hands unless the skill hits with both (`CalcOffence.lua` lines 4826 to 4835)
  **[data]**. So such a line covers about half of an alternating skill's hits **[inference]**. Unscoped lines, such as
  Chober Chaber's, cover every hit.
- The Squire has no known passive tree, so it holds one two-hander unless 1.0 says otherwise (C13).

**Which wearer each unique suits** (all quotes **[data]**):

| Unique (base) | Wearer | What the other actor gets |
|---|---|---|
| Chober Chaber (mace) | player | "Increases and Reductions to Minion Damage also affect you". PoB copies the player's minion damage increases onto the player's own skills (`CalcOffence.lua` lines 874 to 883). Those lines already scale the Squire, which "scales as a minion" (F5), so each one counts for both actors **[inference]**. Also "+(2-3) to Level of all Minion Skills" (matters only if Summon Squire is a Minion skill, C14) and "+50 to Spirit". Cost: "+100 Intelligence Requirement", tripled by Giant's Blood. Trenchtimbre (one-handed) does the same for minion attack speed |
| Trephina (mace) | player | "Always deals Critical Hits against Heavy Stunned Enemies" (its own hits) and "Crushes Enemies on Hit"; PoB: "Crushed enemies have 15% reduced Physical Damage Reduction". It cashes in Heavy Stuns the Squire builds (2.10) |
| Tidebreaker (mace) | Squire | "Causes (150-200)% increased Stun Buildup"; "All Damage from Hits with this Weapon Contributes to Chill Magnitude". A steady Heavy Stun builder, so it suits bosses |
| Marohi Erqi (mace) | Squire | "Heavy Stuns Enemies that are on Full Life"; "Crushes Enemies on Hit". Full life is mostly the first hit, so it suits packs the Squire reaches first (rank 5) |
| Brain Rattler (mace) | Squire | "All damage with this Weapon causes Electrocution buildup". Electrocuted enemies count as Immobilised (PoB: "Frozen, Pinned, Heavy Stunned, or Electrocuted"), and Electrocution activates Voltaic Mark |
| Quecholli (mace) | Squire | "This Weapon's Critical Hit Chance is 100%" on a Crumbling Maul, whose implicit "Causes Enemies to Explode on Critical kill, for 10% of their Life as Physical Damage". Every kill with it explodes: a pack-clear engine. Its crits also activate the player's Sniper's Mark (2.10) |
| Shyaba (mace) | Squire | "Always Hits" and "50% increased Attack Speed": a setter that never misses |
| Hoghunt (mace) | Squire | "Maim on Critical Hit": feeds Undermine |
| Nazir's Judgement (quarterstaff) | Squire | "Dazes on Hit"; PoB: "Dazed enemies take 50% more stun buildup for 8 seconds" |
| The Blood Thorn (quarterstaff) | Squire | "Causes Bleeding on Hit": feeds Haemocrystals and Blood Hunt |
| The Sentry (quarterstaff) | Squire | "100% increased Flammability Magnitude" and added fire: an Ignite source for Immolate and Flame Pillar |
| Hrimnor's Hymn (mace) | player | "Gain (10-20) Life per enemy killed". With Gravebind on the player, the Squire's kills count too (2.5) |

Talismans would matter only on a Squire that can wield them (C13) and has its own Presence (C3) **[data]**: Fury of the
King, "Enemies in your Presence have Exposure" (PoB: 20% of each elemental Exposure) plus "Skills which require Glory
generate (2-5) Glory every 2 seconds"; Amor Mandragora, "Enemies in your Presence are Hindered".

**Example three-weapon set** **[speculation]**, if C2, C13 and C15 go the right way:
- Player with Giant's Blood: Trephina and Chober Chaber.
- Squire: Tidebreaker, with Brink on its strike (2.10).
- The Squire keeps enemies close to Heavy Stun and the player's hits finish them. Trephina's hits crit on Heavy Stunned
  targets, and every minion damage line scales both actors.
- Two maces count as dual wielding, so mace finishers such as Boneshatter lose 30% here (2.11). This set cashes Heavy
  Stuns through Trephina's crits instead.
- Cyclone's weapon requirement (C4) can still veto maces for the player.

**Ruled out.** Two lines in data hand a weapon's damage to another actor, and both are other classes' ascendancy nodes
**[data]**: The Catha's Balance (Spirit Walker), "Companions gain added Attack damage equal to 60% of your main hand
Weapon's damage", and Watch How I Do It (Tactician), 25% to "Allies in your Presence". A Knight cannot take them.

### 2.10 Split setup and payoff

Owner follow-up (cmsg_01RxGYnd78N9kMbbAJ5pWDhUBUVT6jMPQX21ZJzPPgWj5Z): one actor applies and the other detonates, which
triggers payoffs much faster than one actor doing both, and it can be pushed to the extreme.

**Why it is faster** **[inference]**: one actor does setup and payoff in sequence, and a consume removes the state, so
each payoff waits for a fresh setup. Two actors run the steps in parallel, so a cycle takes as long as the slower step,
not both added together. The payoff actor also spends its whole rotation on payoff.

**Payoffs that cannot feed themselves.** Each of these supports forbids the setup it needs **[data]**. The last
column matters for rates (2.11, rule 1): a consumed state pays once per application.

| Payoff support | Text | State the Squire supplies | Consumes it? |
|---|---|---|---|
| Exploit Weakness | "deal more Damage against enemies with Broken Armour but preventing them from Breaking Armour themselves" | Broken Armour: Armour Breaker, Armour Break supports, Corrosion ("causing Poison it applies to also Break enemy Armour") | yes: PoB gives it the `ConsumesFullyBrokenArmour` type, and its 40% more is a consume stat |
| Immolate | "granting them extra Fire damage against Ignited enemies but making them unable to Ignite enemies themselves" | Ignite: The Sentry, any fire hit | no |
| Flame Pillar | "Consume Ignite on Hit to create pillars of flame, but cannot themselves inflict Ignite" | Ignite | yes |
| Haemocrystals | "Consume Bleeding on Hit to create explosive blood-filled crystals, but cannot themselves inflict Bleeding" | Bleeding: The Blood Thorn; Rusted Spikes ("When Supported Skills Pin an Enemy, they also Aggravate Bleeding") | yes |
| Battershout (warcries) | "Consume Fully Broken Armour to trigger Physical Damage explosions on Enemies within their range but cannot themselves Break Armour" | Fully Broken Armour | yes |
| Undermine | "Consume Maim on hit, Breaking a percentage of the Maimed target's Armour in doing so. Supported Skills cannot themselves inflict Maim" | Maim: Hoghunt | yes |

The mirror image is setters that cannot finish **[data]**:
- Brink I: "Supported Skills build up Heavy Stun more quickly, but cannot themselves Heavy Stun".
- Pin I: "allowing its Physical damage to Pin enemies but making it unable to Stun".

Solo, each needs a second skill to feed it. Split, each side's drawback costs nothing, because the other actor covers it
**[inference]**.

**The support wording points the same way** **[inference]**. The setters read "any skill that Hits enemies" or "Melee
Attack Skills". Haemocrystals, Flame Pillar, Runeforged Blades and Frenzied Riposte support only skills "you use
yourself" (or "you use or Trigger yourself"), and Flame Pillar "does not modify the Skills of Minions" **[data]**. So if
the Squire takes supports (C2), it can carry the setters and the payoffs stay on the player. That is the reverse of GGG's
demo (2.3).

**Which way round.** Put the payoff on the actor whose stats it reads (2.11, rules 1 and 2) **[inference]**:
- Payoffs that scale with the payoff actor's own hit ("more Damage", "extra Fire damage") favour the player, who has the
  larger damage budget.
- Payoffs that read the consumed state favour the opposite split. Haemocrystals deals damage "based on a percentage of
  the expected Damage of the Consumed Bleeding"; Flame Pillar deals 25% of the remaining Ignite; Herald of Blood's
  explosion "is partially based on their accumulated Blood Loss" **[data]**. Fed by the Squire's weaker ailment they pay
  less. They pay most when the player applies the state and a slow hit consumes it, as in GGG's demo (2.3).

**Heavy Stun thresholds** **[data]**:
- Boneshatter "will cause a Heavy Stun on enemies that are Primed for Stun. Upon causing a Heavy Stun it will also
  create a Shockwave". Seismic Cry and Staggering Palm also Heavy Stun Primed enemies.
- Impact Shockwave (Melee Strike and Wind attacks) creates "an Aftershock that damages enemies around the target when
  they Heavy Stun an enemy". Whirling Slash, the Cyclone stand-in, qualifies; Cyclone's types are C4.
- Hammer of the Gods: "Build Glory by Heavy Stunning enemies", a Glory sink for the Knight.
- Vaulting Impact "applies Broken Stance to Dazed enemies, causing any Hits against those enemies to deal extra damage".

So a Squire with Brink, Tidebreaker and Daze could keep enemies Primed, and the player's hit would be the one that Heavy
Stuns **[inference]**. Whether both actors fill one meter, and whose Heavy Stun it counts as, is C15.

**Mark relays** (texts **[data]**, cross-actor readings **[inference]**):
- Sniper's Mark: "The next Critical Hit the target receives Activates the Mark, Consuming it to deal extra damage and
  grant you a Frenzy Charge". The word "receives" names no source, so a Squire's crit (Quecholli always crits) should
  activate the player's Mark, and "you" is the player who placed it. That is build 2d (section 4).
- Voltaic Mark activates "When the Marked target is Electrocuted" (Brain Rattler on the Squire). Freezing Mark activates
  "When the Marked target is Frozen", and Bloodhound's Mark "when they are Heavy Stunned".
- Charged Mark: an activation "creates Shocked Ground at the target's location", which Cyclone can pick up (build 1).
- Rate caps: these Marks carry the `Cooldown` type, and Called Shots re-marks "at most once every few seconds"
  **[data]**. PoB lists a 0.5 s cooldown for Voltaic, Freezing and Bloodhound's Mark and 6 s for Sniper's Mark
  **[data]**. A mark relay runs at the Mark's pace, not the setter's.
- A target holds one Mark by default, which on a boss makes the player's and the Squire's Marks compete (2.11, rule 5).

**Kill relay** **[inference]**: with Gravebind on the player (2.5), the Squire's kills of bleeding enemies count as the
player's. They should then also fire the player's Herald of Blood: "killing an enemy with Blood Loss will cause a bloody
explosion" **[data]** (C16).

**The extreme version** **[speculation]**, assuming every check above goes the right way:
- Squire, setters only: Tidebreaker (or Nazir's Judgement) and one strike, Armour Breaker, supported by Brink (one
  skill plus supports). Its weapon decides which ailment it adds (The Sentry for Ignite, which Immolate pays on).
- Player, payoffs only: Cyclone with Immolate and Impact Shockwave (if Cyclone qualifies). Exploit Weakness consumes
  Fully Broken Armour, so it belongs on a separate heavy hit, not on Cyclone (corrected 2026-11-23, see 2.11).
  Trephina in one hand; Hammer of the Gods spends the Glory, at 30% less if the player dual wields (2.11).
- What caps it **[inference]**:
  - Every consumed state must be re-applied, so the payoff rate cannot exceed the Squire's application rate.
  - Mark cooldowns.
  - Recovery after a Heavy Stun (not in data).
  - The Squire's targeting (C6).
  - One weapon and one skill with its supports cover a handful of states, not all of them.
  - Haemocrystals on Cyclone would stop Cyclone's own bleeding (F10, "waves of blood that Bleed") and leave only the
    Squire's weaker bleed to consume. That is the wrong way round (2.11, rule 2).

### 2.11 Maximum prime and payoff, from first principles

Owner follow-up (cmsg_01RxGYnd78N9kMbbAJ5pWDhULDDyGePmZhKfckt39s6SiR): the Squire can hold a different weapon from the
player, and so use different skills, without either actor swapping. What is the maximum prime and payoff synergy?

**Scope.** Sources say the Squire "takes any melee weapon" (F3), not any weapon. Within melee the point holds: the
Squire's weapon serves the setup and the player's serves the payoff, with no swap **[inference]**. Bows, crossbows and
spells on the Squire are unconfirmed (C13). They would add consumers such as Fragmentation Rounds, Glacial Cascade and
Lightning Conduit to the lists below.

**Magnitudes** in PoB data at the pinned commit **[data]**. They are preview values; the support rebalance can change
them (F14).

| State or payoff | Effect | Consumes the state? |
|---|---|---|
| Shock | 20% increased damage taken; 8 s base duration | no |
| Intimidate | 10% increased damage taken | no |
| Exposure | −20% to one elemental resistance | no |
| Crushed | 15% reduced physical damage reduction | no |
| Immolate, against Ignited enemies | 30% of damage gained as extra fire | no |
| Sunder, against Fully Broken Armour | applies Sundered Armour, "making it take additional increased Physical damage" | no |
| Voltaic Mark, Freezing Mark | when Electrocuted or Frozen, the marker gains 30% of damage as extra lightning or cold; 10 s secondary duration; 0.5 s cooldown | the Mark |
| Bloodhound's Mark | 300% of physical damage over time taken as Heavy Stun buildup | the Mark, on Heavy Stun |
| Exploit Weakness | 40% more damage against Fully Broken Armour | yes |
| Biting Frost I and II | 40% more damage against Frozen enemies | yes (Freeze) |
| Blood Hunt | explosion deals 25% of the Blood Loss as life loss | yes (Bleeding) |
| Flame Pillar | pillars deal 25% of the remaining Ignite damage | yes (Ignite) |
| Haemocrystals | "based on a percentage of the expected Damage of the Consumed Bleeding" | yes (Bleeding) |
| Undermine | breaks 35% of the Maimed target's armour | yes (Maim) |
| Brink I, Brink II | 30%, 50% more stun buildup; "cannot themselves Heavy Stun" | no |
| Boneshatter | its own hits build no stun (−100% stun multiplier); it Heavy Stuns Primed enemies | no |

Files: `Data/Misc.lua` lines 76 and 94 and `CalcPerform.lua` line 3311 (Shock); `CalcSetup.lua` line 75 (Intimidate);
`ConfigOptions.lua` lines 1884 to 1899 (Exposure, Crushed); `Data/Skills/*.lua` (gems). Quoted texts are gem
descriptions.

**Five rules** **[inference]**:
1. **Persistent or consumed.** A persistent state pays on every hit while it lasts, so its value is the payoff actor's
   hit rate times uptime. A consumed state pays once per application. On one target, hits beyond the application rate
   gain nothing, and a fast skill's first hit eats the state. So persistent payoffs go on the fast hitter (Cyclone) and
   consuming ones on a slow, heavy hit. On packs this matters less, because each enemy carries its own state.
2. **Apply with the fast actor, consume with the slow one.** A consumer that reads the state (Blood Hunt, Flame Pillar,
   Haemocrystals, Herald of Blood) is sized by the applier's investment. A fast applier also re-applies before the next
   consume. With Cyclone, the player is the fast applier and the Squire's slow hit is the consumer, which is GGG's demo
   direction (2.3). A consumer that multiplies the hitter's own hit (Exploit Weakness, Biting Frost) is the opposite
   case: the Squire applies and the player's heavy hit consumes.
3. **Never consume a multiplier the other actor is using.** Siphoning Strike and Primal Strikes consume Shock.
   Elemental Sundering consumes Freeze, Shock and Ignite, so it also ends Immolate's condition. Blood Hunt consumes the
   Bleeding that Bloodhound's Mark turns into stun, which costs little only while Cyclone re-applies it.
4. **Open a new bucket before deepening one.** In PoB, Shock and Intimidate are both increased damage taken
   (`CalcPerform.lua` line 3311, `CalcSetup.lua` line 75), so together they give 30%, not the 32% that multiplying
   would give **[data]**. Resistance (Exposure), physical damage reduction (Crushed), damage gained as extra
   (Immolate, Mark buffs) and more multipliers (Exploit Weakness) are separate steps, so they multiply. Each Squire slot
   should open a bucket the player does not already fill.
5. **One Mark per target.** "Each target can be affected by a maximum of one Mark by default" **[guide]** (mobalytics,
   updated 2026-02-09). PoB agrees: one Mark slot (`CalcSetup.lua` line 995), filled from the player's, minions' and
   allies' Marks together (`CalcPerform.lua` lines 3026 to 3048) **[data]**. No line in current data adds a slot,
   though PoB already parses "you can apply an additional mark" (`ModParser.lua` line 4358). So on a boss the player's
   Mark and the Squire's Mark probably compete (C16). In packs, each Mark can sit on its own target. With one Squire
   skill, the Mark belongs on the player anyway (below).

**The game already splits the roles.** PoB data gives each of these payoffs a `cannot_` or `never_` stat for the state
it uses **[data]**:
- Bleeding: Blood Hunt, Haemocrystals. Ignite: Immolate, Flame Pillar. Maim: Undermine.
- Shock: Siphoning Strike, Primal Strikes. Freeze: Biting Frost I and II. Freeze, Shock and Ignite: Elemental Sundering.
- Broken Armour: Exploit Weakness, Battershout, Runeforged Blades, Leap Slam, Sunder.
- Heavy Stun: Boneshatter (by a −100% stun multiplier rather than a `cannot_` stat). Daze: Vaulting Impact
  (`cannot_daze`).
- Spells and crossbows outside the Squire's confirmed weapons: Lightning Conduit, Glacial Cascade, Icestorm,
  Elemental Discharge, Fragmentation Rounds, High Velocity Rounds.
- Primers on the other side: Brink and Pin (2.10).

**One Squire skill** (owner, 2026-11-23) **[inference]**:
- The Squire's setup budget is its weapon's own lines, which cost no skill, plus its one skill's built-in effect and
  that skill's supports. With supports allowed, support-made states (Brink, Lightning Exposure, Armour Break) are as
  available as skill-made ones.
- A Mark as that one skill would make the Squire a pure marker. Mark skills deal no damage themselves (PoB
  `base_deal_no_damage`) **[data]**, so the weapon's on-hit lines would never fire. The player has spare skill slots,
  so the Mark moves to the player in both versions below, and rule 5 no longer sets the two actors against each other.
- Supports can add setup to a consumer (Armour Break on Blood Hunt), so the one skill can still do both jobs.

**Two maxima for a Cyclone player** **[speculation]**. In both, the player owns the Mark and the Squire's weapon picks
the version.

*Elemental version (S6): a mace Squire.*
- Squire: Brain Rattler, which "Adds 1 to (110-115) Lightning Damage" and reads "All damage with this Weapon causes
  Electrocution buildup" **[data]**. Its one skill is a strike such as Armour Breaker, supported by Lightning Exposure
  ("inflict Exposure when inflicting Shock"), Brink and Armour Break. That one skill supplies Electrocution, Shock,
  Lightning Exposure, Broken Armour and Heavy Stun buildup.
- Player: Cyclone, and Voltaic Mark supported by Charged Mark. The Squire's Electrocution activates the Mark (C16). The
  player gains 30% of damage as extra lightning, and Charged Mark "creates Shocked Ground at the target's location".
- That ground is the player's own, so Cyclone's pickup and Stormwalker do not depend on C5 (build 1). Enemies standing
  in it may also be Shocked (2.1).
- The Mark is consumed on activation, so the player re-marks. Eternal Mark keeps it through the first activation.
- Player's finisher: Boneshatter with Exploit Weakness, on targets the Squire has Primed (Brink) and fully broken.

*Blood version: a spear Squire (GGG's demo kit, with the Mark moved to the player).*
- Player: Vaal Standard leaves "blood ground that Cyclone pulls in" (F8), and Cyclone's waves Bleed (F10). The player
  is the fast applier.
- Player's Mark: Bloodhound's Mark turns that Blood Loss into Heavy Stun buildup at 300%. Mark for Death on it reads
  "Enemies affected by Supported Marks will have their Armour Broken by Physical Damage they take". Both sit on the
  player's own gems, so they need nothing from the Squire.
- Squire: Blood Hunt, supported by Brink and Armour Break. It consumes the player's bleeding for an explosion sized by
  the player's Blood Loss (rule 2), the chain GGG demoed (2.3).
- Player's finisher once the target is Primed: Boneshatter causes the Heavy Stun and its Shockwave, and the Heavy Stun
  activates Bloodhound's Mark. Exploit Weakness on Boneshatter consumes Fully Broken Armour for 40% more, and
  Trephina's hits crit against the Heavy Stunned target.

**The decision boundary** **[inference]**:
- The blood version has fewer unknowns. Each link is either demoed (the Squire's Blood Hunt on the player's bleeds) or
  the player's own skill, and its stun comes from the player's Mark, so C15 matters little.
- The elemental version opens more buckets on every Cyclone hit: extra lightning (its buff takes all damage as the
  base, not only elemental), Shock, Exposure and Cyclone's ground. That gives it the higher ceiling, but it hinges on
  C16: the Squire's Electrocution must activate the player's Mark, and do it again soon after each activation.
- In packs the player can put two different Marks on two enemies, but the Squire's one weapon still serves only one
  version.

**Giant's Blood clashes with heavy mace skills** **[data]**. PoB counts any two weapons as dual wielding
(`CalcPerform.lua` lines 355 to 356). Boneshatter, Hammer of the Gods, Sunder, Leap Slam, Earthquake, Forge Hammer,
Perfect Strike, Rolling Slam and Stampede deal 30% less damage while dual wielding. Earthshatter and Volcanic Fissure
attack 30% slower, and Armour Breaker attacks 40% faster. So with Giant's Blood, either version should cash Heavy
Stuns through Trephina's crits instead of these skills. The elemental version loses less, because its core is the
persistent layer on Cyclone **[inference]**.

**What decides it at 1.0:** C16 for the elemental version (does the Squire's Electrocution activate the player's
Mark?). C2 confirms the one-skill rule and which supports work on the Squire's skill, including any "you use yourself"
limits. C15 decides only how much the Squire's Brink adds.

## 3. Ranked ideas

**Plausibility** (does it work in 1.0 as described):
- High: every link is confirmed or is current-data text with no Squire-specific unknown.
- Medium: one Squire-specific unknown, with a precedent.
- Low: two or more unknowns.

**Payoff** is judged against the owner's benchmarks (one boss and one mass-mob content). Order follows plausibility
times payoff, ties to fewer unknowns.

| Rank | Idea | Chain | Plausibility | Payoff | Squire slots | 1.0 info that confirms it / kills it |
|---|---|---|---|---|---|---|
| 1 | **Debuff bot** | The Squire's weapon skill (plus supports) puts Shock, Exposure, Armour Break, Intimidate or Heavy Stun on the player's targets (2.2) | High: supports are allowed (owner, 2026-11-23), so support-applied debuffs count as well as skill-built ones (Primal Strikes, Armour Breaker, lightning hits) | High | weapon, one skill and its supports (ring for Blackheart) | Confirms: the Squire attacks the player's target. Kills: no usable debuff skill |
| 2 | **Squire as consumer** (build 2a) | The player applies bleed or elemental ailments; Blood Hunt, Bloodhound's Mark or Elemental Sundering on the Squire detonates them (2.3) | High (bleed, demoed); Medium (elemental twin) | Medium-High, and adds a second damage source with its own weapon budget | weapon | Confirms: demo as shown; Elemental Sundering usable by the Squire. Kills: consume skills only take the user's own ailments |
| 3 | **Ground painter for Cyclone** (build 1) | Squire-made Shocked, Chilled or Ignited ground; Cyclone picks it up for element and ailment; -walker notables (2.1) | Medium | High | boots, or weapon and gems | Confirms: Squire ground is picked up and counts as allied. Kills: pickup only from the player's own ground. Sims can also kill it, if The Taming matches it (section 4) |
| 4 | **Damage sponge** | Damage moves to a damageable Squire; its armour and life gear protects the player (2.7) | Medium | Medium-High (boss survival) | armour pieces | Confirms: the Squire is damageable and Loyalty supports Summon Squire. Kills: an immortal or untargetable Squire |
| 5 | **Heavy-stun setter** | Marohi Erqi on the Squire Heavy Stuns full-life enemies; this activates Bloodhound's Mark and opens Heavy-Stunned windows | Medium | Medium (packs more than bosses) | two-handed mace | Confirms: two-handed maces allowed. Kills: weapon restrictions |
| 6 | **Presence projector** | The Coming Calamity, Leer Cast, Fixation of Yix or Xoph's Blood on the Squire (2.4) | Low | Very high | body, helmet, amulet | Confirms: the Squire has those slots and its own Presence. Kills: no such slots, or "your Presence" undefined for the Squire |
| 7 | **Catalysing Discharge** (build 2b) | Catalysing Elements on Cyclone triggers discharges when boosted by allied ground the Squire made (2.1) | Medium-Low | Medium-High | as rank 3 | Confirms: Cyclone has `InteractsWithElementalGround`, the support survives the rebalance, and Squire ground is "allied". Kills: any one of those |
| 8 | **Parry outsourcing** | A Squire with a buckler parries; enemies are Parried; the player's Cyclone hits them, and Bloodied Blade on Parried enters Blood Stance | Low | High | buckler | Confirms: the AI parries and the Squire takes a buckler |
| 9 | **Frenzy pipeline** (build 2c, as asked) | The Squire gains Frenzy; Lochtonial Caress shares it; Echoing Strikes or Sand Scour spends it (2.5) | Low | High | gloves | Confirms: the Squire holds charges, has gloves and a Presence; Echoing Strikes text |
| 10 | **Banner loop** | Banners buff both actors (confirmed, F7); the Squire also speeds Glory and Valour | Low for the Squire-specific part | Medium | none | Confirms: the Squire builds the player's Glory or plants banners |

**One Squire skill** (owner, 2026-11-23) **[inference]**. Ranks 1 to 3, 5 and S1 to S6 fit a weapon plus one skill
and its supports. Ranks 8 (Parry), 9 (Combat Frenzy or another charge skill) and 10 (banners) would spend the only skill
on something that does not hit, so they drop further. A Squire Mark, like the demo's Bloodhound's Mark, also leaves the
Squire unable to hit; the Mark belongs on the player (2.11).

The Presence projector ranks sixth on expected value but has the largest upside. That is why its check (C3) sits
near the top of section 5: the check order follows decision value, not rank.

Cross-cutting **[inference]**: ranks 1 to 3 can work with only a weapon and gems on the Squire. Under the shared tier budget
(K3), they are the cheap options. Ranks 4 and 6 spend the Squire's armour budget, so K3's reallocation will decide
whether a point is worth more on the Squire or on the player.

**Follow-up ideas (2026-11-23)**, scored on the same scale. The Sits column places each among the ten ranks without
renumbering them.

| ID | Idea | Plausibility | Payoff | Sits | 1.0 info that confirms it / kills it |
|---|---|---|---|---|---|
| S1 | **Split payoff**: Squire setters, player payoffs that cannot feed themselves (2.10) | High: one skill plus supports (owner) covers skill-made (Armour Breaker) and support-made (Brink) states | High: rank 1's debuffs become multipliers on every player hit | with rank 1 | Confirms: C6. Kills: no state-making skill or support works on the Squire |
| S2 | **Heavy Stun relay**: the Squire primes (Brink, Tidebreaker, Daze); the player finishes (Boneshatter, Impact Shockwave, Trephina, Hammer of the Gods) (2.9, 2.10) | Medium | High on bosses, if Heavy Stun repeats | after rank 3 | Confirms: C13, C15. Kills: separate stun meters per actor, or two-handed maces barred |
| S3 | **Shared scaling**: Chober Chaber through Giant's Blood; Inspiring Ally (2.8, 2.9) | High for the player side (PoB models it) | Medium | after rank 4 | Confirms: C14. The Squire side needs the reverse channel (section 6) to show up in sims |
| S4 | **Pack explosions**: Quecholli on the Squire (2.9) | Medium | Medium (packs only) | after rank 5 | Confirms: C13 |
| S5 | **Mark relay for charges**: the player's Sniper's Mark, activated by the Squire's guaranteed crits (2.10) | Medium-Low | Medium (Frenzy capped by the Mark's 6 s cooldown) | after rank 8, ahead of rank 9 | Confirms: C16. Kills: Marks activated only by the marker's own hits |
| S6 | **Mark buff relay** (elemental version of 2.11): the player's Voltaic Mark with Charged Mark, activated by the Squire's Electrocution (Brain Rattler) | Medium | High on bosses: 30% of damage as extra lightning on every Cyclone hit while the buff lasts, plus Shocked Ground from the player's own Mark | after rank 3, with S2 | Confirms: C16, C13. Kills: Marks activated only by the marker's own hits, or the Squire's Mark holding the target's only slot |

## 4. The owner's builds, rethought

### Build 1: Squire makes ground, player uses Cyclone

**Mechanism:** confirmed (F8, F10, F11).

**Concept package** (names only, no numbers):
- *Player:* Knight Duelist with Cyclone; Vaal Standard and/or War Banner; Stormwalker, Frostwalker or Flamewalker;
  Catalysing Elements if Cyclone qualifies; Echoing Strikes if Frenzy is available.
- *Squire* (one skill): a sword with Blade Conduit, or a spear with Fangs of Frost on targets the player Parried.
  Wake of Destruction or Birth of Fury boots make ground without using the skill. Lightning Exposure as a support on
  that skill stacks rank 1 onto the same Squire.
- *Variant with fewer unknowns (S6, 2.11):* Charged Mark on the player's own Voltaic Mark, activated by the Squire's
  Electrocution. The Shocked Ground is then the player's, so C5 drops out and C16 takes its place.

**Sims to run at 1.0 (K5).** Compare these four:
- (a) no Squire;
- (b) no Squire, with The Taming;
- (c) Squire ground;
- (d) Squire ground plus Squire debuffs.

Run each on the boss and pack benchmarks, with every uptime labelled. The Squire earns its slot only if (c) or (d)
beats (b) at the same tier budget.

### Build 2: Squire makes charges, Elemental Discharge with Cyclone

**What fails as written:**
- Elemental Discharge is "Supports any Spell that Hits enemies, causing it to Consume Elemental Ailments on hit to
  trigger an Elemental Discharge. Cannot support the skills of Minions" **[data]**. Cyclone is an attack.
- A Squire's charges stay on the Squire (2.5).

Real versions, best first:
- **2a, the Squire is the discharge** (rank 2). The player's Cyclone applies elemental ailments; the Squire's Elemental
  Sundering detonates them. This is the elemental twin of GGG's demo.
- **2b, Catalysing Discharge** (rank 7). This merges builds 1 and 2: ground the Squire makes triggers discharges
  through Cyclone.
- **2c, Frenzy pipeline** (rank 9). This is the literal "charges" version. It needs three unknowns to land and gives the
  biggest payoff only if Echoing Strikes is as reported.
- **2d, mark relay** (S5, added 2026-11-23). The player places Sniper's Mark; the Squire's guaranteed crits (Quecholli)
  activate it, and the player gains the Frenzy Charge. It needs no gloves, Presence or Squire charges, so it has fewer
  unknowns than 2c, but the Mark's cooldown caps its rate.

Check at 1.0: Elemental Discharge's text after the support rebalance (F14). It could change shape.

### Build 3: other value from two gear sets and a separate skill activation

- Rank 1 (debuffs at no action cost) is the reliable core.
- Rank 6 (Presence projector) is the upside.
- Rank 4 (damage sponge) covers boss survival.
- Split setup and payoff (S1, S2) is the strongest use of the separate skill activation: the Squire's skill becomes the
  player's setup, so the player's own skills can be all payoff.
- Section 2.11 gives the rules for that split and the two maxima (elemental and blood). With one Squire skill, the
  Squire's weapon chooses between them.

## 5. 1.0 checks for K4

Ordered by decision value: how many ideas each check decides, weighted by the payoff at stake. Most need only the
equipment screen or a short in-game test on launch day.

| # | Check | How | Decides ranks |
|---|---|---|---|
| C1 | Squire equipment slots: which armour pieces, and whether it has jewellery | equipment screen | 3, 4, 5, 6, 8, 9 |
| C2 | Squire skill rules: one skill plus its supports per the owner (2026-11-23), against two skills in the demo (F6), so confirm the count; which types (Marks, spells, warcries, banners, persistent buffs?); which supports work, including "you use yourself" limits | gem screen | 1, 2, 3, 7, 10, 2.11 |
| C3 | Does "your Presence" work on items the Squire wears? | put Leer Cast on the Squire and read the player's damage on the character sheet; or read stat descriptions in data | 6, 9 |
| C4 | Cyclone gem: its types (`Wind`, `Storm`, `InteractsWithElementalGround`?); whether pickup consumes the ground; whether several elements stack (F11 says they combine); its weapon requirement | gem data after re-pin | 3, 7, and the The Taming baseline |
| C5 | Does ground the Squire makes count as allied for Cyclone pickup, the -walker notables and Catalysing Elements? | in-game test with Wake of Destruction on the Squire | 3, 7 |
| C6 | Squire AI: when it uses its skill, whether it attacks the player's target, any command skill | observe in-game | uptime for 1, 2, 3 |
| C7 | Can the Squire be damaged, die, or revive? | in-game | 4 |
| C8 | Does the Squire gain charges, and does Lochtonial Caress share them? | in-game | 9 |
| C9 | Do Squire attacks build the player's Glory or Valour? | in-game | 10 |
| C10 | Can Summon Squire take companion supports (Loyalty, Romira's Requital, Catha's Brilliance, Tangmazu's Thurible)? | gem screen | 2, 4 |
| C11 | Does PoB 1.0 model the Squire natively, and does it add a Cyclone ground-pickup option? | PoB code at the re-pin | engine path (native_pob vs separate_build) |
| C12 | Text of Elemental Discharge, Catalysing Elements and Echoing Strikes after the support rebalance | gem data after re-pin | 7, 9, build 2 |
| C13 | Squire weapon rules: "any melee weapon" (F3) or any weapon (bows, crossbows, and so spells and ranged consumers); which two-handers (maces, quarterstaves, talismans); uniques allowed; a second weapon set; any passive tree (and so Giant's Blood); Giant's Blood's text at 1.0 | equipment screen; tree data after re-pin | S2, S4, S5, S6, 2.9 roles, 2.11 scope |
| C14 | Does Summon Squire carry the Minion and Companion types? | gem data after re-pin | S3, 2.8 |
| C15 | Do both actors' hits fill one Heavy Stun (and Freeze, Electrocute, Pin, Daze) buildup, and does the player's finishing hit count as the player's Heavy Stun for Boneshatter, Impact Shockwave and Glory? | in-game test: Squire with Brink, player with Boneshatter | S1, S2 |
| C16 | Do the Squire's hits and kills count for the player's Marks and Heralds (Sniper's Mark activation and who gains the charge; Voltaic and Freezing Mark activation by the Squire's Electrocution and Freeze; Herald of Blood with Gravebind)? Do the Squire's Mark and the player's Mark share a target's one Mark slot? | in-game test: Squire with Brain Rattler on a target the player marked with Voltaic Mark; then both actors mark one target | S5, S6, kill relay, 2.11 choice |

Recommendation for K4: add C1 to C5 to `unknowns` in `data/actors.yaml` when the Squire is sourced. They decide the
most ideas per check. Of the follow-up checks, C15 and C16 decide the most: together they pick between the two maxima
in 2.11.

## 6. Engine notes for Path of Sim (not implemented here)

PoB config keys checked in `src/Modules/ConfigOptions.lua` at the pinned PoB commit 601768b:

| Proposed effect | PoB key(s) | Note |
|---|---|---|
| player on Shocked, Chilled or Ignited Ground | `conditionOnShockedGround`, `conditionOnChilledGround`, `conditionOnIgnitedGround` | covers the -walker notables |
| enemy Shocked | `conditionEnemyShocked` | |
| enemy Intimidated | `conditionEnemyIntimidated` | |
| enemy Armour Broken | `conditionEnemyArmourBroken`, `multiplierArmourBreak` | the apply function itself is ungated; only the UI visibility is gated |
| enemy Heavy Stunned | `conditionEnemyHeavyStunned` | |
| enemy Critical Weakness | `conditionEnemyCriticalWeakness`, `enemyCriticalWeaknessStacks` | |
| enemy Frozen, Electrocuted, Blinded | `conditionEnemyFrozen`, `conditionEnemyElectrocuted`, `conditionEnemyBlinded` | |
| enemy Crushed, Dazed, Pinned, Maimed, Hindered, Immobilised (2.9, 2.10) | `conditionEnemyCrushed`, `conditionEnemyDazed`, `conditionEnemyPinned`, `conditionEnemyMaimed`, `conditionEnemyHindered`, `conditionEnemyImmobilised` | ungated: each apply function adds only an `Effective` condition. Frozen, Electrocuted, Pinned and Heavy Stunned also set Immobilised |
| enemy Bleeding, Ignited, Chilled; enemy on Full Life (2.10) | `conditionEnemyBleeding`, `conditionEnemyIgnited`, `conditionEnemyChilled`, `conditionEnemyFullLife` | ungated |
| banner Valour | `bannerValour` | |
| element picked up by a whirlwind (pre-1.0 stand-in for Cyclone) | `whirlwindBuffCold`, `whirlwindBuffFire`, `whirlwindBuffLightning` (Whirling Slash, Whirlwind Lance) | also marks the enemy Chilled, Ignited or Shocked; expect a Cyclone equivalent in PoB 1.0 (C11) |
| enemy Fire, Cold or Lightning Exposure | `conditionEnemyFireExposure`, `conditionEnemyColdExposure`, `conditionEnemyLightningExposure` | **gated, see below** |

**Gap: Exposure.**
- At ConfigOptions.lua lines 1884 to 1891, the exposure config adds its mod with `{ type = "ActorCondition", actor =
  "enemy", var = "CanApply<Element>Exposure" }`. That condition comes from the player's own build.
- So a Squire-only Exposure, applied as config on a player build that cannot inflict it, adds nothing.
- `ConfigTab:BuildModList` applies every set option regardless of UI visibility, so the gate lives in the mod, not in
  the UI.
- Fix options for K4: an effect kind that injects an enemy mod directly (a custom modifier), or setting the
  `CanApply...` condition alongside.

**Proposed check** (this turns the gap into a test, not a reminder): for every effect in `data/actor_effects.yaml`,
evaluate a probe build that has no source of that effect, with the effect on and off. Require a non-zero metric change,
or a documented reason why the metric does not use that effect. This would have caught Exposure. It would also catch
the same kind of gate on the existing ground and charge keys if PoB adds one at 1.0.

**Gap: the reverse channel** (found 2026-11-23).
- Under `separate_build`, effects flow one way, from the Squire to the player as config (docs/second-actor.md,
  section 3). Nothing carries the player's lines that scale the Squire into the Squire's own build:
  - minion and companion damage, including the Knight's "Companions deal 15% increased Damage";
  - "Allies in your Presence" gear worn by the player (Leer Cast, Fixation of Yix);
  - banners (F7).
- So S3, and every buff from the player to the Squire, would read as zero on the Squire's side.
- A ready channel exists: `pos_engine/engine.py` already passes `custom_mods`, and `pob_headless.lua` writes it to PoB's
  custom modifiers. K4 can rewrite each such player line in the Squire build's own terms. For example, a player line
  of the form `Minions deal X% increased Damage` becomes `X% increased Damage` on the Squire.
- The probe check applies here too: toggling a player-side minion line must move the Squire's metric.
- Under `native_pob`, PoB would do this itself (C11).

**Rates** **[inference]**. PoB gives per-hit numbers with a state on or off. How often a consumed state is present
(2.10) is a rate: the setter's application rate against the payoff's hit rate, capped by Mark cooldowns. K2's on/off
blend needs that uptime as an input. It belongs in the benchmark model layer, not in PoB.

**Rule to enforce: one Mark per target across actors** (found 2026-11-23, 2.11 rule 5).
- PoB fills one Mark slot from the player's, minions' and allies' Marks (`CalcPerform.lua` lines 3026 to 3048), so
  `native_pob` would enforce the cap itself.
- Under `separate_build`, each actor's build is calculated alone, so a Squire Mark and a player Mark on the same boss
  would both count. When Squire Marks are modelled, the engine has to let one Mark per target through, across both
  actors, unless C16 shows the cap is per actor.
- Stacking needs no engine work: PoB already adds Shock and Intimidate in one increased-damage-taken bucket when both
  are set in config.

## Sources

Read on 2026-11-22. Dates are as shown on each page.

- Output Lag, "Path of Exile 2 1.0 shows the Duelist's Knight ascendancy, with a squire and war banners", 2026-11-06:
  https://outputlag.com/news/path-of-exile-2-1-0-shows-the-duelists-knight-ascendancy-with-a-squire-and-war-banners/
- Output Lag, developer Q&A recap, 2026-11-06:
  https://outputlag.com/news/everything-ggg-answered-in-the-path-of-exile-2-exilecon-2026-developer-qa/
- PathofExile.gg, ExileCon 2026 Day 1 (2026-11-07) and Day 2 (2026-11-09): https://pathofexile.gg/exilecon-2026-day-1/ ,
  https://pathofexile.gg/exilecon-2026-day-2
- PCGamesN, Gamescom 2026 interview with Jonathan Rogers (undated page):
  https://www.pcgamesn.com/path-of-exile-2/1-0-interview-melee-duelist-swords
- kekbur.net, Rogers interview, 2026-11-08: https://kekbur.net/interviews/path-of-exile-2-duelist-interview-gamescom-2026/
- MMORPG.com hands-on, 2026-11-09:
  https://www.mmorpg.com/previews/path-of-exile-2-hands-on-shadow-and-duelist-exilecon-2026-2000139278
- poe2db, Knight (node text, undated): https://poe2db.tw/us/Knight
- expcarry Knight guide, 2026-11-13: https://expcarry.com/poe-2-knight-ascendancy-guide
- poe-vault Knight article (undated):
  https://www.poe-vault.com/poe2/news/path-of-exile-2s-duelist-knight-gets-a-squire-you-gear-yourself-war-banners-and-a-chariot-charge
- elyxir.gg Duelist reveal, 2026-08-29:
  https://www.elyxir.gg/news/path-of-exile-2/path-of-exile-2-duelist-reveal-sword-stances-endgame-builds-and-the-forbidden-rights-event
- allthings.how Duelist stances and skills, 2026-08-29:
  https://allthings.how/path-of-exile-2-duelist-how-sword-stances-and-skill-gems-work-ahead-of-1-0/
- ExileCon 2026 keynote video (not readable here): https://www.youtube.com/watch?v=yul3Bt_irNY
- Current game data: `data/catalogue/601768b.json`; PoB `ConfigOptions.lua` and `ConfigTab.lua` at commit
  601768bd105869618c3d6581b883e5d7aeec91b2. Added 2026-11-23: `CalcSetup.lua`, `CalcOffence.lua`, `ModParser.lua` and
  `ItemsTab.lua` at the same commit (Giant's Blood, weapon sets, dual wield, minion-to-player damage, mod scoping).
  Also added 2026-11-23 for 2.11: `CalcPerform.lua`, `Data/Misc.lua` and `Data/Skills/*.lua` at the same commit (gem
  magnitudes, cooldowns, Shock, Mark slots, dual wielding).
- mobalytics.gg, "PoE 2: Marks Explained", updated 2026-02-09, read 2026-11-23 (one Mark per target):
  https://mobalytics.gg/poe-2/guides/mark
