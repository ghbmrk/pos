# Adversarial 1.0 scaling search (PvP against the devs)

Date: 2026-11-25. Owner asks: cmsg_01RxGYnd78N9kMbbAJ5pWDhUB3CPkA1msYvj2SebvyRxyw ("PvP theorycrafting vs the devs ... scale beyond what they intend") and cmsg_01RxGYnd78N9kMbbAJ5pWDhUGV6G9sEvmdWsVuBts7tGuZ ("path dependent on a narrow range of skills").

Frame: every strong mechanic has a brake the devs put on it (a cap, a cooldown, a "you use yourself" clause, a cost, a hit count). A finding counts only if a 1.0 piece (or an old piece made reachable by 1.0) removes or bypasses that brake. Synergies that work as written score low even when strong.

Blindness: the ranking in sections 1-4 was written before reading any earlier pass in `docs/`. The project memory index was injected into this session's context at start, so earlier lead names were visible; the method below (scripted scan plus forced family coverage) is what stood in for blindness. Section 5 compares only after the ranking was fixed.

## 1. Method

Corpus: pinned catalogue `data/catalogue/601768b.json` (399 skills, 567 supports, 435 uniques, 1,193 notables incl. ascendancy, 33 keystones) plus the 105 public 1.0 entries in `tools/census/new_1_0.json`, re-checked against poe2db `Conquerors_of_Wraeclast_gems` / `_uniques` on 2026-11-25 (no new names). Numbers below come from poe2db 1.0 pages fetched today (Hollow Focus, Ako's Answer, Fan the Flames, Blade Vortex, Whirling Blades, Ethereal Knives, Tempest Bell, Siege of Sands, Liminal Coil, keyword page) and from PoB data (`Uhtred's Constellation`, penetration floor).

Exploit primitives (scripted in `tools/adversarial/scan.py`, run `python3 tools/adversarial/scan.py out.json`):

| id | primitive | what breaks a brake |
|---|---|---|
| P1 | uncapped per-X | "per N X" with no cap on the line |
| P2 | count-as without spend | "count as", "as though", "does not consume" |
| P3 | cost and payoff in different units | a currency whose drawback is not on the spend path |
| P4 | non-damage stat to damage | life/armour/power/darkness turned into damage |
| P5 | recursion / copies | triggers, mirages, shockwaves, copies |
| P6 | snapshot / per-use | stages, empower, "revived recently", stored values |
| P7 | guard phrases | used to find siblings that lack the guard |

The scan tagged 1,506 rule lines across 60 families. Triage read every P1/P2/P4 line (457 unique), every ascendancy notable, every keystone and all 105 1.0 entries, then asked per family: what is the brake, and does a 1.0 piece break it.

## 2. Brakes that held (guards found, so rejected)

These were the obvious exploit doors; each is closed in current text.

- Blade Vortex: "Blades cannot inflict or Extract Impale", max 50 blades, 5 hits each. No impale loop.
- Impale: max 60 on a target; each hit extracts only the strongest. No stacking bank.
- Fan the Flames: triggered explosion has 0.10 s cooldown, 5 uses. Caps at ~10 explosions/s.
- Armour break below 0 (Warbringer Imploding Impacts): capped by the enemy's base Armour.
- Penetration floors at 0 resistance (PoB `CalcOffence.lua:467`), so "per Glory skill" pen (Call Upon the Deep) and Windripper's infinite pen stop at 0.
- Glory: once per 0.5 s per monster per skill; no gain while the skill is active.
- Galvanising Blades 5 blades; Lightless Stalker 12 Foul Eyes; Vampirism, Impaling Blade II, Rending Blade "Strikes you use yourself"; Ancestral Boost "Triggered Skills cannot be Ancestrally Boosted".
- Ako's Answer: "Bells you create are Immune to Elemental Ailments" removes Tempest Bell's ailment bonus (a guard inside the exploit, see F1).
- Liminal Coil: curses ignore the limit but have zero magnitude (0.5 engine; 1.0 adds only Whispers as one more curse).

## 3. Family coverage (forced, before ranking; at most 2 finalists per family)

"None" means the family was checked and no 1.0 brake-break was found in public text.

| family | finalist(s) or result |
|---|---|
| Warrior: Titan / Warbringer / Smith | none: slam payoffs carry "you use yourself"; armour-below-0 capped. Kaom's Roots (Mountain's Wake 531% while moving) is a designed pressure economy |
| Ranger: Deadeye / Pathfinder | none new; Pathfinder double poison count only feeds Pestilent Volley pack spread |
| Huntress: Amazon / Ritualist / Spirit Walker | none: Amazon "on consume a Charge" triggers fire once per consume; tamed unique beasts unquantified |
| Mercenary: Tactician / Witchhunter / Gemling | none: banner Glory is per banner; pen floors at 0 |
| Monk: Martial Artist | **F1 Ako's Answer x Hollow Focus bells** |
| Monk: Invoker / Acolyte | Acolyte max Darkness feeds F2 (see F2 caveat) |
| Sorceress: Stormweaver / Chronomancer / Varashta | F9 (Stormweaver +2 elemental limit on Ashcaller spirits, if spirits are elemental) |
| Witch: Infernalist / Blood Mage / Lich / Abyssal Lich | none: Demon Magus "cost paid by you" into Pyromantic Pact is a small Flame feed; Abyssal Lich has no notables in data |
| Druid: Oracle / Shaman | **F4** (Shaman rage regen feeds Blood Rage) |
| Duelist (1.0) | **F3 Siege of Sands x Uhtred's Constellation**; F6 Fan the Flames on Cyclone |
| Shadow (1.0) | **F2 Whirling Blades quadratic in Darkness**; F8 Detonate from Stealth |
| Knight (1.0) | none until Dec 4 text: Glory 1/2 s and "Empowered +20%" are linear |
| mace | Kaom's Roots (above); Molten Forge anvil: designed |
| sword | F3, F6 |
| axe / flail / crossbow / talisman | none: no 1.0 piece touches them |
| dagger | F2, F8 |
| spear | none new (Tasalio's per-Power scaling is linear in Power) |
| bow | none: Windripper's infinite pen floors at 0 |
| quarterstaff | F1 |
| wand / staff / sceptre | F9 (wand); F5 (sceptre/staff minions) |
| fire spells | F9 Ashcaller per-spirit Ancestral Boost |
| cold / lightning / chaos / physical spells | none: Elemental Penetration support is linear; Soul Extraction consumes Decay linearly |
| minions / companions / totems | **F5 Bunkerbuster revive cycle x From the Icy Brink**; Hand of Weeping Black zombies (designed, x3.5 per zombie, limit 10); totems none |
| ignite | F6 (Radiant Grief gives permanent ignite to arm Fan the Flames); Tear Through Reality non-hit ignite: designed |
| bleed / Blood Loss | F10 Blood Loss into Rending Dash (x1.7 on physical DoT) |
| poison | none: Pestilent Volley spread is pack-only |
| freeze / shock / electrocute | none: Electrocution Trap electrocute-on-extract is CC, boss immunity unknown |
| impale | none: guards in section 2 |
| curses / marks | none new (Liminal Coil +1 curse from Whispers) |
| heralds / auras / buffs | F11 Grim Bargain fed by always-crit bells (rides on F1) |
| warcries | none: Intimidate endurance bypass plus Flare is linear in endurance supply |
| charges / resources | **F4 Primal Hunger x Blood Rage**; F7 Uhtred's Constellation x cooldown flood |
| defence | none beyond intent. Best designed: Duplicity (one full hit avoided per channel, fails on Heavy Stun) and F1's crushing-blow shockwaves as boss lock |
| on-death / corpse | none: Engulf/Combust/Volatile are per-death; Blade Vortex corpse impales are clear-only |

## 4. Ranking (fixed before comparison)

Estimates are from text, not engine runs. "Ceiling" is the multiplier on the host skill's single-target damage if the reading holds; p is the subjective chance the reading holds at 1.0.

| # | finding | brake broken | ceiling | p | why it beats the devs |
|---|---|---|---|---|---|
| 1 | F1 Ako's Answer x Hollow Focus | 1-hit bell lifespan | x8-15 | 0.35 | ascendancy bells sized as single-use always-crit pops become permanent |
| 2 | F2 Whirling Blades x Darkness | projectile count has no cap | x4.75 at 30 Darkness, x24 at 100, unbounded | 0.5 | one scalar (Darkness) multiplies twice |
| 3 | F7 + F3 Uhtred's Constellation x 1.0 cooldown flood, on Siege of Sands | "more per different cooldown skill" has no cap | x2.2 generic; x3-9 on Siege of Sands | 0.8 / 0.4 | Shadow and Duelist add ~15 cooldown skills to a support sized for 3-5 |
| 4 | F4 Primal Hunger x Blood Rage | "No Rage effect" drawback is not on the spend path | enabler: 4-5 Frenzy per 8.7 s | 0.6 | keystone's cost disappears when Rage is spent as currency |
| 5 | F5 Bunkerbuster + Siegebreaker x From the Icy Brink | "Revived Recently" meant as a post-death window | x1.5-2 minion damage, freeze lock | 0.5 | revival becomes a controllable cycle |
| 6 | F6 Fan the Flames on Cyclone with Radiant Grief | none fully (0.1 s guard holds) | x2-3 single target, more in packs | 0.6 | ignite precondition made free; mostly as designed |
| 7 | F8 Detonate from Stealth | one Stealth spend, N Ambushes | x1.9 per trap at 30 Darkness (19-38 traps) | 0.7 | stated in text, so partly intended; scales with F2's Darkness |
| 8 | F9 Ashcaller per-spirit Ancestral Boost | per-spirit, cap unknown | x1.3-1.6 | 0.3 | spirit limit unpublished |
| 9 | F10 Blood Loss into Rending Dash | accumulates all physical DoT | x1.7 on physical DoT | 0.6 | linear, bounded |

### F1 Ako's Answer x Hollow Focus (Martial Artist, quarterstaff)

Text: Hollow Focus (Martial Artist ascendancy skill) spawns a bell every 2-3 s within 3 m, limit 3, 21 s duration. "Your Hits immediately destroy the bells, creating a shockwave" at 237% attack damage (L20), crushing blow, "Hits against them are always Critical Hits", per-bell shockwave cooldown 0.1 s. Ako's Answer (1.0): "Skills which create Bells have +2 to Limit"; "Hits with this weapon do not count towards the number of Hits Bells take to destroy".

Brake: the bell is a one-hit pop. Break: if "immediately destroy" is a 1-hit counter, Ako's makes each bell persist for its 21 s, and the limit rises to 5. Every swing that covers the boss and the bells then adds 5 shockwaves. With a strike of ~200% attack damage: 200% + 5 x 237% = 1,385%, x6.9; Tempest Bell (also +2 limit, 10-hit counter removed for weapon hits, 6 s) adds more shockwaves, so x8-15. Side effects: 5 guaranteed crits per swing for on-crit triggers (Hollow Resonance, F11), crushing-blow shockwaves heavy-stun primed bosses (defence by lockdown).

Tests at 1.0: (a) Hollow Focus bells destroyed by hit count, not by a flag; (b) Ako's "+2 limit" applies to an ascendancy skill; (c) shockwave reaches the boss (2.3 m) from bell spawn (3 m from you); (d) Culling Strike must be absent (bells can be Culled).

### F2 Whirling Blades x Darkness (Shadow, dagger)

Text: "Fires 20 projectiles. Fires 1 additional projectile for each Darkness spent when Ambushing. 35% more projectiles while Dual Wielding. Multiple knives can hit the same target." Ambush: "3% more damage per Darkness" expended.

Brake: Darkness max (30 by default). The projectile clause has no cap, so damage per throw goes as (20 + D) x (1 + 0.03 D): x4.75 at D = 30, x24 at D = 100, x160 at D = 300, versus a non-Ambush throw. Eclipse makes every attack count as Ambushing at maximum Darkness. Raising D needs either the 1.0 Shadow tree or ascendancy (unpublished until Dec 4) or Acolyte's Darkness pool (100 + 10 per level, +1% per 1% chaos resistance) if that is the same resource.

Tests at 1.0: fraction of the spiral that hits one boss; whether Acolyte Darkness is spendable by Ambush; Shadow max-Darkness nodes.

### F3 + F7 Uhtred's Constellation x the 1.0 cooldown flood

PoB data: `support_uhtred_damage_+%_final_per_different_cooldown_skill_in_last_8_seconds = 8`, +2 cooldown uses, 50% less cooldown speed; no cap. 1.0 adds about 15 cooldown skills (8 traps, Contingency Plan, Shroud, Whispers, Intimidate, Echoing Strikes, Rending Dash, Blade Conduit, Siege of Sands, Tear Through Reality, Molten Forge). Fifteen distinct in 8 s gives 1 + 0.08 x 15 = x2.2 on the supported skill. Host: Siege of Sands (Elysium; 9 stages; Sand Mirages at 974% attack damage each; 5 s cooldown) gets 3 uses per 10 s instead of 1 per 5 s. If mirage count equals stages, one use is 468% + 9 x 974% = 9,234%, x3-9 against a normal sword strike over time.

Tests: mirage count per stage; Elysium-granted skill accepts supports; whether traps thrown count as "used" for the 8 s window.

### F4 Primal Hunger x Blood Rage

Text: Primal Hunger "100% more Maximum Rage; Regenerate 1 Rage per second per 4 Rage spent Recently; No Rage effect". Blood Rage (1.0): "consume all your current Rage to gain Frenzy Charges; 5% Surpassing chance per Rage consumed", 8.7 s cooldown. Shaman Furious Wellspring regenerates 6% of max Rage per second and +7 max Rage.

Brake: Primal Hunger's cost is "No Rage effect", but Blood Rage spends Rage as a currency, not as an effect. 80-100 Rage gives 400-500% Surpassing, 4-5 Frenzy Charges per cast. Value depends on the Frenzy consumer (Duelist Bloodied Blade, Sand Scour, Echoing Strikes).

Test: whether "No Rage effect" blocks Blood Rage's conversion.

### F5 Bunkerbuster + Siegebreaker x From the Icy Brink

Text: Siegebreaker (1.0) grants Bunkerbuster (3 uses / 4 s; consumes the closest reviving minion for an explosion of 12.2% of its max life as fire) and "-1.5 seconds to Minion Revival timer when you cast Bunkerbuster". From the Icy Brink (1.0): reviving minions that "have Revived Recently" get 200% more Freeze buildup, 100% physical converted to cold, 40% gained as extra cold.

Brake: "Revived Recently" is a short window after an uncontrolled death. Break: Bunkerbuster kills on demand and shortens revival, so three minions can be kept inside the window permanently, and each kill is itself an explosion. x1.5-2 minion damage plus freeze lock.

Tests: Bunkerbuster death counts as a death for revival; From the Icy Brink applies to the Demon Magus meta minion.

### F6, F8-F10 (short)

- F6: Fan the Flames triggers on Wind skill hits against Ignited enemies; Radiant Grief ignites everything in Presence, so Cyclone (330% base attack speed) fires the 0.1 s / 5-use explosion at its cap. Guard holds; strong on packs.
- F8: Detonate from Stealth makes all trap detonations count as Ambushing and gain Darkness damage; traps carry 19 uses across 8 gems, doubled by Contingency Plan.
- F9: Ashcaller boosts the next 3 Fire Spells after each Fire Infusion; Ancestral Boost (30% more) gets 20% increased effect per Spirit of Ngamahu. The spirit skill text is not on poe2db yet.
- F10: Blood Loss accumulates all physical DoT taken; Rending Dash converts 70% of it to life loss. Linear.

### Best combined shape (to sim once 1.0 data exists)

Martial Artist quarterstaff: Ako's Answer + Hollow Focus + Tempest Bell for the shockwave multiplier (F1); Grim Bargain turns the five guaranteed crits per swing into 25+ Darkness per swing (F11), which builds Eclipse Glory and keeps every attack at max-Darkness Ambush. That stacks F1 (x8-15) with the Ambush multiplier (x1.9 at 30 Darkness) on one swing; Uhtred's (F7) on a cooldown host adds x2. Survival: crushing-blow shockwaves lock primed bosses; quarterstaff block 12-18%.

## 5. Comparison with earlier passes (written after the ranking was committed)

Checked by grepping every earlier doc in `docs/` for each finding's key names.

| finding | in earlier passes? | verdict |
|---|---|---|
| F1 Ako's Answer x Hollow Focus | Ako's appears only with Tempest Bell, rejected as "printed on purpose" (`unplanned-1-0-first-principles.md`). Hollow Focus appears nowhere | **new**: the exploit is the ascendancy bell, not the Tempest Bell |
| F7 Uhtred's Constellation x cooldown flood | not mentioned | **new** |
| F4 Primal Hunger x Blood Rage | Primal Hunger only with Abyssus, rejected on "No Rage effect" (`novel-1-0-interactions.md`). Blood Rage never | **new**: spend path avoids the effect clause |
| F5 Bunkerbuster x From the Icy Brink | Bunkerbuster listed as 12.2% minion-life damage only; From the Icy Brink never | **new**: revival as a controlled cycle |
| F9 Ashcaller per-spirit boost | not mentioned | **new** (low, text incomplete) |
| F2 Whirling Blades x Darkness | Darkness pool lead with Whirling Blades (`unlocked-by-1-0.md`, `unplanned-1-0-rerun.md`, x60 per hit) | **seen**; the quadratic projectile term is a refinement, same scalar the owner judged as designed |
| F3 Siege of Sands | listed as designed burst (`off-intent-scaling-1-0.md`) | **seen**; only the Uhtred's host pairing is new |
| F6 Fan the Flames | in `off-intent-scaling-1-0.md` and the Oro build | **seen** |
| F8 Detonate from Stealth | owner judged Darkness/Detonate Ambush as designed | **seen** |
| F10 Blood Loss into Rending Dash | first pass, x3.3 at p 0.1 | **seen** |

Net new against earlier passes: F1, F7, F4, F5 (and F9 as a stub). None of the four use Shades, Eclipse, Echoing Strikes or Infernal Step. The top new lead (F1) is a Monk build, a class earlier passes did not reach.

Next steps: F1 tests (a)-(d) are the first thing to check when 1.0 data lands (Dec 4 text, Dec 12 repin). F7 is checkable now in PoB once a cooldown-heavy spec exists; it needs no 1.0 text beyond the skills already public.

## 6. Owner verdict and loop search (2026-11-25, after merge request)

Owner (cmsg_01RxGYnd78N9kMbbAJ5pWDhUQrB3qBV3oegeSKkPeykEQQ): "These are all obvious/intended and don't scale that well." Accepted: F1-F10 are bounded multipliers (x2-15), not runaway scaling.

What scales without bound is a feedback loop: X produces Y, Y produces more X, with gain above 1 and no cap. `tools/adversarial/loops.py` builds a quantity graph from every rule line (36 quantity nodes; generic flows such as hits, kills, crits, mana and life excluded, `LOOPS_GENERIC=1` keeps them) and lists cycles of length 2-3.

Result: 23 cycles touch a 1.0 entry and 42 exist in all public text (`LOOPS_ALL=1`). After triage:
- Every 1.0 cycle with possible gain above 1 runs through Darkness / Stealth / Glory (Eclipse, Conceal, Duplicity, Whirling Blades). The owner already judged that family as designed.
- The rest are parser artefacts (one skill's own setup and payoff, e.g. Echoing Strikes, Abiding Hex, Walking Calamity) or cross-skill links with gain below 1 (Hand of Weeping Black zombies, From the Icy Brink, Freezing Trap fragments).

Conclusion: public 1.0 text (105 entries, no 1.0 ascendancy, tree or keystone text) contains no new loop with gain above 1. The loop finder is the tool to rerun on the Dec 4 text and the Dec 12 data, where the new ascendancies and keystones land.

## 7. Term-driven avenues (owner: "use words in skill description", cmsg_01RxGYnd78N9kMbbAJ5pWDhUP2WXocPFuQgJbPGBdyPyno)

Method: `tools/adversarial/terms.py` pulls every capitalised or linked mechanic term from the 105 public 1.0 entries (Hazard, Detonator, Limit, Parried, Perfect Timing, Final Strike, Reviving Minions, Ice Crystals, Spread, Activate, Shrine and so on), then lists every old rule line in the pinned game that uses the same word. Run `python3 tools/adversarial/terms.py 40`. Each term was read for one question: does a 1.0 skill make the term cheap or plentiful, while an old line pays off per instance with no cap?

### The one avenue that can run away: Hazard rearm x traps x Detonate

- 1.0: all eight Shadow traps are tagged **Hazard**. Detonate triggers every placed trap at once and has no cost or cooldown on its page.
- Old Hazard lines (sized for the Huntress Spearfield): Rearm II support "Hazards ... have a chance to be rearmed a short duration after triggering" (30%, PoB `hazard_rearm_%_chance`), Efficient Contraptions notable 15%, one small node 5%. Current total 50%.
- Structure: every Detonate removes a fraction (1 - p) of the traps on the ground. If traps are thrown at rate T and Detonate is cast at rate D, the number of traps on the ground settles at N = T / ((1 - p) D), and damage per second is D x N x (trap damage) = T x trap damage / (1 - p). That is geometric in p: x2 at 50%, x5 at 80%, x10 at 90%. **At 100% a rearmed trap is never used up**, so N grows with every throw until trap duration (or an unpublished trap limit) stops it. Every detonation also counts as an Ambush with Darkness when Detonate is used from Stealth.
- Brake: the rearm total. The current game reaches 50%, and the 1.0 Shadow tree and ascendancies (text on Dec 4) are where more would come from. A trap limit or rearm cap would also close it.
- Tests: rearm applies to traps triggered by Detonate; rearm chance caps below 100%; trap limit and duration; whether a rearmed trap re-arms again (chained) or only once.

### Avenues read and bounded

| term | 1.0 source | old payoff | why bounded |
|---|---|---|---|
| Limit | Shades (limit 3), Raise Zombie (10), Foul Eyes (12), Bells | Overabundance I/II, Idol of Uldurn +1, Stormweaver +2 elemental | each adds a fixed count |
| Detonator | Fire Trap, Poison Trap, Pestilent Volley | Gas Arrow, Decompose, Gas Grenade, Stormblast Bolts, Explosive Spear | each cloud or bolt detonates once |
| Spread / Ignited Ground | Concussive Trap spreads Ignite as ground | Beira's Anguish ground ignites as 500% of max Life; Flamewalker; Desert's Scorn | ignite from life is fixed per flask use |
| Parried | Shattering Parry, Engage, Bloodied Blade, Riptide | Dunkelhalt +50% magnitude, four notables +15-25%, Nocturne | consumed by the next hit |
| Final Strike | Perforate, Shadow Assault | Crescendo I/II (twice), III (Ancestral Boost) | x2 |
| Perfect Timing | Perfect Squall | Perfection 4 x 5%, Window of Opportunity, Assailum | fixed window and stacks |
| Reviving Minions | From the Icy Brink | Sacrifice (minions as corpses), Crazed Minions, Muster | per revive |
| Ice Crystals | Fangs of Agnar (10,118-life walls) | Verglas, Crystalline Shards, Vruun's Aftermath, Eventide Petals | per crystal destroyed |
| Empowered | Intimidate, Viper Strike, Whispers | The Empty Roar, Bolstering Yell, Tireless | flat increased damage |
| Surpassing | Blood Rage | Way of the Mountain | linear in Rage |
| Shrine | Knight Valour | Hammer of Faith | one buff at a time |
