# Gear price tiers for rare items (S3)

Status: proposal for decision. Written 2026-11-22.

## What the tier has to do

The simulator tests build variants "at expected gear price points". Structurally that means one of two directions:

- **Tier -> gear constraints** (used by the variant generator): "at budget tier T, what gear may this variant assume?" This is the direction that drives search.
- **Gear -> price** (used for reporting): "this variant's gear costs about X divines."

The first is required; the second is nice to have. Any option that only gives the second must be inverted by search (find items whose modelled price fits the budget), which adds a solver on top of the engine.

## Facts that constrain the design

Checked 2026-11-22.

- **No legitimate bulk source for rare prices.** GGG has no documented trade API and has closed new app registration; the trade site's internal API is off-limits (ToS 7i). poe.ninja's supported endpoints cover currency and uniques only. See `docs/prior-art.md` (PR #1).
- **GGG Currency Exchange API** (documented, hourly, poe2 realm) and poe.ninja give currency and unique prices. Both hosts are blocked by this cloud environment's network policy today; live prices need either a policy change or a fetch from the owner's device.
- **PoB PoE2 mod data has tiers and levels but no spawn weights.** `src/Data/ModItem.lua` on `dev` (2,550 mods): every mod has `level`, `group`, `type`, and a `weightVal` that is only 0/1 eligibility (3,774 zeros, 3,322 ones, no other values). Real spawn weights live in GGG's data export (RePoE fork / poe2db), a second data dependency, and `repoe-fork.github.io` is blocked here.
- **1.0 launches 2026-12-11 with an economy reset.** For the first days there are no stable prices at all, and prices in divines inflate across any league.
- **PoE2 crafting is not "spam one orb".** Essences, omens and other deterministic or semi-deterministic methods mean naive "1 / P(roll)" overstates the cost of many target items; drops supply many mid rares far below craft cost.

## Options

### 1. Relative tier tables (hand-authored templates)

Each budget tier is a per-slot gear template written in **mod-tier ranks**, not numbers, e.g. "body armour, tier Mid: 4 build-relevant affixes, 2 of them in the top 3 tiers for their group, rest in top 6". Ranks resolve to concrete rolls from PoB's own `ModItem.lua` (`group` + `level`), so a template is game-data-correct by construction. Uniques are allowed by price band from poe.ninja/Exchange when available, by hand otherwise.

Suggested starting tiers (labels, not prices): Starter (self-found, ~0-1 div), Budget (~1-10 div), Mid (~10-50 div), High (~50-300 div), Mirror (uncapped). The divine ranges are documentation only; the template is the definition.

- Pros: answers tier -> gear directly (generator input, no solver); no rare price data needed; deterministic and reviewable; survives the economy reset; zero new data sources.
- Cons: subjective; cannot report "costs X div" with any accuracy; template quality depends on the author's market knowledge; one template per slot per tier to write (about 12 slots x 5 tiers, mostly shared rules).
- 1.0 path: re-pin PoB; ranks re-resolve against new mod data automatically. Rewrite only templates whose slot rules changed (new affix groups, new slots).
- Cost: small. A YAML file plus a resolver in the variant generator.

### 2. Craft-cost model (rarity from spawn weights)

Price ~= expected crafting cost: probability of hitting the target affix set (spawn weights, item level, prefix/suffix limits) times cost per attempt (currency prices from the Exchange), with known deterministic methods (essences, omens) as cheaper paths when they apply.

- Pros: grounded in game data plus live currency prices; produces a number; principled ranking of "which affix is expensive".
- Cons: needs GGG spawn weights (not in PoB, host blocked here); modelling the full PoE2 crafting toolbox is a large and patch-sensitive project; craft cost is an upper bound that ignores drop supply and meta demand, so error versus market price is unbounded in both directions and unmeasured; gives gear -> price only, so needs a solver for the generator.
- 1.0 path: new data export plus re-checking every crafting method rule after the patch notes. Highest maintenance of the four.
- Cost: large.

### 3. Hedonic regression on hand-collected samples

The owner (or a helper on the owner's device) copies listed items from the trade site in game (Ctrl+C item text) with their asking price into a samples file. Fit price ~ f(slot, base, affix group, tier rank) per slot.

- Pros: the only option measured against market prices; error is quantifiable.
- Cons: data-hungry (rough guess, not measured: a few hundred samples per slot per economy snapshot for a usable fit); manual collection is slow; asking prices are biased high; every league and the 1.0 reset invalidate the data; gear -> price only, needs a solver.
- 1.0 path: re-collect after the economy settles (weeks after launch).
- Cost: medium to build, ongoing manual labour.

### 4. Hybrid: Option 1 now, with cheap anchors and an upgrade slot (recommended)

Ship Option 1 as the definition of tiers. Attach to each (slot, tier) cell an optional **anchor price** in divines with a date, filled from a handful of owner samples (for example 3-5 per cell for the slots that dominate cost: weapon, body, amulet, rings) and from poe.ninja for uniques. Report variant cost as the sum of anchors with an explicit "estimate, anchored on N samples dated D" label. Keep a `PriceModel` interface (gear -> price) so Option 2 or 3 can replace anchors later without touching the generator.

- Pros: everything Option 1 has, plus a rough number that is honest about its sample size; the upgrade path is an interface, not a rewrite.
- Cons: anchors are coarse (one number per cell, not per item); still subjective at the template level.
- 1.0 path: templates as in Option 1 on launch day; anchors marked stale at the reset and refilled when prices settle.
- Cost: small, plus optional manual sampling.

## Comparison

| | 1 Tables | 2 Craft cost | 3 Regression | 4 Hybrid |
|---|---|---|---|---|
| Tier -> gear (generator) | direct | needs solver | needs solver | direct |
| Gear -> price (report) | no | yes, unvalidated | yes, measured | coarse, labelled |
| New data sources | none | spawn weights + currency | manual samples | optional samples + currency |
| Works on 1.0 day one | yes | partly (currency missing) | no | yes |
| Build cost | small | large | medium + labour | small |
| Patch maintenance | low | high | high (re-collect) | low |

## Recommendation

Judgement, not fact: **Option 4.**

Decision boundary: does the project need a **ranking of variants within a budget** (ordinal) or a **trustworthy price per variant** (cardinal, say within 30%)? Options 1 and 4 answer the ordinal question well and the cardinal one roughly. Only Option 3 can approach a measured cardinal answer, and without a legitimate bulk price source it stays expensive and short-lived. If cardinal accuracy becomes a hard requirement, the upgrade is to add Option 3 behind the `PriceModel` interface, not to start with Option 2, whose error versus market price cannot be measured without Option 3's data anyway.

Challenge to the goal's framing: "expected gear price points" implies a stable currency unit. Divine prices inflate during a league and reset at 1.0, so tiers defined by templates (with dated divine labels) are more durable than tiers defined by divine amounts.

## Next steps if Option 4 is chosen

1. `data/tiers.yaml`: tier names, per-slot rank templates, empty anchor fields.
2. Resolver: rank template -> concrete affix rolls from the pinned PoB `ModItem.lua` (depends on S2 engine re-pin).
3. `PriceModel` interface with an anchor-sum implementation and the "N samples, dated D" label.
4. Optional: price fetch for currency/uniques from the owner's device or after a network-policy change.
