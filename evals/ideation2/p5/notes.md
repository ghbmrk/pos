# p5 notes

## (a) Tool-call counts (CLI equivalents)
- search: about 9; explain: about 14; resolve: about 40 (batched); enablers: 2; bridges: 3
- validate_spec: 0; sweep: 0 (no probes written); validate_slate: 2 (round1, round2)
- plus a few direct reads of data/config_profiles.yaml (conditions table) and a bases dump via search.

## (b) Names recalled from memory and resolve results
All resolved exact on first try: classes Witch, Sorceress, Warrior, Druid; skills Exsanguinate, Thunderstorm,
Flameblast, Shockwave Totem, Furious Slam (from search), Earthquake, Forge Hammer (from search); keystones Crimson
Assault, Wildsurge Incantation, Blackflame Covenant, Avatar of Fire, Resolute Technique, Ancestral Bond, Primal Hunger.
Misses: ascendancy "Blood Mage" and "Smith of Kitava" resolve returns the squashed names BloodMage / SmithofKitava
as `name`; I first put those in the slate and the gate rejected them (spec wants the spaced form; suggestion given).
Fixed in round2.

## (c) Ideas dropped
- Whispers of Doom curse build, Dance with Death (one-hand plus empty off-hand), Heartstopper, Giant's Blood, Hollow
  Palm: not explored to a skill pairing; time/effort. Explosive Spear + Avatar of Fire: needs a frenzy charge
  to detonate, too many declared conditions. Molten Crash: similar to Furious Slam.

## (d) Non-obvious candidates
- Blood Barbs Exsanguinate: a spell whose damage is bleed, aggravated by Crimson Assault, with elemental feeding bleed.
- Primal Hunger Bear Slam: keystone whose "no Rage effect" drawback is irrelevant to a rage-spending skill.
- Blackflame Flameblast: ignite becomes chaos, a damage-type swap rarely tried on a channel.
- Ancestral Bond Shockwave: totem stacking via ignored keystone (gate classed it metric TotalDPS, "other").

## (e) Declared conditions
- Blood Barbs Exsanguinate: enemy_bleeding; sustained by the skill's own bleed; holds on a lone boss and in packs.
- Wildsurge Thunderstorm: enemy_shocked; sustained via drench from the storm (makes shock easier, not guaranteed);
  holds on a lone boss only if shock threshold allows; likely weaker on a boss than packs. Mildly optimistic.
- Blackflame Flameblast: enemy_ignited; the spell's own ignite; fine on boss and packs.
- Others: none declared.

## (f) Friction
- Brief says ascendancy names from resolve; resolve returns squashed names unusable in spec. Gate suggestion fixed it.
- Catalogue search --kind flag does not exist; kind is positional. search by skill-type "Mace" returned nothing.
- Base search has no easy filter by item class; I dumped and filtered locally.
- A `frozen/` directory already existed in p5; I did not read it.
