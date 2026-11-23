# p2 notes

## (a) Tool-call counts (approx.)
- Read: 2 (brief, prompt)
- pos_catalogue search: ~12 (class, ascendancy, notable x many, skill, support x7, keystone, base)
- pos_catalogue explain: ~50 (batched in loops)
- pos_catalogue resolve: ~45 (batched)
- pos_catalogue bridges: 7 (bleeding/ignite, poison/flask, freeze/attack, shock/armour, heavy stun/bleed, stun/poison, ignite/poison, frozen/shock)
- pos_catalogue enablers: 4 (SkillConsumesBleeding/Freeze/Ignite/Poison)
- pos_pipeline validate: 2 (one deliberate unknown-condition call to list the conditions table)
- pos_pipeline sweep: 1 (keystone, Gas Arrow, Ranger/Pathfinder seed, Crude Bow)
- pos_pipeline slate validate: 1 (round1, 7 of 7 kept)

## Sweep summary
probe1.yaml: Gas Arrow, Ranger Pathfinder, conditions enemy_poisoned+enemy_ignited, no gear, weapon Crude Bow.
keystone sweep FullDPS baseline 1.7, 33 entries, 23 s. Top: Avatar of Fire +0.7, Resolute Technique +0.3, rest +0.1.
Candidate "Fire-only gas bomber" built on the Avatar of Fire lead (source sweep:probe1/Avatar of Fire).
Caveat: the sweep seed has no gear (tiny baseline), so deltas are low-resolution. Avatar of Fire also removes
non-fire damage, so poison damage on Gas Arrow is lost; the build is an ignite/fire build.

## (b) Names recalled from memory
All resolved exact on first try: Blood Hunt, Gas Arrow, Poisonburst Arrow, Electrocuting Arrow, Ice Strike, Boneshatter,
Molten Blast, Incendiary Shot, Armour Piercing Rounds, Crimson Assault, Avatar of Fire, Overwhelming Toxicity,
Neural Overload, Rupture, Incision, Escalating Poison, Biting Frost II, Deep Freeze, Fiery Death, classes/ascendancies
(Huntress, Amazon, Warrior, Warbringer, Monk, Invoker, Tactician, Smith of Kitava, Pathfinder, Mercenary, Ranger).
Misses: generic base names "Crossbow", "Heavy Crossbow", "Spear", "Quarterstaff", "Gnarled Quarterstaff",
"Forging Hammer" -> unresolved; used suggestions/search: Alloy Crossbow, Akoyan Spear, Aegis Quarterstaff, Fortified Hammer.
(The Dread Engineer's Concoction resolve failed only because of my shell quoting, not the catalogue.)
Most names came from search/explain, not memory.

## (c) Ideas dropped
- Dread Engineer's Concoction (ignite magnitude vs poisoned) on Gas Arrow: dropped because Avatar of Fire (sweep lead)
  removes the poison damage; kept as a possible variant.
- Bleeding Concoction / Acidic Concoction (Pathfinder unarmed): flask-charge skills, unclear fit with the harness.
- Hand of Chayula (Acolyte): meta curse/mark skill, damage secondary; skipped.
- Druid talisman skills (Rend, Flame Breath, Rolling Magma): no ailment-focused Shaman notables found; skipped.
- Malady (swaps bleed and poison chance): too fiddly for a measured slate.
- Second sweep: not run (cap and time).

## (d) Non-obvious candidates
- Stun-rupture bleeder: bleed is driven by heavy stun (Rupture), not by a bleed-chance stack; Boneshatter is a stun
  payoff skill that few would pair with an ailment build.
- Electrocute pulse gunner: crossbow ammo payoff keyed off a lightning ailment that Neural Overload applies via electrocute
  (not shock); a caster-free electrocute route.
- Fire-only gas bomber: a poison cloud skill turned into a pure fire/ignite build by Avatar of Fire (sweep lead).
- Freeze then shatter monk: melee freeze consumed by Biting Frost, with ground effect; less common than cold spells.

## (e) Declared conditions
- Aggravated bleed lance: enemy_bleeding. Sustained by Incision plus Crimson Assault (aggravated, more bleed magnitude);
  Blood Hunt also consumes it, so uptime may dip. Lone boss: plausible (single target, repeated hits). Breach packs: holds
  on enemies hit; weaker on enemies not yet hit.
- Stacked poison archer: enemy_poisoned. Sustained by Poisonburst Arrow's own burst + Escalating Poison. Boss: yes
  (direct hit). Packs: burst is area so yes.
- Fire-only gas bomber: enemy_ignited. Sustained by the arrow's fire (ignite chance from fire hits); the gas also needs an
  ignited enemy to detonate, so initial ignite must come from hits. Boss: ok if ignite lands (bosses may resist ailments
  via thresholds; not modelled by the condition). Packs: ok.
- Freeze then shatter monk: enemy_chilled, ground_chilled. Chilled from Ice Strike (cold) and Biting Frost leaving
  chilled; ground from the Invoker notable when freezing. Boss: freeze may not land on a boss (freeze threshold), which
  weakens both the payoff and the ground; Packs: holds.
- Electrocute pulse gunner: none declared. Electrocute is not in the conditions table, so the lightning-ailment payoff
  may read as zero; the report will tell. Boss/pack: unknown.
- Stun-rupture bleeder: enemy_bleeding. Heavy stun is not in the table; bleed must come from tree/other bleed chance.
  Heavily stunned requirement of Rupture is NOT modelled, so the condition is partly an assumption (stronger than the
  build proves). Boss: heavy stun on a boss is harder; Packs: easier.
- Ignite-extending forge blaster: enemy_ignited. Sustained by Molten Blast's fire hits. Boss/packs: same ailment-threshold
  caveat.

## (f) Friction
- `slate validate` output has no per-claim detail on success; fine.
- Search `text` seems to match names only for notables, so ailment notables could not be found by word; I had to
  list every ascendancy's notables and filter stats. A text search across stats would help.
- `bridges` output is verbose JSON with empty lines for skills.
- Conditions table lacks frozen, electrocuted, heavily stunned, which are central to several payoff skills.
- Prompt says `bases` slots; `Garment`/`Grand Regalia` etc. have no armour-type tag, making body choice noisy.
- Stray `p2/frozen/` directory existed; I did not read it.
