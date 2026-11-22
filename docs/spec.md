# BuildSpec and validator (G3a)

Split of G3 (per `docs/pipeline.md`): **G3a** is this layer (schema, catalogue/compatibility validation, config profiles, metric mapping, limitation warnings). **G3b** (assembler, engine round trip, unparsed-mod detection, PoB code import) is separate and not built here.

Run: `python -m pos_pipeline validate spec.yaml` (exit 1 on errors). Library: `load_spec`, `validate(spec, catalogue)` -> `Report(issues, metric, metric_note, profile_hash)`.

## Schema
`pob_sha, class, ascendancy?, level, main_skill.gem, fixed.{supports,keystones,notables,uniques}, axes, tiers, config_profile, objective.{maximise,floors}`. Unknown keys and wrong types raise `SpecError`; game-data problems are `Issue`s (error or warning) with suggestions, never silent repairs. `main_skill.gem` and supports accept a catalogue id, gem_id or name.

## Checks
- pob_sha prefix (>= 7 hex) matches the catalogue; class, ascendancy-of-class, level range.
- Skill resolves and is not a support; fixed supports resolve, are not duplicated, share no `family`, and satisfy `can_support`. Supports that add skill types (`add_types`) are applied as an order-insensitive fixed point (permissive; PoB's own ordering is unchecked until G5).
- Socket limit: `data/rules.yaml` `max_supports` = 5, **unverified guess**, so exceeding it is a warning until G5 verifies it against PoB.
- Minion-tagged support on a non-minion skill: warning (the minion-only rule is not otherwise modelled).
- Fixed keystones/notables/uniques resolve (ambiguous names list candidates); ascendancy notables must match the spec's ascendancy or an ascendancy axis value; one unique per name.
- Axes limited to `ascendancy, main_skill, weapon_base` (`+` joins a weapon set; tokens match catalogue base `type`); tiers exist in `data/tiers.yaml`.
- `config_profile` exists in `data/config_profiles.yaml`; `Report.profile_hash` is the cache-key component. Profiles currently use only `enemyIsBoss` (the one option key exercised in engine tests); add keys after checking `list_config_options` on the pinned PoB.
- Objective: `maximise: auto` uses `data/metrics.yaml` (first rule matching the skill's types: minion and buff-only skills have **no** metric and fail with `no_metric` unless a PoB stat key is named; projectile skills use FullDPS; attack/spell/damage use TotalDPS). Floors: `resist_capped`, `attributes_met` (booleans) or a stat key with a number or `tier_default`.

## Limitations
`data/limitations.yaml` is hand-maintained and surfaces as `limitation` warnings carrying `confidence`: `verified` (Mana Tempest, minion damage; both confirmed in the engine wrapper) or `suspected` (Meta skills, passives that grant skills; generic heuristics, unconfirmed against PoB). Add entries as they are found; reports must show them.

## Not here (G3b)
Unparsed-mod-line detection, assembly to PoB XML, engine round trip, PoB code import.
