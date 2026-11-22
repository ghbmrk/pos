# Ranked report: Sorceress Stormweaver L90, Spark

- Objective metric: `FullDPS` (PoB output, one config profile `pinnacle_boss` for every variant). FullDPS: upper bound
- Engine: PoB-PoE2 pin `601768b`. Tiers: starter, mid.
- Source of numbers: PoB calculations unless marked: `~` = price model estimate, `proxy` = benchmark density proxy, `ASSUMPTION` = owner-tunable constant, not game data. Variants and items are tool output, not advice.
- Preflight estimate: 2 seed(s) x 2 tier(s) x 2 slot(s), ~9,546 engine evals, ~7.4 min wall (rates: data/rates.yaml)

## Tier `starter`

| # | variant | FullDPS | vs best | EHP | Life / ES | min res | price | floors | arbiter_ash | breach_t15 |
|---|---|---:|---:|---:|---:|---|---|---|---|---|
| 1 | ascendancy=Chronomancer | 1,500.0 | best | 9,000 | 1,200 / 3,000 | 60% (<75 uncapped) | ~1.5 div, 12 samples, 2026-11-20 | NOT met | TTK 3799.2s FAIL; survival n/a (named hits unsourced); EHP 9,000 | clear n/a; coverage 100% incomplete |
| 2 | ascendancy=Stormweaver | 1,000.0 | -33.3% | 9,000 | 1,200 / 3,000 | 60% (<75 uncapped) | ~1.5 div, 12 samples, 2026-11-20 | NOT met | TTK 5698.7s FAIL; survival n/a (named hits unsourced); EHP 9,000 | clear n/a; coverage 100% incomplete |

**1. ascendancy=Chronomancer**: supports Chain, Fork; tree +50.0% (100 points); gear 10.0 -> 1,500.0 FullDPS, 700 engine evals.
  - weapon: Added Lightning r2 [Acrid Wand]
  - candidate mods rejected, PoB cannot parse: SomeUnparsedMod1
  - note: floors not met (deficit 30)

**2. ascendancy=Stormweaver**: supports Chain, Fork; tree +50.0% (100 points); gear 10.0 -> 1,000.0 FullDPS, 700 engine evals.
  - weapon: Added Lightning r2 [Acrid Wand]
  - candidate mods rejected, PoB cannot parse: SomeUnparsedMod1
  - note: floors not met (deficit 30)

Benchmark flags:

- arbiter_ash: FullDPS includes all-hits-landing and ailment/DoT: an upper bound
- arbiter_ash: named hits unsourced: survival not judged, generic PoB hit shown (generic_hits_to_die)
- breach_t15: density proxy only: no movement, monster movement, on-kill effects or ailment spread; no swarm survival in v1
- breach_t15: incomplete: monsters.magic.life_mult, monsters.rare.life_mult


## Tier `mid`

| # | variant | FullDPS | vs best | EHP | Life / ES | min res | price | floors | arbiter_ash | breach_t15 |
|---|---|---:|---:|---:|---:|---|---|---|---|---|
| 1 | ascendancy=Chronomancer | 75,000.0 | best | 9,000 | 1,200 / 3,000 | 60% (<75 uncapped) | ~1.5 div, 12 samples, 2026-11-20 | met | TTK 3799.2s FAIL; survival n/a (named hits unsourced); EHP 9,000 | clear n/a; coverage 100% incomplete |
| 2 | ascendancy=Stormweaver | 50,000.0 | -33.3% | 9,000 | 1,200 / 3,000 | 60% (<75 uncapped) | ~1.5 div, 12 samples, 2026-11-20 | met | TTK 5698.7s FAIL; survival n/a (named hits unsourced); EHP 9,000 | clear n/a; coverage 100% incomplete |

**1. ascendancy=Chronomancer**: supports Chain, Fork; tree +50.0% (100 points); gear 10.0 -> 75,000.0 FullDPS, 700 engine evals.
  - weapon: Added Lightning r2 [Acrid Wand]
  - candidate mods rejected, PoB cannot parse: SomeUnparsedMod1

**2. ascendancy=Stormweaver**: supports Chain, Fork; tree +50.0% (100 points); gear 10.0 -> 50,000.0 FullDPS, 700 engine evals.
  - weapon: Added Lightning r2 [Acrid Wand]
  - candidate mods rejected, PoB cannot parse: SomeUnparsedMod1

Benchmark flags:

- arbiter_ash: FullDPS includes all-hits-landing and ailment/DoT: an upper bound
- arbiter_ash: named hits unsourced: survival not judged, generic PoB hit shown (generic_hits_to_die)
- breach_t15: density proxy only: no movement, monster movement, on-kill effects or ailment spread; no swarm survival in v1
- breach_t15: incomplete: monsters.magic.life_mult, monsters.rare.life_mult


## Across tiers

Axis `ascendancy`: best FullDPS per value, by tier (winner in bold).

| tier | Chronomancer | Stormweaver |
|---|---:|---:|
| starter | **1,500.0** | 1,000.0 |
| mid | **75,000.0** | 50,000.0 |

## Benchmarks

- `arbiter_ash` (boss, patch 0.5.2): Arbiter of Ash (pinnacle).
  - ASSUMPTION constants (owner-tunable, not game data): gates.ttk_s_max, uptime
- `breach_t15` (pack, patch 0.5.2): Breach in a tier-15+ waystone (density proxy, not real seconds).
  - incomplete, unsourced inputs: monsters.magic.life_mult, monsters.rare.life_mult (metrics depending on them are n/a, never guessed)
  - ASSUMPTION constants (owner-tunable, not game data): gates.clear_s_max, monsters.magic.count, monsters.normal.count, monsters.rare.count, spread_radius_m

## Limitations and flags

- [suspected] example limitation
- pure-DPS metric leaves boots/belt (and other stat-only slots) without damage affixes; survivability comes only from floors (G7b finding, not solved here)
- Outside the search: jewels, runes/soul cores and weapon-set passive points stay as in the seed (docs/pipeline.md section 4).
- Prices are a model estimate (`~`), not a market quote; see docs/price-tiers.md for the sample label.
