# Assumed-Squire what-if runs (K5)

Status: built 2026-11-22. Owner decision (card cmsg_01RxGYnd78N9kMbbAJ5pWDhUBKLQGf5LDJC5En4e4zFCdx): full what-if runs
with an assumed Squire are allowed before PoE2 1.0, clearly labelled, and redone on 1.0 data (K4).

**Nothing here is game data.** The Squire is not in the pinned data (601768b). `data/actors.yaml` keeps it `pending`; the
loud failure for ordinary specs is unchanged. The assumed profile is a separate file that only an explicit opt-in reads.

## Opt-in (two switches, both required)

1. The spec says so: `companion: { kind: squire, assumed: { scenario: <id>, uptime: <0-1, optional> }, skills: [...], gear: {...} }`.
2. The run says so: CLI `--assumed`, MCP `run(..., allow_assumed=true)`. Without it the run is refused before any work
   (`AssumedNotAllowed`); preflight needs neither.

```
python -m pos_pipeline run examples/squire_assumed_ground.yaml weapon='Akoyan Spear' --assumed --realloc-rounds 0 --out OUT
```
(about 1.5 min on 2 workers for one weapon slot each; the preflight estimate counts the Squire's slots too.)

## What the profile assumes (`data/squire_assumed.yaml`)

Every item is listed in the file and printed in every report: gear slots (weapon, body armour, helmet, gloves, boots),
one damage skill, effects from a named scenario at assumed uptimes, 25% of the tier budget before reallocation, a Squire
that is a copy of the player's class and level with its own gear and no passives, no Exposure (PoB counts it only when the
player can inflict it, docs/theorycraft-squire.md section 6). Each assumption names the 1.0 check (C1-C12) that replaces it.

| Scenario | Idea (theorycraft rank) | Effects (config options on the player's calc) |
|---|---|---|
| `debuff_bot` | 1: Squire keeps debuffs on the target | enemy Shocked, Intimidated, Armour Broken at 0.5 |
| `ground_painter` | 3, owner build 1 | whirlwind lightning pickup + enemy on Shocked ground at 0.5 |
| `charge_provider` | 9, owner build 2c | Frenzy and Power charges x3 at 0.6 |

Stand-ins, said in every report: Whirling Slash for Cyclone (it has the same `InteractsWithElementalGround` type and the
pickup config keys), any class for Duelist/Knight, any catalogue skill for the Squire's skills. Owner build 2 as written
(Elemental Discharge on Cyclone) cannot run: the support is Spell-only. `charge_provider` is its literal charge version.
Not covered: Presence projector (needs item text on the Squire), damage sponge (Squire survivability), Mark/consume skills.

`uptime` in the spec overrides every effect's uptime, so one scenario can be swept over uptimes by writing several specs.

## How a run works

K2 `SeparateBuildModel` (player build + effects as config, on/off blend by uptime, Squire as its own PoB build) and K3
`search_two_actors` (both gear sets in one tier budget, points reallocated across actors). While searching, the player's
build carries every assumed effect ON, which is an upper bound used only to choose gear; the tier value is then restored
to the player without effects, and the with-effects / companion / combined columns come from the actor stage (blended).
The Squire's own damage is its own build's metric on its searched gear, shown separately and in `combined`.

## Labelling and quarantine

- `report.md` opens with `# ASSUMED SQUIRE WHAT-IF`, the banner, scenario, every assumption, stand-ins and effects; tier
  headings and the with-effects columns say ASSUMED; the limitation line names the model.
- `run.json` `meta.assumed` holds all of that; `results.sqlite` has an `assumed` column on every `tier_runs` row (NULL =
  real data; else the scenario id) and an `ASSUMED` row in `meta`.
- Slates (ranked cross-archetype results) reject such a spec (`assumed_in_slate`): they never enter ranked slate output.
- MCP `list_runs` hides assumed runs unless `include_assumed=true` (reports how many are hidden); `compare` refuses them
  unless `include_assumed=true`; `get_report` leads with the banner. The `run` tool text tells clients to set the flag only
  when the owner asked for a what-if and to quote the banner.
- When the effects change the player's metric by 0 the report says the build has no consumer for them (not a model error).

## Probe findings (pinned PoB, plain Whirling Slash spear, pinnacle-boss config, TotalDPS 28.6 baseline)

`test_assumed_effects_move_a_probe_build` runs the gate check proposed in docs/theorycraft-squire.md section 6 on every
scenario effect: Shocked +20%, Intimidated +10%, Armour Broken x4.8 (physical spear, fully broken armour: large because the
probe is pure physical; read it as an upper bound), whirlwind lightning pickup and Shocked ground +20% (the same Shock:
combining them does not stack), Frenzy and Power charges 0 (no consumer on the probe: `needs_consumer`; the test fails if that
changes). No effect is silently gated off for these keys.

## Limits

- Effects do not depend on the Squire's skill or gear; a better Squire changes only its own damage and the budget split.
- Uptimes combine as independent on/off blends; overlapping effects (Shocked via two routes) are not de-duplicated.
- Preflight rates for the second gear set are the single-actor rates scaled by slot count (unmeasured for two lanes).

## At 1.0 (K4)

Fill `data/actors.yaml` from sourced data, flip the Squire to `available`, delete or retire `data/squire_assumed.yaml`, and
rerun every what-if. The assumptions' check ids (C1-C12) are the list of what to verify.
