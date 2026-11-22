# p5 notes

## (a) Tool calls (approx, CLI)
- ideate render: 1
- search: 4 (keystone x2, skill x2 incl. one broken-pipe rerun, base x2)
- explain: ~13 (6 keystones, 3 skills + 5 skills by id, plus 2 extra)
- bridges: 6 (keystone name x term; all returned only the keystone itself, no cross-domain hits)
- resolve: ~55 (classes, ascendancies, skills, keystones, bases)
- enablers: 0
- validate (spec): 1; slate validate: 1 (round1 only)
- sweep: 1 attempt (failed), a second attempt was blocked by the harness permission classifier and not run

## (b) Names recalled from memory (resolve)
Exact: Warrior, Mercenary, Ranger, Huntress, Monk, Sorceress, Witch, Druid; Titan, Warbringer, Deadeye, Witchhunter, Invoker, Pathfinder, Blood Mage, Amazon, Ritualist, Stormweaver, Chronomancer, Infernalist, Lich, Tactician, Gemling Legionnaire; skills Boneshatter, Hammer of the Gods, Lightning Arrow, Rake, Killing Palm, Flameblast, Perfect Strike, Molten Blast, Icestorm, Hand of Chayula, Firestorm; keystones Resolute Technique, Dance with Death, Crimson Assault, Avatar of Fire, Heartstopper; bases Hunting Spear, Hardwood Spear, Sacrificial Mantle.
Suggestion: ascendancy "Smith" -> Smith of Kitava (not used); bases Advanced Quarterstaff, Ironwood Spear, Warm Bow, Ornate Mace, Sceptre -> suggestions, I took Hardwood Spear and used catalogue-listed bases instead.
Ambiguous: skill Spear Stab (two entries); not used.
None: keystones Perfect Agony, Iron Grip (PoE1 names), dropped.

## (c) Dropped
- Primal Hunger + Rampage/rage: "No Rage effect" removes the point of rage; no clear damage engine.
- Heartstopper, Vaal Pact, Eldritch Battery, Mind Over Matter, Iron Reflexes etc.: defensive keystones, metric is damage only.
- Ritual Cadence / Whispers of Doom / Conduit / Necromantic Talisman: minion, curse or buff based, no damage metric.
- Second Storm candidate (Icestorm): near duplicate of Firestorm.
- Perfect Agony / Iron Grip: do not exist in PoE2 catalogue.

## (d) Non-obvious candidates
- Crimson Assault + Rake: bleed keystone on a movement spear, boss stands still so aggravated bleed fits.
- Hollow Palm Technique + Killing Palm: unarmed, no weapon slot; gear search gets no weapon.
- Dance with Death + Perfect Strike: skill speed keystone on a channel attack (weak fit with channel, untested).
- Blackflame Covenant on Flameblast: fire-to-chaos conversion, unusual defence/resist profile.
- Wildsurge Incantation on Firestorm: keystone tied to Storm tag; Firestorm duration shortening may make it ill suited (untested).

## (e) Procedure problems
- Sweep: the CLI requires running from repo root; first probe (Warrior Titan Boneshatter, unsearched seed, no weapon) failed with "probe seed failed to evaluate" after 5 s and gave no hint why (likely no weapon on the assembled seed). The retry with a spell probe was denied by the permission classifier, so no sweep leads were obtained. Procedure should say sweep probes should be spells or have a weapon, and that a failed probe does not count as the used sweep.
- Step 1 never says to scan keystones; `search keystone` with no text lists all (~35) which is the best entry for this idea. bridges returned nothing useful for keystone names (only the keystone itself).
- Key quotes with digits ("50% more damage") are accepted though claims forbid digits; the rule's scope for quotes is ambiguous.
- Slate prints "melee/unknown" for Hammer of the Gods damage; unclear what it implies.
- Skill explain needs the id (FirestormPlayer), not the name; resolve gives it, but explain of a name fails ("not in catalogue"); procedure says explain(kind, name).
- Step 3 gate kept all 7 in round 1, so rounds 2 and 3 not used (round2/3 files not created). Gate checks only catalogue resolve and quote text, not whether the keystone interacts with the skill (e.g. Dance with Death on a channel, Wildsurge on a Sustained Duration spell).

## (f) Sweep wall time
Failed attempt: 5.1 s (no output beyond the traceback, saved in sweep.txt). No successful sweep.
