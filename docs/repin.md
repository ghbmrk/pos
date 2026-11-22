# Re-pin to PoE2 1.0 (G10)

PoE2 1.0 launches 2026-12-11. When PoB-PoE2 publishes 1.0 data, run:

```
tools/repin.sh <pob_sha> [--skip-tests] [--specs DIR]
```

Nothing is committed; review the working tree and report, then commit. Exit 0 means clean; 1 means engine tests failed or a saved spec fails; 2 means usage or setup problem.

| Step | What the script does |
|---|---|
| 1 | Bumps the submodule (refuses if it has local changes: zero-patch policy). If PoB's `Dockerfile` pins a different LuaJIT commit, rewrites `REF` in `tools/build_luajit.sh` and rebuilds. |
| 2 | `pytest pos_engine/tests` (includes the Fireball golden DPS; review shifts, do not update goldens blindly). Failure does not stop the later steps. |
| 3 | `python -m pos_catalogue export` writes `data/catalogue/<new7>.json`. The old catalogue stays, so specs pinned to it remain reproducible. |
| 4 | `python -m pos_repin report` writes `docs/repin/<new7>.md`. |

## Report contents
- **Catalogue diff** per kind (skills, supports, uniques, bases, classes, ascendancies, keystones, notables): added, removed, renamed (same id or node, new name: certain), possibly renamed (removed and added with similar name and same base: unconfirmed), and which fields changed.
- **Spec revalidation**: every `*.yaml` under `specs/` (override with `--specs`) is validated against the new catalogue with its `pob_sha` treated as the new pin, so only content problems show, with the validator's suggestions. Specs are never rewritten; fix them, then set `pob_sha`.
- **Tier table**: affix groups new in `ModItem.lua` with no premium-weight rule (priced at default 1.0), removed groups, premium rules that now match nothing, and every price anchor (economy reset makes all stale; anchors are only reported, not edited).

## Still manual
- Review golden value shifts, and unparsed-mod behaviour for new 1.0 content.
- Resample price anchors after launch.
- `Catalogue.load()` with several catalogues present picks the one matching the pinned submodule; callers wanting another pass `pob_sha`.

## Rehearsal (2026-11-22)
Run against the older PoB `a82a33b` (2026-06-13) as the "new" pin: LuaJIT pin change detected and rebuilt, 63/63 engine tests passed, catalogue exported, report produced (7 removed or renamed entries, 434 base changes). The rehearsal exposed that older PoB generated files read `local skills, mod = ...` instead of returning a function; `tools/export_catalogue.lua` now accepts both shapes. Expect 1.0 to need more such adjustments in the exporter's stubs; they show up as an export error, not silent drift.
