# p3 notes

## (a) Tool-call counts (approximate, CLI equivalents)
- resolve: 36 (bases, skills, classes/ascendancies, 1 keystone, 1 unique; all in one batch)
- search: about 16 (skill list, class, ascendancy, notable per ascendancy x9, base x3, support x1)
- explain: 18 (10 notables + 8 skills, through a helper script)
- bridges: 9 (Breach/area, Breach/damage, Shock/Slam, Freeze/Spear, Ignite/Totem, Chill/Quarterstaff, Poison/Spell, Corpse/Fire, Armour/Lightning)
- enablers: 0
- validate_spec: 1 (probe1.yaml, OK)
- sweep: 2 attempts, both crashed (PobEngineError, engine exited, code -9 / None, ~27 s in, during keystone alloc_passive); no output. No candidate comes from a sweep.
- validate_slate: 2 (round1, round2)

## (b) Names recalled from memory
Everything used resolved exact: classes, ascendancies (Titan, Invoker, Stormweaver, Infernalist, Amazon, Gemling Legionnaire, Shaman, Blood Mage), skills (Earthquake, Tempest Flurry, Ball Lightning, Flameblast, Whirlwind Lance, Siege Ballista, Fury of the Mountain, Bonestorm), bases (Crumbling Maul, Crackling Quarterstaff, Coursing Spear, Dyad Crossbow, Cruel Talisman, Conqueror Plate, Corsair Coat, Arcane Raiment, Devout Garb, Death Mantle), Chaos Inoculation, Doryani's Prototype. Notables were read from `search notable --ascendancy`, not recalled. Not resolved by me before use (only checked by the gate, all passed): Attuned Wand, Death Mail, Elegant Plate. Zero misses. No names were guessed from PoE1; I picked skills from the PoE2 skill listing.

## (c) Ideas dropped
- Gemling Legionnaire + Siege Ballista: Integrated Efficiency needs coloured connected supports in the spec; no cheap way to fix them, so replaced by Tactician (Cannons, Ready!), whose totem effect needs no supports.
- Acolyte of Chayula + Hand of Chayula, Warbringer armour break + slams, Shockwave Totem, Detonate Dead/corpse builds, Contagion: dropped to keep the slate at eight and avoid a second slam/chaos near-copy; corpse builds would need corpses_nearby, which a lone boss cannot sustain.
- Sweeps: dropped because the engine died on both attempts.
- Anything with a bow (user constraint); Lightning Arrow, Tornado Shot, etc. not considered.

## (d) Non-obvious candidates
- Tactician Ballista Battery: a crossbow totem build for Breach, with the player not firing; Tactician is usually thought of as a gun-attack class, and the totem-speed notable is the real engine.
- Shaman Bear Fissures: shapeshift Druid melee as a clearing tool; fissures spread randomly, so pack coverage is the premise.
- Amazon Whirlwind Lance: spear thrown for a collapsing whirlwind (control plus clear), with open-weakness damage; not the usual spear-melee pick.
- Infernalist Ignite Blast: ignite scaling by Bringer of Flame on a channel nova rather than a minion or Demon Form route.

## (e) Declared conditions
- Invoker Thunder Flurry: enemy_shocked. Source: the combo finisher "calls down a powerful Shocking bolt" (Tempest Flurry), plus lightning damage from the Invoker notable. Lone boss: only holds if the finisher lands, which is a repeated combo and so plausible on a boss but not every hit. Breach packs: holds once the finisher lands; weaker for fast clear since the finisher is every few uses. Not fully self-sustained; moderate risk of overstating.
- Stormweaver Shock Ball: enemy_shocked. Source: Shaper of Storms (all hit damage contributes to shock chance), with many small bolt hits. Boss: holds as hits are frequent (shock chance on a boss may be lower because of ailment thresholds, the engine may not model that). Packs: holds.
- Infernalist Ignite Blast: enemy_ignited. Source: Bringer of Flame (all damage contributes to ignite magnitude). Boss: depends on a hit actually landing and igniting; Flameblast releases rarely when charged long, so uptime on a boss is the weak point. Packs: holds after the first release.
- Others (Titan, Amazon, Tactician, Shaman, Blood Mage): none declared. Amazon's Open Weakness works on rares and uniques, so boss yes, normal Breach trash no (Breach rares yes); this is a skill effect not a declared condition. Whirlwind Lance would gain from frenzy charges but none declared since the build has no charge source chosen.

## (f) Friction
- `sweep` crashed twice (engine exited with code -9, then None), mid keystone allocation, so the sweep step was unusable; the error output is a raw traceback.
- `explain ascendancy` fails with non-JSON output; ascendancy passives only via `search notable --ascendancy` (which does carry text).
- The claim_number gate fired on the word "one" in an ordinary phrase ("one large area explosion"); fine but a reminder to avoid number words in prose.
- `search` output is large JSON; needs piping to filter.
- The `frozen/` directory in my output directory contained a final.yaml; I did not read it.
- Prompt says "key_pieces: keystone, notable, unique or support"; ascendancy notables work through kind notable, as the prompt says.
