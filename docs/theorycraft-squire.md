# Theorycraft: what the Knight's Squire unlocks

Status: theorycraft for PoE2 1.0 (launch 2026-12-11), written 2026-11-22. No engine numbers and no invented values:
every game number below is quoted from a source or from the pinned catalogue.

- Owner asks: target builds cmsg_01RxGYnd78N9kMbbAJ5pWDhU91siC64a4kvoveU2FoJ95E; this exploration
  cmsg_01RxGYnd78N9kMbbAJ5pWDhUXBdt1E1AEWrTthjU1sog6S.
- Baseline (owner, cmsg_01RxGYnd78N9kMbbAJ5pWDhUKXYJyC5hSBnTQELRB8Csqz): content confirmed for 1.0 plus current game data.
- Cyclone is a confirmed 1.0 Duelist skill (owner, cmsg_01RxGYnd78N9kMbbAJ5pWDhURa2nYrS6YKpHK3nHuv9Fkf; sources F9 to F11).
  It is missing from the pinned data only because the Duelist is not in it yet.

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
5. **Engine gap found.** PoB's Exposure config only takes effect when the player's own build can inflict that Exposure, so
   `separate_build` would read a Squire-only Exposure as zero (section 6). Other Squire effects map to verified PoB keys.

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
- The only route is Lochtonial Caress on the Squire **[data]**. That needs gloves, a Presence and a Squire that holds
  charges.
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

## 3. Ranked ideas

**Plausibility** (does it work in 1.0 as described):
- High: every link is confirmed or is current-data text with no Squire-specific unknown.
- Medium: one Squire-specific unknown, with a precedent.
- Low: two or more unknowns.

**Payoff** is judged against the owner's benchmarks (one boss and one mass-mob content). Order follows plausibility
times payoff, ties to fewer unknowns.

| Rank | Idea | Chain | Plausibility | Payoff | Squire slots | 1.0 info that confirms it / kills it |
|---|---|---|---|---|---|---|
| 1 | **Debuff bot** | The Squire's weapon skill (plus supports) puts Shock, Exposure, Armour Break, Intimidate or Heavy Stun on the player's targets (2.2) | High for debuffs built into skills (Primal Strikes, Armour Breaker, lightning hits); Medium for support-applied | High | weapon, gems (ring for Blackheart) | Confirms: the Squire takes supports and attacks the player's target. Kills: supports barred and no usable debuff-skill |
| 2 | **Squire as consumer** (build 2a) | The player applies bleed or elemental ailments; Blood Hunt, Bloodhound's Mark or Elemental Sundering on the Squire detonates them (2.3) | High (bleed, demoed); Medium (elemental twin) | Medium-High, and adds a second damage source with its own weapon budget | weapon | Confirms: demo as shown; Elemental Sundering usable by the Squire. Kills: consume skills only take the user's own ailments |
| 3 | **Ground painter for Cyclone** (build 1) | Squire-made Shocked, Chilled or Ignited ground; Cyclone picks it up for element and ailment; -walker notables (2.1) | Medium | High | boots, or weapon and gems | Confirms: Squire ground is picked up and counts as allied. Kills: pickup only from the player's own ground. Sims can also kill it, if The Taming matches it (section 4) |
| 4 | **Damage sponge** | Damage moves to a damageable Squire; its armour and life gear protects the player (2.7) | Medium | Medium-High (boss survival) | armour pieces | Confirms: the Squire is damageable and Loyalty supports Summon Squire. Kills: an immortal or untargetable Squire |
| 5 | **Heavy-stun setter** | Marohi Erqi on the Squire Heavy Stuns full-life enemies; this activates Bloodhound's Mark and opens Heavy-Stunned windows | Medium | Medium (packs more than bosses) | two-handed mace | Confirms: two-handed maces allowed. Kills: weapon restrictions |
| 6 | **Presence projector** | The Coming Calamity, Leer Cast, Fixation of Yix or Xoph's Blood on the Squire (2.4) | Low | Very high | body, helmet, amulet | Confirms: the Squire has those slots and its own Presence. Kills: no such slots, or "your Presence" undefined for the Squire |
| 7 | **Catalysing Discharge** (build 2b) | Catalysing Elements on Cyclone triggers discharges when boosted by allied ground the Squire made (2.1) | Medium-Low | Medium-High | as rank 3 | Confirms: Cyclone has `InteractsWithElementalGround`, the support survives the rebalance, and Squire ground is "allied". Kills: any one of those |
| 8 | **Parry outsourcing** | A Squire with a buckler parries; enemies are Parried; the player's Cyclone hits them, and Bloodied Blade on Parried enters Blood Stance | Low | High | buckler | Confirms: the AI parries and the Squire takes a buckler |
| 9 | **Frenzy pipeline** (build 2c, as asked) | The Squire gains Frenzy; Lochtonial Caress shares it; Echoing Strikes or Sand Scour spends it (2.5) | Low | High | gloves | Confirms: the Squire holds charges, has gloves and a Presence; Echoing Strikes text |
| 10 | **Banner loop** | Banners buff both actors (confirmed, F7); the Squire also speeds Glory and Valour | Low for the Squire-specific part | Medium | none | Confirms: the Squire builds the player's Glory or plants banners |

