<!-- Real engine run of examples/spark_golden.yaml (pin 601768b, 4 vCPU, 2m11s wall, --realloc-rounds 0). Sample only, not asserted by tests. -->
# Ranked report: Sorceress Stormweaver L90, Spark

- Objective metric: `FullDPS` (PoB output, one config profile `pinnacle_boss` for every variant). TotalDPS is one hit, so it would reward fewer projectiles; FullDPS is consistent across variants but an upper bound if hits do not overlap on one target.
- Engine: PoB-PoE2 pin `601768b`. Tiers: mid.
- Source of numbers: PoB calculations unless marked: `~` = price model estimate, `proxy` = benchmark density proxy, `ASSUMPTION` = owner-tunable constant, not game data. Variants and items are tool output, not advice.
- Preflight estimate: 1 seed(s) x 1 tier(s) x 2 slot(s), ~1,031 engine evals, ~2.3 min wall (rates: data/rates.yaml)

## Tier `mid`

| # | variant | FullDPS | vs best | EHP | Life / ES | min res | price | floors | arbiter_ash | breach_t15 |
|---|---|---:|---:|---:|---:|---|---|---|---|---|
| 1 | (no axes) | 30,726.0 | best | 1,584 | 1,554 / 0 | -24% (<75 uncapped) | ~no price: missing anchors weapon:mid, amulet:mid | NOT met | TTK 279.8s FAIL; survival n/a (named hits unsourced); EHP 1,584 incomplete | clear n/a; coverage 20% incomplete |

**1. (no axes)**: supports SupportRakiatasFlowPlayer, SupportAddedLightningDamagePlayer, SupportElementalFocusPlayer, SupportRapidCastingPlayerTwo, SupportDeliberationPlayer; tree +1516.2% (113 points); gear 9,648.8 -> 30,726.0 FullDPS, 658 engine evals.
  - weapon: DamageGainedAsLightning r1, WeaponSpellDamage r7, GlobalIncreaseLightningSpellSkillGemLevelWeapon r1, GlobalIncreaseSpellSkillGemLevelWeapon r2, Intelligence r1 [Acrid Wand]
  - amulet: AllResistances r1, FireResistance r1, LightningResistance r1 [Lapis Amulet]
  - note: floors not met (deficit 296); other slots (G7b) must cover the rest

Benchmark flags:

- arbiter_ash: FullDPS includes all-hits-landing and ailment/DoT: an upper bound
- arbiter_ash: named hits unsourced: survival not judged, generic PoB hit shown (generic_hits_to_die)
- arbiter_ash: incomplete: hits.phase2_sword_combo.physical, hits.phase2_sword_combo.fire
- breach_t15: density proxy only: no movement, monster movement, on-kill effects or ailment spread; no swarm survival in v1
- breach_t15: incomplete: monsters.magic.life_mult, monsters.rare.life_mult
- breach_t15: no AoE radius: projectiles treated as single-target, coverage = projectiles / monsters


## Across tiers

No axes: a single variant per tier, nothing to compare.

## Benchmarks

- `arbiter_ash` (boss, patch 0.5.2): Arbiter of Ash (pinnacle).
  - incomplete, unsourced inputs: hits.phase2_sword_combo.physical, hits.phase2_sword_combo.fire (metrics depending on them are n/a, never guessed)
  - ASSUMPTION constants (owner-tunable, not game data): gates.ttk_s_max, uptime
- `breach_t15` (pack, patch 0.5.2): Breach in a tier-15+ waystone (density proxy, not real seconds).
  - incomplete, unsourced inputs: monsters.magic.life_mult, monsters.rare.life_mult (metrics depending on them are n/a, never guessed)
  - ASSUMPTION constants (owner-tunable, not game data): gates.clear_s_max, monsters.magic.count, monsters.normal.count, monsters.rare.count, spread_radius_m

## Limitations and flags

- pure-DPS metric leaves boots/belt (and other stat-only slots) without damage affixes; survivability comes only from floors (G7b finding, not solved here)
- Outside the search: jewels, runes/soul cores and weapon-set passive points stay as in the seed (docs/pipeline.md section 4).
- Prices are a model estimate (`~`), not a market quote; see docs/price-tiers.md for the sample label.
- seed (no axes): 15 triggered-skill support(s) gated out (profile sets no trigger condition): Bone Shrapnel, Bursting Plague, Coursing Current, Electromagnetism, Elemental Discharge, Eonyr's Thunder, Fiery Death, Flame Pillar, Living Lightning, Living Lightning II, Mana Flare, Morrigan's Insight, Static Shocks, Trickster's Shard, Wind Wave
- seed (no axes): candidate caps: 100=8692.5094962857, 200=9648.8050628571, 400=9106.8624; kept 200
