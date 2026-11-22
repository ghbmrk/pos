# Notes (p3)
## (a) Tool calls by command (approx)
render 1; search ~14 (skill/notable/unique/base/support/ascendancy); bridges ~12 (4 breach terms + 8 cross-domain pairs); enablers 1; resolve ~45 (batched); explain ~25; sweep 0; validate_slate 1 (round1 only). validate_spec 0 (slate validation covers it).
## (b) Recalled names tried (resolve)
Exact: Detonate Dead, Lightning Spear, Volcanic Fissure, Glacial Cascade, Spark, Ball Lightning, Falling Thunder, Earthquake, Comet, Hammer of the Gods, Monk, Warrior, Witch, Sorceress, Invoker, Titan, Stormweaver, Lich, Warbringer, Infernalist, Resonance, Elemental Equilibrium, Acolyte of Chayula, Huntress, Amazon, Chain I, Wildfire, Reverberate, Tectonic Slams, Aftershock I, Eonyr's Thunder, Corpse Conservation, Meat Recycling, Shattering, Aftershocks, Fireball, bases Ashen Staff / Anvil Maul / Akoyan Spear.
Suggestion only: base "Quarterstaff" -> suggestions list; "Expert Ashen Staff" and "Crude Maul" -> suggestions (PoE1-style/wrong); I switched to Arcing Quarterstaff / Anvil Maul taken from catalogue search.
None: none fully unresolved. Most skill names were found via a full skill listing first, so few were pure memory.
## (c) Dropped
Warcry + Deidbell corpse explode (warcries are buff-only, no_metric). Xibaqua's Rending/Thunderous Leap (needs leap skill, extra setup). Hrimnor's Hymn (unique weapon would be overwritten by weapon-slot search). Into the Breach / Waking Dream (buff skill, no metric). Comet (fire infusion plumbing unclear).
## (d) Non-obvious
Corpse Reuse Detonation (Corpse Conservation + Meat Recycling: turns corpses into reusable ammo). Electrocute Staff Slam (kills explode via Eonyr's Thunder on a melee slam). Wildfire Fireball (ignite spreading, a delay-based clear). Elemental Equilibrium on Ball Lightning is speculative: it swaps infusion types, and the skill consumes Fire infusion, so it may be anti-synergy; left for the engine.
## (e) Procedure issues
- No Breach-specific content in catalogue (bridges with "Breach" empty), so "Breach" only maps to benchmark breach_t15; unclear how to use it.
- Supports need gem id for explain (names fail); resolve first. Not stated.
- explain/search outputs are verbose JSON; no "text only" view.
- Quarterstaff bases have type "Staff" and are mixed with caster staves; no way to filter quarterstaff.
- Step 0 default benchmarks include arbiter_ash; I chose breach_t15 only (pack idea).
- Numbers in quotes (e.g. "30% increased") are allowed in quotes but not claims; fine but easy to trip on.
- CLI `validate` for spec has no --help; takes a path only.
