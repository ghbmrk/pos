# Second actor per build: Knight's Squire (K1 design)

Status: K1 built (schema, registry, effect translation, loud stub); K2 built (separate_build model, companion assembly, orchestrator wiring, report columns; tested with a fake actor only). Approval: owner "Okay do it", 2026-11-22
(cmsg_01RxGYnd78N9kMbbAJ5pWDhU1rV7vhNcCUFrXzAenA5jNG) on the recommendation to model a second actor with its
own gear, own skills and cross-actor effects. Target builds: cmsg_01RxGYnd78N9kMbbAJ5pWDhU91siC64a4kvoveU2FoJ95E.

## What is known (2026-11-22)

| Fact | Source / check | Status |
|---|---|---|
| Knight is a Duelist ascendancy; Squire comes from "Summon Squire"; the player equips its weapons and armour and picks its skills; any melee weapon | poe-vault, mobalytics previews (Questions thread) | announced, not playable until PoE2 1.0 (2026-12-11) |
| Duelist class, Knight, Squire | pinned catalogue 601768b: no Duelist class at all | absent from current data |
| Squire gear slots, how its skills fire, which of its stats pass to the player, how it scales | no source | unknown |
| PoB support for Squire | no source; PoB models minions with own skills but not own gear | unknown, main risk |
| PoB config keys a companion's output can drive on the player's calc | `list_config_options` on pinned PoB (checked here) | verified: `use/override{Power,Frenzy,Endurance}Charges`, `conditionEnemyOn{Shocked,Chilled,Scorched,Brittle,Sapped,Consecrated,Profane,Fungal}Ground`, `conditionOn{Consecrated,...}Ground`, `bannerPlanted`, `companionInPresence`, `multiplierNearbyAlly` |
| Build 2 skill names | pinned catalogue | **Cyclone is not a PoE2 skill** (nearest: Whirling Slash, Whirling Assault). **Elemental Discharge is a PoE2 support**, but it supports Spells that Hit and consumes elemental *ailments*, not charges, and "cannot support the skills of Minions". As written, build 2 does not work on current data; re-check at 1.0 |

## Principle

The companion is a second actor with its own skills and gear. Everything that crosses from it to the player is an
**effect**: a named entry in `data/actor_effects.yaml` that maps to PoB config options (verified to exist on the
pinned PoB) plus an uptime. Which companion skill produces which effect comes only from `data/actors.yaml`
(sourced data), never from the spec or the LLM. Until an actor's data is sourced, it is `status: pending`, and
every entry point fails loudly (`actor_unavailable` validator error, `ActorUnavailable` exception) with the list
of unknowns. No number is ever produced for a pending actor.

## 1. BuildSpec extension

```yaml
companion:
  kind: squire                         # key in data/actors.yaml
  skills:                              # its own skill groups (catalogue skills + supports, same rules as main)
    - { gem: "Whirling Slash", supports: [] }
  gear: { weapon: "Spear" }            # base per companion slot; slot names come from the actor's gear_slots
```

One companion per spec (a list is not needed for any known mechanic). Structural errors raise `SpecError`;
everything else is a validator `Issue`:

| Code | Severity | Meaning |
|---|---|---|
| `actor_kind` | error | kind not in `data/actors.yaml` |
| `actor_unavailable` | error | actor is `pending`; message lists its unknowns |
| `actor_requires` | error | class/ascendancy does not grant this actor |
| `companion_skills` | error | more skills than the actor allows |
| `companion_slot` | error | gear slot not in the actor's `gear_slots` |
| `unresolved` / `support_incompatible` / ... | error | companion skills and supports get the same checks as the main skill |

## 2. Registry: `data/actors.yaml`

Per actor: `status` (pending | available), `requires` {class, ascendancy}, `unknowns` (what blocks it),
`model` (`native_pob` | `separate_build`, see 3), `gear_slots`, `max_skills`, `skill_effects` {skill id ->
[{effect, uptime, source}]}, `budget_share` (see 5). Squire is `pending` with every 1.0-dependent field null.

