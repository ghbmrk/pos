# Gear search (G7): weapon, body armour, amulet

`pos_pipeline/gear.py`; pipeline stage 3, gear row (docs/pipeline.md). G7b extends it to the other slots.

## API
- `GearSearcher(cat, pool, engine, metric=..., floors=..., shortlist=8, beam=2, roll=0.5, item_level=82, unique_prices=...)`
  `.search(seed_xml, tier, bases, slots=("weapon","body_armour","amulet"), passes=2, realloc_rounds=4) -> GearSearch`.
  `search_gear(...)` wraps both.
- `bases`: base type per slot (catalogue name, e.g. `{"weapon": "Acrid Wand"}`). Required: the weapon base is the
  spec's `weapon_base` axis (deferred to gear by the assembler), and body/amulet bases are a caller choice.
- `GearSearch`: chosen item per slot (affixes as group, pricing rank, mod id, points; or a unique and its band),
  final slot budgets, baseline (unmodded bases) and final metric, floor deficit, final stats and build XML,
  `PriceModel` estimate, eval counts, rejected (unparsed) mod ids, notes.
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

## Known weaknesses (judgement)
- Screening scores each group alone, so a group worth nothing alone but much in combination (crit multiplier with
  no crit chance) is dropped. Same order-sensitivity as the rest of the coordinate descent (docs/pipeline.md).
- Body armour gets no affixes for this spell seed: every spawnable body mod is defensive and the metric is damage.
  That is correct for a pure-DPS objective; defensive value needs floors or a defensive metric.
- Base choice (weapon type, armour type, amulet implicit) is an input, not searched.
- `item_level` 82 and `roll` 0.5 are assumptions; implicit values use the same roll.
- Mod families beyond `group` (e.g. two "+level" mods of different groups on one wand) are not restricted; PoB data
  has no family field in the dump, unverified whether the game forbids such pairs.
- Uniques are only considered when hand-priced in `data/unique_prices.yaml` (empty today).
