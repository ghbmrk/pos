# Ideation eval p1 notes

Brief: arbiter_ash + breach_t15, tier budget (user said "budget"). Lightning + tanky fixed; class, delivery, defence, main skill open.
Stopped at Step 3 (2 gate rounds). No sweep, no engine commands.

## (a) Tool-call counts (approximate, tallied from memory of the session; helper scripts wrapped many in loops)
- resolve ~68 (batch loops)
- search ~7
- bridges ~28 (several returned empty)
- explain ~35
- enablers 2 (Shocked, GeneratesInfusion)
- validate_slate 2 (round1, round2)
- sweep 0

## (b) Names recalled from memory
- Resolved exact: Arc, Spark, Ball Lightning, Lightning Conduit, Storm Wave, Galvanic Shards, Lightning Spear (skills); Chaos Inoculation, Eldritch Battery, Resonance, Pain Attunement, Avatar of Fire (keystones); Stormweaver, Invoker, Chronomancer, Shaman, Titan, Warbringer (asc.); Lightning Coil only found as a unique.
- Unresolved when I tried the wrong kind: "Chaos Inoculation", "Eldritch Battery", "Resonance" as kind skill (suggestions only; they are keystones, so I re-resolved as keystone: exact). "Lightning Coil" as keystone: unresolved (it is a unique; exact there). Not respelled.
- Bases: "Warstaff", "Crossbow", "Spear", "Wand", "Sceptre" unresolved (generic words); used suggestions Wyrm Quarterstaff, Alloy Crossbow, Akoyan Spear, Attuned Wand (exact). "Voltaic Staff" exact but is a caster staff, not used.
- Quirk: "Breachlords Rift" (no apostrophe) resolved exact to "Breachlord's Rift".

## (c) Dropped
- Lightning Warp: movement/cull skill, poor main skill; kept only as lore ("deletes" idea via cull) but no confidence.
- Ball Lightning, Orb of Storms, Skeletal Storm Mage/minions: duplicate class or no_metric risk.
- Witchhunter Galvanic Shards + Overload (round 1): replaced in round 2 as a near-copy of the Mercenary crossbow candidate and a thin claim.
- Warbringer Storm Wave + Shockproof (round 1): replaced; the claim's quote did not support the engine I named, and Shockproof duplicated candidate 1.
- Eldritch Battery, Pain Attunement, Avatar of Fire: no tank/lightning story.
- Voltaic Staff weapon: caster staff, unclear fit.

## (d) Non-obvious
- Titan Conduit with Doryani's Prototype: armour counted against lightning twice (notable + unique), a tank layer aimed at the lightning boss; Doryani's resistance-mirroring text is a risk I did not resolve.
- Mercenary Voltaic Grenade + Breachlord's Rift: electrocute-to-armour-break via a support; grenade is an Attack with an electrocute buildup effect.
- Warbringer Storm Wave + Imploding Impacts: broken armour pushed below zero amplifies all hit damage; a physical-ish armour-break idea hosted on a lightning skill.
- Shaman Nova + Lightning Coil: physical-taken-as-lightning tanking with a ring nova.
- Invoker Falling Thunder + Resonance: charge-swap keystone feeding a power-charge consumer.

## (e) Procedure problems
- Skill `explain` needs the gem id (e.g. LightningWarpPlayer), not the name; `explain skill "Lightning Warp"` fails with "not in catalogue". Procedure says "explain(kind, name)" and the slate cite example uses `id`; I had to find ids via search. Also, search output is huge JSON; had to write wrapper scripts.
- CLI `bridges` takes only two single terms; multi-word terms and many natural pairs return nothing; no way to restrict kind, output unwieldy.
- Rule 3 forbids digits in claims but verbatim quotes often contain digits; fine, but claim text must paraphrase "10%" etc. Also words like "first/second" ambiguity unclear.
- Gate does not check that the claim supports the candidate's engine (round 1 kept a weak Shockproof claim); passing the gate says nothing about claim relevance. It also did not flag two Mercenary/Witchhunter crossbow candidates sharing ascendancy.
- "budget" tier semantics (what gear/unique price counts) not stated; I couldn't check that Doryani's Prototype / Lightning Coil fit a budget. No price lookup tool.
- Step 1 says to check `enablers` with skill types but types for lightning interactions (Shocked, Electrocute) are not skill types; `enablers Shocked` returned notables only.
- "Arbiter deletes" burst/boss-specific text (cull, lightning res of Arbiter) is not discoverable from the catalogue.
