# Notes (counts approximate; stopped after Step 3, one gate round)

## (a) Tool calls by command
- render: 1
- search: ~38 (skill x7 ailment words, support x3, notable x4, keystone x2, unique x3, ascendancy x2, base x1, plus a few loops)
- resolve: ~60 (skill 16, class 5, ascendancy 6, support 7, base 6, skill 3 others)
- bridges: 7
- enablers: 1 (SkillConsumesBleeding)
- explain: ~30 (several failed: kind=ascendancy is not accepted)
- validate_slate: 1 (round1 only, 7/7 kept)
- sweep/preflight/run: 0

## (b) Recalled names and resolve result
- Viper Strike: none (suggestions all non-matching) -> dropped
- Caustic Arrow: none (suggested Gas Arrow) -> used Gas Arrow instead
- Cobra Lash: none -> dropped
- Wild Strike: none -> dropped
- Exact: Poisonburst Arrow, Gas Arrow, Lightning Arrow, Explosive Spear, Rake, Blood Hunt, Toxic Domain, Perfect Strike, Rolling Slam, Flicker Strike, Fangs of Frost, Rapid Assault, Gas Grenade, Primal Strikes
- Bases: Hardwood Spear, Crude Bow, Dyad Crossbow exact; Forked Bow none; Rampart Crossbow none (suggestions only)
- Most of my final names came from search, not memory.

## (c) Dropped
- Toxic Domain: tags Buff, likely no_metric; not tried at gate.
- Elemental Sundering: pulse itself deals no damage, depends on ailments from another skill.
- Rapid Assault, Fangs of Frost (parry/chill): too close to other spear candidates / weaker ailment theme.
- Perfect Strike, Lightning Arrow: no clear ailment engine found.
- Caster ailment ideas excluded by the user's constraint.

## (d) Non-obvious candidates
- Gas Cloud Ignite Bow: poison gas that detonates on Ignited enemies (cross-ailment engine from skill text).
- Plague Grenadier: grenade + Bursting Plague + Fiery Death; crossbow grenade ailment build is atypical.
- Shock Spirit Shaman: Druid melee shock via Primal Strikes spirits.
- Ignited Ground Spear: Flame Pillar converting Ignite from detonation-created ground.
Weaker diversity: Rake and Blood Hunt are both spear bleed (differ by class, defence, skill, keystone).

## (e) Procedure issues
- explain does not accept kind ascendancy/class, so ascendancy choices cannot be cited or checked for text; I picked ascendancies without reading them (no way to tell what Pathfinder/Deadeye actually grant).
- Notables/keystones in search output have id None; explain works by name, but the claim cite `id` convention (name for these, gem id for skills/supports) is only discoverable from CLI help.
- search takes text words only; skill/support results lack ailment-aware filtering, so I ran a text search per ailment. bridges returns entries with empty descriptions for notables/uniques (name only), requiring a follow-up explain.
- Output is verbose JSON; had to post-process with python for readability.
- Rule 3 number-word ban is easy to trip ("one", "single"); quotes containing digits are fine but not stated explicitly.
- `resolve` of a base printed name without spaces in my compact view only because I stripped whitespace; no actual problem.
- Unclear whether fixing a notable/support that duplicates another candidate counts toward near_duplicate; Firestarter is used by two candidates and gate accepted.
- Step 4 onward not run per instructions; ailment candidates' real viability (e.g. whether PoB models Plague Burst, Aggravated) untested.
