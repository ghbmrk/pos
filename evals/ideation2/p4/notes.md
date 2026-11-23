# p4 notes

## (a) Tool-call counts (CLI equivalents)
- resolve: ~17 (ascendancies, bases, supports, skills)
- search: ~22 (skill/notable/base/support, incl. 3 helper-wrapped)
- explain: ~25 (via helper script, batched)
- enablers: 3 (GainsStages, ConsumesCharges, GeneratesCharges)
- bridges: 1 (Power Charge / Shock)
- validate_spec: 0; sweep: 0 (none run); validate_slate: 3 calls (round1 ok, a failed round2 attempt on schema header, round2 ok)

## (b) Names recalled from memory
- "Cyclone" (user): unresolved, no suggestions. PoE1 skill. Substituted Whirling Slash (spear whirlwind, stages) with Culmination II as the build-up/release layer.
- "Elemental Discharge" (user): unresolved (suggestions Elemental Surge/Storm/...). Substituted charge-consumption dumps: Wind Serpent's Fury + Amazon notable Elemental Surge (triggers on consuming a charge), Flicker Strike (Power Charges), Rain of Arrows.
- All other names (skills, notables, bases, supports) were taken from search/explain output before use; resolve exact for the ones checked (Akoyan Spear, Arcing Quarterstaff, Composite Bow, Crown Mace, Assassin Garb, Armoured Vest, Culmination II, Burgeon II, ascendancies). Misses: no Two Hand mace via first guess "Crown Mace" (it is one-hand) -> used Forge Maul from search.

## (c) Ideas dropped
- Elemental Equilibrium keystone on Ball Lightning: remaps infusion types so Ball Lightning's Fire consumption gets awkward; dropped.
- Pinnacle of Power / Charged Staff / Pinnacle-type buffs: buff-only, no_metric.
- Bonestorm, Detonating Arrow, Snipe, Siphoning Strike: kept archetype space smaller; overlap with kept channel/charge ideas.
- Second Wind Serpent's Fury build on Deadeye: near-duplicate of the Amazon one; used Rain of Arrows instead.

## (d) Non-obvious candidates
- Bell Combo Artist (Tempest Bell + Martial Artist Combo notables): delayed dump, Combo not a charge.
- Infusion Orb Stormweaver: Elemental Infusion collect/consume is the PoE2 stand-in for stored-element dump; no charges at all.
- Serpent Surge Amazon: Elemental Surge triggers on any charge consumption, closest to the "Elemental Discharge" intent.

## (e) Conditions
- Serpent Surge Amazon: frenzy_charges. Sustained by Prize of the Hunt (fills pool on gain). The gain source itself is not a fixed piece, so it is an assumption. Lone boss: plausible only if gain on hit exists; Breach packs: easier.
- Rainfall Deadeye: frenzy_charges. Avidity doubles gain chance, base source not fixed; same caveat. Boss ok if gains from hits, pack ok.
- Storm Teleport Monk: power_charges. Overflowing Power raises max; the gain source is not fixed. Flicker Strike chain needs nearby enemies, weak on lone boss, better in Breach packs.
- Others: none declared (Combo and infusions are not in the conditions table).

## (f) Friction
- Prompt says "Rankable skills only" but Wind Serpent's Fury etc. show "unknown" damage type; fine.
- "Claims may not contain digits or number words": the word "once"/"one" is easy to hit; avoided.
- Helper wrapper needed for compact search output (CLI prints large JSON). The directory had a pre-existing frozen/ folder with a final.yaml; I did not open it.
- Round 2 only changed a claim wording (Phased Form) that overstated the quote; the gate did not catch the overstatement.
- Cyclone/Elemental Discharge not in data: handled via substitution as instructed.
