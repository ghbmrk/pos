# Squire value channels: joint search (assumed Squire)

Status: run 2026-11-23 on pinned data 601768b. Owner ask: "Go" (cmsg_01RxGYnd78N9kMbbAJ5pWDhUN7wzu4E7SYKFBWbaaEgsw3) on
the proposal to encode the Squire's value channels as assumed options and search player and Squire jointly. Goal framing
(owner, cmsg_01RxGYnd78N9kMbbAJ5pWDhU3UqpJDyDdWYH8toSJQsZAx): highest DPS that survives all endgame content, with the
Squire and Cyclone as added constraints; only compounding ideas are worth keeping.

**Everything about the Squire here is ASSUMED** (docs/squire-assumed.md). Redo at 1.0 (K4).

## Channels

From DPS = sum over actors of hit x crit x rate x enemy-side multipliers, a second actor adds value only by:

1. its own damage (`own_damage`, the reference row);
2. enemy-side multipliers (`res_lightning`, `res_all_zero`, `debuff_bot`);
3. ally buffs through its Presence (`ally_buffer`);
4. enabling states the player cashes in (`stun_enabler`, `ground_painter`);
5. survival that frees player slots (`damage_sponge`);

plus `presence_stack` (2 + 3 + a shocking skill). Item lines are quoted in `data/squire_assumed.yaml`; the Squire wearing
them, its Presence (owner assumption, C3) and every uptime are assumptions.

## How to run

```
tools/squire_channels.sh OUT 4          # 9 runs, about 3 min each on 4 workers
python tools/squire_channels.py OUT     # the table below
```
Specs: `examples/squire_channels/*.yaml` (Huntress L90, Whirling Slash for Cyclone and for the Squire's one skill, mid tier,
player searches weapon, body, helmet, gloves, boots; the Squire searches weapon, gloves, boots).

## Results (mid tier, HitAilmentDPS vs PoB Pinnacle boss, enemy elemental resistance 50%)

| Scenario | Player alone | Player with effects | Squire own | Combined | x own_damage | EHP on / off |
|---|---|---|---|---|---|---|
| presence_stack | 680 | 1,429 | 1,073 | 2,502 | 1.58 | 2,632 / 2,632 |
| res_all_zero | 690 | 1,346 | 1,073 | 2,419 | 1.53 | 2,632 / 2,632 |
| res_lightning | 680 | 1,232 | 1,073 | 2,305 | 1.45 | 2,632 / 2,632 |
| debuff_bot | 451 | 864 | 1,152 | 2,017 | 1.27 | 2,924 / 2,632 |
| ally_buffer | 690 | 878 | 1,073 | 1,950 | 1.23 | 2,632 / 2,632 |
| ground_painter | 433 | 498 | 1,152 | 1,650 | 1.04 | 2,632 / 2,632 |
| damage_sponge | 433 | 433 | 1,152 | 1,585 | 1.00 | 3,309 / 2,632 |
| own_damage | 433 | 433 | 1,152 | 1,585 | 1.00 | 2,632 / 2,632 |
| stun_enabler | 433 | 433 | 1,152 | 1,585 | 1.00 | 2,632 / 2,632 |

"Player alone" differs by scenario because the gear search scores the player with every effect on (it moves to
elemental gear when resistance effects exist). Every build fails survival (0.6 generic hits to die; Arbiter TTK in the
thousands of seconds): the stand-in builds are weak, so read the ratios, not the absolute numbers.

## Reading

- Every channel is bounded: resistances reach a floor, increased-damage stacks are additive, a second actor's own damage
  at most doubles the total. Best measured: x1.58 combined. None compounds.
- Heavy Stun has no consumer in a searched build without Heavy Stun payoffs (Trephina is a mace; Cyclone needs swords,
  poe2db). Damage sharing moves EHP (+26%), not DPS, and costs the player's helmet (Starkonja's Head), which the search
  does not charge.
- Ground painting is dominated by The Taming (player ring: Wind skills count as boosted by Ignited, Shocked and Chilled
  Ground, several at once); PoB parses neither The Taming nor Cyclone's "Gain 50% of damage as damage of the corresponding
  Type", so `ground_painter` uses Whirling Slash's whirlwind keys and understates Cyclone. Squire ground still matters for
  Catalysing Elements ("allied" surface) and to free a ring.
- The one coupling found that compounds is Cast on Critical Energy (per enemy Power x share of ailment threshold dealt):
  each enemy-side multiplier counts in both trigger rate and spell damage. PoB has no Energy model; next step.

## Engine changes in this PR

- Effects can carry PoB custom mod lines (`customMods`, text templates `{pct}`) and enemy resistance values; custom mod
  lines from several effects add up; resetting an enemy resistance re-applies the profile's boss tier.
- Bug fixed: `set_config` wrote custom mods only to `input.customMods`, which PoB ignores once a build saved with custom
  mods carries them as a block; an effect's "off" state silently kept them. The engine now writes the active config
  set's custom-mod block too (regression test `test_custom_mods_replace_and_clear_on_a_saved_build`).
- The actor stage records the player's EHP with every effect on and off (`actor.survival`).

## Meta-graft loop (owner: "loop on various squire builds until competitive with current meta", 2026-11-23)

The search above builds weak stand-ins (about 2.5k DPS, failing survival), so their ratios say little about endgame. The
loop instead starts from a strong exported build and changes only what a Knight changes: remove the build's ascendancy,
add the Squire's Presence gear and skill effects, add the Squire's own damage. `tools/meta_graft.py BUILD ...` does it
(pobb.in link, PoB code file or XML).

Reference: a Gemling Legionnaire export (https://pobb.in/3qVMEwZkvTTK, from a mobalytics endgame guide, patch 0.4; PoB's
main skill Magma Spray; Arbiter TTK 4.9 s, survives at 27 hits, EHP 93k). Forbidden Rites class share: Gemling
Legionnaire 32% (poe.ninja build index).

| Variant | Player | Squire own | Total | vs meta |
|---|---|---|---|---|
| meta (reference) | 1,082,664 | - | 1,082,664 | 100% |
| ascendancy removed | 812,414 | - | 812,414 | 75% |
| Squire own damage only | 812,414 | 98,488 | 910,902 | 84% |
| Calamity + Leer | 942,670 | 73,866 | 1,016,536 | 94% |
| Calamity + Leer + shock 0.5 | 1,036,937 | 73,866 | 1,110,803 | 103% |
| Perfidy + Leer + shock 0.5 | 1,036,818 | 73,866 | 1,110,684 | 103% |
| Calamity + shock 0.5 (no Leer) | 974,985 | 98,488 | 1,073,473 | 99% |

Assumptions that decide it: the Squire has a Presence (owner assumption); its gear is as good as the player's (a second
full gear set, double cost); Shock uptime 0.5; the Squire can use the build's skill (Magma Spray is probably not melee;
the Squire takes melee skills); Squire own damage = the build's gear minus jewellery with no passive tree, x1.15 (Knight
companion node), x0.75 with Leer Cast. Knight node text adds no player damage; the five Standards are unpublished
(upside). Gemling is worth x1.33 to this build; the Squire's Presence gear wins back x1.28. Survival unchanged.

Next iterations: more meta exports, attack and melee builds closer to Cyclone (needs swords, absent before 1.0).
