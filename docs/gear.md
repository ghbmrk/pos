# Gear search (G7, G7b): all slots

`pos_pipeline/gear.py`; pipeline stage 3, gear row (docs/pipeline.md). G7 built weapon, body armour and amulet; G7b added both rings, helmet, gloves, boots and belt.

## API
- `GearSearcher(cat, pool, engine, metric=..., floors=..., shortlist=8, beam=2, roll=0.5, item_level=82, unique_prices=...)`
  `.search(seed_xml, tier, bases, slots=<all of SLOTS>, passes=2, realloc_rounds=4) -> GearSearch`.
  `search_gear(...)` wraps both.
- `bases`: base type per slot (catalogue name, e.g. `{"weapon": "Acrid Wand"}`). Required: the weapon base is the
  spec's `weapon_base` axis (deferred to gear by the assembler), and body/amulet bases are a caller choice.
- `GearSearch`: chosen item per slot (affixes as group, pricing rank, mod id, points; or a unique and its band),
  final slot budgets, baseline (unmodded bases) and final metric, floor deficit, final stats and build XML,
  `PriceModel` estimate, eval counts, rejected (unparsed) mod ids, notes.
- Slots (`SLOTS`): `weapon, body_armour, amulet, ring_1, ring_2, helmet, gloves, boots, belt`. The tier table has one
  `ring` allocation "per build, split over both rings", so each ring slot gets half (`GearSearcher.slot_budget`). Pricing
  treats each ring as a `ring` item. `ring=Base` on the CLI sets both rings. Uniques are one per name across slots.
- `STANDARD_FLOORS`: resistance caps 75 and `Str/Dex/Int` vs `Req*`, for a build with every slot searched. PoB omits a
  `Req*` stat when the requirement is 0; floors read that as 0. Off-hand/second weapon is not searched.
- CLI: `python -m pos_pipeline gear spec.yaml TIER weapon="Acrid Wand" amulet="Absent Amulet" body_armour="Abyssal Cuirass"`.

## Method
1. **Affix options per base.** Mods from the pinned `ModItem.lua` that spawn on the base's tags (game rule: first
   weightKey present on the base decides), at or below `item_level`. Rank 1 = highest-level tier on that base;
   points = `TierTable.affix_points(group, rank)`. Per group only the best rank at each distinct point cost is kept
   (at most 4 options: the `rank_points` bands). Values are taken at `roll` within each range (0.5, PoB's default).
2. **Unparsed-line rejection.** Every option is checked with PoB `check_item` once; a mod with any unparsed line is
   excluded and listed in `rejected_unparsed`. Final items are checked again. Uniques with unparsed lines are skipped.
3. **One slot** (others fixed): screen each group alone at its best affordable rank in one batched `eval_items`
   call; keep the top `shortlist` groups that beat the unmodded base; then beam search (width `beam`) adding one
   (group, rank) per round within the slot budget, at most 3 prefixes and 3 suffixes, one mod per group, stopping
   when no extension beats its parent. Priced uniques (`data/unique_prices.yaml`) whose band fits are scored too.
4. **Coordinate descent** over the slots, up to `passes` passes or until no item changes.
5. **Budget reallocation** (capped tiers): starting from `default_allocation`, estimate each slot's best item at
   +/- 10% of the searched slots' total; move the step from the slot that loses least to the slot that gains most,
   re-run descent, keep only if the full build improves. Total points are conserved.
6. **Objective**: `(-floor deficit, metric)` compared lexicographically, so floors rank ahead of damage. Floors are
   `{stat: number | stat key}`, e.g. `{"FireResist": 75, "Int": "ReqInt"}`. Default: none, because three slots
   cannot carry full resistance caps at low tiers; G7b/G8 set floors over all slots.

Pricing: `AnchorSumModel` over the chosen items. Until anchors are sampled it returns points only ("no price:
missing anchors ...").

## Measured (4 vCPU, PoB `601768b`, Spark Stormweaver L90 seed, no other gear, FullDPS)

| Tier | FullDPS | Submitted evals (cache hits) | Time, 4 workers |
|---|---|---|---|
| budget | 88 -> 774 | 2,456 (1,477) | not timed (2 workers, CLI) |
| mid | 88 -> 1,651 | 3,244 (1,754) | 58 s |

About 1,000-1,500 engine evaluations per seed x tier for three slots; reallocation is most of it. The pipeline
estimate (600-900 for all eight slots) is about 3x low; G8a should budget roughly 500 per slot before G7b tunes
`shortlist`, `beam` and `realloc_rounds`.

## G7b measurement (4 vCPU, same Spark seed, FullDPS, `STANDARD_FLOORS`, all 9 slots)

| Tier | Realloc rounds | FullDPS | Submitted evals (cache hits) | Time | Floors |
|---|---|---|---|---|---|
| mid | 0 | 88 -> 865 | 1,920 (91) | 71 s | met |
| mid | 4 | 88 -> 1,045 | 6,517 (1,924) | 159 s | met |
| budget | 4 | 88 -> 509 | 5,013 (1,361) | 148 s | met |

About 210 engine evals per slot for descent alone and about 510 per slot with reallocation (4,600 engine evals for 9
slots), so the ~500 evals/slot planning figure holds for G8a. Reallocation costs 2 x slots `best_item` calls per round and
bought +21% FullDPS at mid, so it stays on by default; `realloc_rounds=0` is the cheap mode (about a third of the evals).
Reallocation moved only one step in each run (the rounds stop at the first non-improving move). Defaults for `shortlist`,
`beam`, `passes` were not changed: no run showed a failure mode that tuning would fix.
In these runs the floors were met at both tiers; with floors on, resistance and attribute affixes take most non-weapon
points, boots and belt took almost nothing (a DPS metric gives movement speed and life no value).

## Known weaknesses (judgement)
- Screening scores each group alone, so a group worth nothing alone but much in combination (crit multiplier with
  no crit chance) is dropped. Same order-sensitivity as the rest of the coordinate descent (docs/pipeline.md).
- Body armour gets no affixes for this spell seed: every spawnable body mod is defensive and the metric is damage.
  That is correct for a pure-DPS objective; defensive value needs floors or a defensive metric.
- Base choice (weapon type, armour type, amulet implicit) is an input, not searched.
- `item_level` 82 and `roll` 0.5 are assumptions; implicit values use the same roll.
- Mod families beyond `group` (e.g. two "+level" mods of different groups on one wand) are not restricted; PoB data
  has no family field in the dump, unverified whether the game forbids such pairs.
- Rings share one allocation and are searched independently, so two rings may end up with different budgets after reallocation.
- Uniques are only considered when hand-priced in `data/unique_prices.yaml` (empty today).
