# Sweep and ablate (I4)

`pos_pipeline/sweep.py`. Implements the engine half of `docs/ideation.md` step 1 (sweeps) and step 4 (ablation). Numbers come from the engine only; the LLM never supplies them.

## `sweep(cat, pool, xml, kind, metric, *, options, engine, skill_id, supports)`

One change at a time on a probe seed `xml`; result is a `Sweep` with `entries` ranked by delta (unevaluated last).

| kind | change | notes |
|---|---|---|
| `keystone` | allocate the keystone with its path | `points` = path cost from the engine; `unreachable` if the tree cannot reach it |
| `ascendancy` | allocate each notable of the seed's own ascendancy | other ascendancies are not swept (class swap resets allocations); separate 8-point pool, path cost not budget-checked |
| `unique:<slot>` | equip each catalogue unique of that slot kind via the `slot_item` fast path | uniques PoB cannot fully parse are `unparsed` and never scored (would be a silent zero) |
| `support` | ADD each eligible support to the current group | G5 eligibility; socket limit not enforced; current group read from the seed, or `supports=` |

Caveats: a keystone/notable delta includes the path nodes' own stats, not only the keystone (on an unsearched seed the paths overlap and many keystones show the same delta; sweep a tree-searched seed, and read `points`). `options` (a `set_config` mutation, e.g. a benchmark's `pob_options`) applies to keystone, ascendancy and support sweeps; unique sweeps use the seed's own config.

Flags (carried from G5): `audit_outlier` (delta above 3x baseline: check for an artefact before trusting), `possibly_unmodelled` (exactly zero delta on an entry that has effect text: an engine gap, not a dud), `no_effect` (zero delta, no text; supports have no catalogue text until I2), `unreachable`, `over_budget`, `unparsed`, `failed`.

## Probe weapon (I12)

The probe seed has no gear, so an attack main skill computes 0 damage. `equip_probe_weapon(cat, engine, xml, base)` puts a plain, unmodded catalogue weapon base (implicits only) in Weapon 1; errors on an unknown or non-weapon base. Job/CLI/MCP: `--weapon BASE` / `sweep ... --weapon BASE` / `sweep(..., weapon=BASE)`; it is applied before the supports and tree search. The job checks the seed's metric first and exits 1 with a hint when it is 0 (attack skill without weapon, or a weapon the skill cannot use). Checked: Boneshatter keystone sweep baseline 0 without weapon, 66 HitAilmentDPS with a plain mace; Falling Thunder needs a quarterstaff (0 unarmed).

## `ablate(cat, pool, xml, key_pieces, metric, *, ..., threshold=0.10)`

Per key piece `{kind, id[, slot]}`: remove it and re-measure.

- `keystone`, `notable`: deallocated. A piece that is not allocated in the build is `not_testable`.
- `support`: replaced by the best other eligible support, or left empty if that is better (`replacement` says which).
- `unique`: needs `slot`; unequipped. The ideation design wants the slot's best rare as the replacement; that needs the gear search and belongs to the slate runner (I5), so the verdict here is an upper bound on the unique's worth.

Verdicts: `confirmed` (removal costs at least `threshold`, default 10%, to move to `data/ideation.yaml` in I3), `not_load_bearing` (note says if removal RAISES the metric), `possibly_unmodelled` (zero delta and the piece has effect text), `not_testable` (reason in `note`). A bad piece is recorded, not raised.

## CLI

```
python -m pos_pipeline sweep spec.yaml KIND [workers] [top]
python -m pos_pipeline ablate spec.yaml notable:Name keystone:Name support:Name unique:Name@slot
```
Both use the assembled, unsearched seed of the spec's first variant; use the library with a searched seed for real slates.

## Measured (Spark L90, assembled seed, FullDPS, 4 vCPU, 4 workers)

| sweep | entries | wall |
|---|---|---|
| keystone | 33 | 22 s (path-cost probes run serially on one engine) |
| ascendancy (Stormweaver) | 10 | 9.7 s |
| `unique:weapon` | 61 (33 unparsed, 1 failed) | 7 s |
| support | 221 | 20 s |

Whole sweep set for one probe seed: about 1 min, so the ideation plan of at most 2 probe seeds per slate costs about 2 min. Ablation is 1-3 short evals per piece (support: one per eligible support, about 20 s).
