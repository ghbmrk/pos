# p1 notes

## (a) Tool-call counts (approx, CLI equivalents)
resolve 6 (5 bases + class), search ~14, explain ~40 (batched via helper scripts), bridges 8, enablers 2,
validate_spec 2, sweep 3 attempts (2 crashed, 1 ok), validate_slate 2 (rounds 1 and 2).

## (b) Names recalled from memory vs resolve
Resolution was mostly through search/explain, which return catalogue names, so little free recall. Recalled and then
confirmed via search/explain: Arc, Lightning Arrow, Galvanic Shards, Lightning Spear, Storm Wave, Falling Thunder, Ball
Lightning, Lightning Conduit, all ascendancies and notables used. Bases resolved exact: Barrier Quarterstaff, Composite
Bow, Bombard Crossbow, Akoyan Spear, Broad Spear (unused). No misses. Body armour bases (Full Plate, Arcane Raiment,
Altar Robe, Armoured Vest, Assassin Garb, Ancestral Mail, Hunting Coat) came from `search base --tag body_armour`, not resolve; the gate accepted them.
Not tried: Spell Totem (meta, probably no_metric). Mines/traps: no support exists in the data that makes a skill a mine/trap; delivery stays "self-cast".

## (c) Ideas dropped
- Warbringer + Shockwave Totem / Ancestral totems: Shockwave Totem is not lightning, Spell Totem is a meta/totem skill (likely no_metric), no totem-creating support found, so no totem delivery.
- Arc with Stormchain: Stormchain says "cannot themselves inflict Shock", which fights Shaper of Storms.
- Voltaic Grenade, Orb of Storms, Enervating Nova: more near-copies of existing spell/attack deliveries.
- Falling Thunder + power_charges condition: no sustained source found, so no charge condition declared.
- Original Shock-Locked Arc Weaver (Shaper of Storms + Shock Siphon + enemy_shocked): replaced in round 2 after the ascendancy sweep marked Shaper of Storms possibly_unmodelled and showed Constant Gale as a lead.

## Sweeps
probe1.yaml (Sorceress/Stormweaver/Arc), kind keystone: crashed twice (engine exited code=-9 in _tree_alloc; a broken tool, not my spec).
kind ascendancy (10 entries, FullDPS baseline 100.6): Constant Gale +15.1, Force of Will +15.1, Multiplying Squalls +2.0,
Tempest Caller +1.0, rest +0.0 (Shaper of Storms, Heavy Snows, Refracted Infusion, Shaper of Winter, Storm's Recollection,
Strike Twice flagged possibly_unmodelled). Candidate "Gale-Surge Arc Weaver" built from Constant Gale + Force of Will (source sweep:probe1/Constant Gale).

## (d) Non-obvious candidates
- Mana-Shield Orb Oracle: Druid/Oracle mana-before-life plus unlucky enemy damage on a Ball Lightning; defence from Mana, not life/ES/armour.
- Warded Crossbow Witchhunter: ascendancy trades armour/evasion for Sorcery Ward whose barrier also takes physical and chaos; crossbow chain lightning.
- Lich Lightning Conduit: Eternal Life (life frozen while ES) with a shock-synergy cone spell, ES as the only bar.
- Gale-Surge Arc Weaver: sweep lead, always-on Arcane Surge plus mana-first damage.
- Plated Thunder Titan: armour-applies-to-lightning stacked on boosted body armour, a "tank is the lightning answer" idea.
- Least obvious on offence: Evasion Arrow Pathfinder with elemental reduction from evasion.

## (e) Declared conditions
- Lich Conduit: enemy_shocked. Sustained by the fixed Shock support ("making it more likely to Shock"); skill text rewards shocked targets. Holds on a lone boss only if shock lands (shock chance is probabilistic, boss shock threshold may limit); in Breach packs it holds more easily from hits on many targets. Riskiest declaration.
- Round 1 Arc Weaver had enemy_shocked from Shaper of Storms; removed in round 2.
- All others: none declared (no charges, ground effects or recently clauses relied on). Invoker's shocked-ground chance and Amazon's surge were not declared.

## (f) Friction
- `sweep keystone` crashes the engine (code -9) on a 16GB box with other load; ascendancy sweep worked in 9 s.
- Prompt says `delivery` derives from the skill; there is no way to select trap/mine/totem, so those deliveries are unreachable in practice.
- Candidate name "Frozen-Life Conduit Lich" is a misnomer (Eternal Life); not changed because round 1 is frozen and rename would need a new round with no benefit.
- Gate kept all 8 in both rounds; Witchhunter damage type printed "unknown" and a limitation warning for a granted skill.
- `bridges` returns very thin results for defence+damage term pairs; most leads came from search of ascendancy notables.
