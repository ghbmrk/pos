# Assembler (G3b)

Library: `pos_pipeline.assemble`. CLI: `python -m pos_pipeline assemble spec.yaml [out_dir]` (validates, then builds one seed per axis combination and writes `seed_N.xml`) and `python -m pos_pipeline import code.pobcode` (PoB code -> spec YAML). Neither depends on the MCP-vs-embedded-API interface decision: both are library calls the MCP server will wrap.

## assemble(spec, catalogue, engine, variant) -> Assembled
`variants(spec)` is the cartesian product of the axes. `assemble` applies `ascendancy` and `main_skill` axis values; `weapon_base` is reported in `deferred_axes` (gear placement belongs to the gear search, G7). Steps: `new_build`, `set_class`, `set_level`, `paste_skill` (main skill + fixed supports, level 20), `alloc_passive` per fixed keystone/notable (catalogue node id), fixed uniques equipped from PoB's own unique database (`unique_text`, real mods), config profile via `set_config`. Result: PoB's own XML, stats, issues.

## Round-trip checks (engine `check_build`)
| Code | Severity | Meaning |
|---|---|---|
| `no_main_skill`, `main_skill_mismatch` | error | PoB resolved no / a different main skill |
| `unrecognised_gem`, `supports_missing` | error | a gem PoB did not recognise; fewer supports socketed than the spec lists |
| `passive_missing`, `level`, `ascendancy` | error | build does not match the spec |
| `pob_warning` | error for `socketLimitWarning`, else warning | PoB's own item/socket warnings from the last calc |
| `unparsed_mod` | warning | an equipped item has a mod line PoB cannot parse (it contributes nothing) |
| `zero_dps` | warning | seed computes 0 DPS (normal for attack skills before a weapon is placed) |

## Unparsed mod lines
`unparsed_lines(engine, raw)` (engine method `check_item`) parses an item without equipping it and returns lines PoB kept with `extra` set (Classes/Item.lua `modLine.extra`), excluding "Grants Skill" lines. Gear search (G7) must reject any candidate with a non-empty result. Fixed uniques with unparsed lines are kept but warned, because the user asked for them. Measured on the pinned PoB: `Ab Aeterno` has 4 unparsed lines (Dodge Roll, Overencumbrance, sprint slow immunity, movement-speed-per-roll), so real uniques do hit this; the report must list them. Caveat: `extra` can swallow neighbouring tokens (a fully unknown line also corrupts adjacent known text in the same `extra` string), so only the line is reliable, not the leftover text.

## import_pob
Decodes a PoB code/XML and builds a spec: class, ascendancy, level, main skill + supports (first group), allocated keystones/notables (incl. ascendancy), equipped uniques. Non-unique gear, other socket groups, jewels and tree layout are dropped and listed as `import_dropped` warnings; the tree is re-searched, not copied. Names not in the catalogue are dropped with a warning.

## Verified here
- Socket limit 5: PoB `Modules/CalcSetup.lua` raises `socketLimitWarning` when a group has more than 5 non-hidden supports; it only warns, the calc still runs. `data/rules.yaml` now has `verified: true`, so exceeding 5 is a validator **error**. Lineage-support exceptions are not modelled.
- Corrected (B3, 2026-11-22): PoB's `enemyIsBoss` default is Pinnacle (`defaultIndex = 3`), so an empty option set equals `pinnacle_boss`. Profile `none` now sets `enemyIsBoss: None` (unresisted normal enemy); `pob_default` is the empty option set.