## 3. How cross-actor effects enter PoB calcs

Two models behind one interface (`pos_pipeline.actors.ActorModel.evaluate(main_xml, companion_xml, effects)`):

- **native_pob**: if PoB 1.0 models the Squire as a minion/companion with its own gear, the companion goes into
  the main build and PoB computes everything. Preferred; nothing to approximate. Decided at 1.0 by reading
  PoB's Squire code, not assumed.
- **separate_build** (fallback): the companion is assembled as its own PoB build (its gear, its skills) to read
  its own numbers (its damage, its attack rate, ailment chance). Its effects on the player are applied to the
  main build as config options. Effects with uptime < 1 are evaluated on and off and blended linearly
  (`blend`); the report marks blended numbers.

Effects merge with the spec's config profile; two effects (or an effect and the profile) setting the same key
to different values is an error, never a silent override. Combined damage = main metric (with effects) +
companion's own metric when the companion deals damage, reported separately as well as summed.

## 4. Assembler

`assemble` is unchanged for the main build. A companion assembler (K2) builds the `separate_build` XML through the
same engine calls; under `native_pob` it adds the companion to the main build. Both go through the existing
round-trip checks.

K2 as built: `actors.SeparateBuildModel` (player metric callable, optional companion metric callable) evaluates effects off
once and the effects on over every on/off combination of the partial-uptime effects (independent uptimes, at most 4;
more is an error); effect options are reset to the config profile value (else off) between evaluations. `assemble_companion`
builds the companion as its own build (one skill group; more is an error until K4). `Stages.actor(xml, variant)` runs
per tier after the gear stage; `TierRun.actor` carries main / companion / total / without_companion / effects / blended.
`run()` raises `ActorUnavailable` for a pending actor before any work, and when a companion is declared without an actor
stage. The tier's search value is still the player's metric without effects (K3 changes the search score).

## 5. Gear search over two gear sets in one tier budget

The tier budget stays the build's total (the owner's question is what a given amount of currency buys).
Companion slots join the slot list under a namespace (`squire.weapon`). Default allocation: main shares scaled by
`1 - budget_share`, companion slots share `budget_share` (from `data/actors.yaml`, set at 1.0). The existing
reallocation step then moves points across both actors, so the search decides whether a point is worth more on
the Squire or on the player. Score = combined metric after effects. Floors (res, attributes) apply to the
player only unless the actor can die (unknown).

## 6. Report columns

Per variant: `metric (with effects)`, `companion metric`, `combined`, `effects` (id x uptime, blended flag),
`gear points main / companion`, plus a limitation line naming the actor model used. Effect-off baseline
(`metric without companion`) shows what the second actor is worth.

## 7. Tasks

| Id | Scope | Depends on 1.0 | Model |
|---|---|---|---|
| K1 | this doc; spec `companion`; validator; `data/actors.yaml` (squire pending); `data/actor_effects.yaml` (keys verified on pinned PoB); `pos_pipeline/actors.py` (effects, merge, blend, pending stub); tests | no | done |
| K2 | companion assembly (`separate_build`), orchestrator wiring (effects into config, on/off blend, combined metric), report columns; tested with a test-only fake actor | no | Sonnet |
| K3 | two-gear-set search: namespaced slots, budget split, realloc across actors | no | Sonnet |
| K4 | at 1.0 (2026-12-11, after re-pin): source Squire facts (PoB code + game data), choose `native_pob` vs `separate_build`, fill `actors.yaml`, flip to `available`; re-check build 1 and 2 skill names | yes | Opus |
| K5 | ideation: slate fields and sweeps over companion skills | after K4 | Sonnet |

## Open question (not blocking)

Pre-1.0 "what-if" runs (spec-declared, clearly labelled assumed effects, for example "Squire keeps 3 power charges
up") would let the owner explore before 11 Dec, at the cost of numbers that rest on assumptions. Not built;
it needs an owner decision.
