# Notes (procedure p4)

Brief reading: benchmarks arbiter_ash + breach_t15, tier mid (defaults); all else open. User idea fixed neither class nor skill.

## (a) Tool calls (approximate, CLI)
resolve ~33, search ~14 (incl. 2 failed with invalid --text flag), enablers 2 (GeneratesCharges useful; InteractsWithElementalGround returned empty from my printing script, probably my parsing), bridges 7, explain ~17, validate_slate 1. No sweep, no engine.

## (b) Names recalled from memory
- Cyclone (skill): none (no suggestions). Dropped as main skill; substituted Whirling Slash / Spiral Volley / Wind Serpent's Fury as nearest spinning/whirlwind skills.
- Elemental Discharge (skill): none; suggestions were Elemental Surge/Storm/Sundering/Invocation/Conflux (irrelevant). Found via search that "ElementalDischarge" is a support family: Catalysing Elements triggers "Catalysing Discharge". Used that as the nearest.
- Invoker, Titan, Warbringer, Pathfinder, Deadeye, Stormweaver, Ritualist, Amazon, Tactician: exact. Classes Monk/Ranger/Warrior/Huntress/Witch/Druid: exact.
- Elemental Equilibrium keystone: exact (not used).
- unique "One with the Storm": none (suggestion Choir of the Storm); it is a notable, exact. Used as notable.
- base "Fine Bow": none (suggestions Twin Bow etc.); used Composite Bow (found via search). Wrapped Quarterstaff exact.

## (c) Dropped
- Charged Staff (power charge dump): buff-only, would be no_metric.
- Flicker Strike, Pinnacle of Power, Siphoning Strike: not pursued; Flicker too close to Falling Thunder, Pinnacle is buff.
- Elemental Equilibrium: not related to charges.
- Warrior/Titan/Warbringer melee: no charge link found.

## (d) Non-obvious
- Whirling Slash + Berek's Grip + Catalysing Elements: the ring makes Wind skills count as on Shocked Ground, so the support's discharge triggers with no real ground; found via bridges (Ground Surface / Elemental).
- Tornado and Eye of Winter as discharge hosts: spells that read ground surfaces; unusual vs. weapon spear idea.
- Wind Serpent's Fury with Perpetual Charge: charge dump that partly refunds charges.

## (e) Procedure issues
- The idea's two names do not exist in this data; procedure has no guidance for premise-level misses (user asks for a skill that is absent). I reinterpreted to nearest mechanics and should tell the user.
- search takes positional text only (docs/prompt say text=...); `--text` fails. Output is large JSON; needed a helper script to read it.
- explain id differs per kind (gem id for skills, name for uniques/notables); unique explain with spaces needs quoting. Resolve of a notable as unique fails with no hint it is a notable.
- bridges with multiword terms like "Elemental Discharge" returned nothing; terms seem matched against text only, not family names. The family name ElementalDischarge was only visible in the support's JSON.
- No way to find charge GENERATORS besides enablers(GeneratesCharges), which returned only two irrelevant supports; the "builds up charges" half of the idea could not be put into any spec (no key piece generating charges). Candidates rely on passive charge generation not modelled/claimed.
- Rule 3 (no digits) forbids quoting text that contains numbers; avoided those lines.
- Gate kept all 7 first round; the gate does not check that Perpetual Charge can sustain Spiral Volley (unclear if ConsumesCharges supports it).
- Four of seven candidates use Catalysing Elements (near-duplicates in key piece; gate did not flag).