The Presence projector ranks sixth on expected value but has the largest upside. That is why its check (C3) sits
near the top of section 5: the check order follows decision value, not rank.

Cross-cutting **[inference]**: ranks 1 to 3 can work with only a weapon and gems on the Squire. Under the shared tier budget
(K3), they are the cheap options. Ranks 4 and 6 spend the Squire's armour budget, so K3's reallocation will decide
whether a point is worth more on the Squire or on the player.

## 4. The owner's builds, rethought

### Build 1: Squire makes ground, player uses Cyclone

**Mechanism:** confirmed (F8, F10, F11).

**Concept package** (names only, no numbers):
- *Player:* Knight Duelist with Cyclone; Vaal Standard and/or War Banner; Stormwalker, Frostwalker or Flamewalker;
  Catalysing Elements if Cyclone qualifies; Echoing Strikes if Frenzy is available.
- *Squire:* a sword with Blade Conduit, or a spear with Fangs of Frost on targets the player Parried. Wake of
  Destruction or Birth of Fury boots. A Mark supported by Charged Mark. Lightning Exposure on its lightning hits, which
  also stacks rank 1 onto the same Squire.

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

Check at 1.0: Elemental Discharge's text after the support rebalance (F14). It could change shape.

### Build 3: other value from two gear sets and a separate skill activation

- Rank 1 (debuffs at no action cost) is the reliable core.
- Rank 6 (Presence projector) is the upside.
- Rank 4 (damage sponge) covers boss survival.

## 5. 1.0 checks for K4

Ordered by decision value: how many ideas each check decides, weighted by the payoff at stake. Most need only the
equipment screen or a short in-game test on launch day.

| # | Check | How | Decides ranks |
|---|---|---|---|
| C1 | Squire equipment slots: which armour pieces, and whether it has jewellery | equipment screen | 3, 4, 5, 6, 8, 9 |
| C2 | Squire skill rules: how many skills; which types (Marks are likely, per the demo; spells, warcries, banners, persistent buffs?); whether support gems are allowed | gem screen | 1, 2, 3, 7, 10 |
| C3 | Does "your Presence" work on items the Squire wears? | put Leer Cast on the Squire and read the player's damage on the character sheet; or read stat descriptions in data | 6, 9 |
| C4 | Cyclone gem: its types (`Wind`, `Storm`, `InteractsWithElementalGround`?); whether pickup consumes the ground; whether several elements stack (F11 says they combine); its weapon requirement | gem data after re-pin | 3, 7, and the The Taming baseline |
| C5 | Does ground the Squire makes count as allied for Cyclone pickup, the -walker notables and Catalysing Elements? | in-game test with Wake of Destruction on the Squire | 3, 7 |
| C6 | Squire AI: when it uses Marks and ground skills, whether it attacks the player's target, any command skill | observe in-game | uptime for 1, 2, 3 |
| C7 | Can the Squire be damaged, die, or revive? | in-game | 4 |
| C8 | Does the Squire gain charges, and does Lochtonial Caress share them? | in-game | 9 |
| C9 | Do Squire attacks build the player's Glory or Valour? | in-game | 10 |
| C10 | Can Summon Squire take companion supports (Loyalty, Romira's Requital, Catha's Brilliance, Tangmazu's Thurible)? | gem screen | 2, 4 |
| C11 | Does PoB 1.0 model the Squire natively, and does it add a Cyclone ground-pickup option? | PoB code at the re-pin | engine path (native_pob vs separate_build) |
| C12 | Text of Elemental Discharge, Catalysing Elements and Echoing Strikes after the support rebalance | gem data after re-pin | 7, 9, build 2 |

Recommendation for K4: add C1 to C5 to `unknowns` in `data/actors.yaml` when the Squire is sourced. They decide the
most ideas per check.

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
  601768bd105869618c3d6581b883e5d7aeec91b2.
