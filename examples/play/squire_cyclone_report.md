# Build report: Knight Squire + Cyclone

8 builds screened, 5 sim-verified improvements kept in 2 round(s) (stopped: rounds_done), 3 finalists on the full pipeline. Run time 28.2 min. Benchmarks: arbiter_ash; lower time is better. Tiers: mid.

> **ASSUMED:** Cyclone is absent from the pinned pre-1.0 data: Whirling Slash stands in (nearest whirlwind skill).

> **ASSUMED:** A Huntress stands in for the Duelist/Knight; the Squire is the assumed profile in data/squire_assumed.yaml (slots, effects, uptimes are assumptions, not game data). Redo on 1.0 data (K4).

## Results

### Tier mid

| rank | build | arbiter_ash | what it is |
|---|---|---|---|
| 1 | Debuff bot, no crit + Dance with Death + Surging Avatar | 1,526s (dies) | supports: -; no price: missing anchors weapon:mid |
| 2 | Ground painter, armour + Dance with Death | 1,812s (dies) | supports: -; no price: missing anchors weapon:mid |
| 3 | Own damage, stun immune + Dance with Death + The Catha's Balance | 4,446s (dies) | supports: -; no price: missing anchors weapon:mid, weapon:mid |

## How the ideas fared

| idea | origin | arbiter_ash | outcome |
|---|---|---|---|
| Ground painter, armour | llm (round 0) | 6,685s (dies) | superseded by Ground painter, armour + Dance with Death |
| Debuff bot, no crit | llm (round 0) | 6,943s (dies) | superseded by Debuff bot, no crit + Dance with Death |
| Own damage, stun immune | llm (round 0) | 6,685s (dies) | superseded by Own damage, stun immune + Dance with Death |
| Ground painter, armour + Dance with Death | sweep:keystone (round 1) | 5,348s (dies) | in the final pool |
| Own damage, stun immune + Dance with Death | sweep:keystone (round 1) | 5,348s (dies) | superseded by Own damage, stun immune + Dance with Death + The Catha's Balance |
| Debuff bot, no crit + Dance with Death | sweep:keystone (round 1) | 5,554s (dies) | superseded by Debuff bot, no crit + Dance with Death + Surging Avatar |
| Own damage, stun immune + Dance with Death + The Catha's Balance | sweep:ascendancy (round 2) | 4,446s (dies) | in the final pool |
| Debuff bot, no crit + Dance with Death + Surging Avatar | sweep:ascendancy (round 2) | 4,516s (dies) | in the final pool |

## Improvement rounds

Each row is one single change proposed from a finalist's own sweep and verified by the sim; kept only if the mean benchmark value improves by at least 2% and no survival check is lost.

| round | parent | change | sweep says | sim says | verdict |
|---|---|---|---|---|---|
| 1 | Ground painter, armour | + keystone Dance with Death | +25% DPS | +20.0% benchmark time | KEPT  |
| 1 | Own damage, stun immune | + keystone Dance with Death | +25% DPS | +20.0% benchmark time | KEPT  |
| 1 | Debuff bot, no crit | + keystone Dance with Death | +25% DPS | +20.0% benchmark time | KEPT  |
| 2 | Ground painter, armour + Dance with Death | - | - | - | no sweep pick above the threshold (or all flagged) |
| 2 | Own damage, stun immune + Dance with Death | + ascendancy The Catha's Balance | +20% DPS | +16.9% benchmark time | KEPT  |
| 2 | Debuff bot, no crit + Dance with Death | + ascendancy Surging Avatar | +23% DPS | +18.7% benchmark time | KEPT  |

The sweep predicts a DPS gain on the parent's build; the sim re-searches supports, tree and gear around the change and the benchmark decides, so a big sweep number can still lose.

## Does the core interaction compound? (Debuff bot, no crit + Dance with Death + Surging Avatar)

Tree key pieces Resolute Technique, Dance with Death, Surging Avatar: removing them together loses 17% of the damage; independent multiplicative effects would predict 20% (synergy -3%, verdict **overlaps**). The build without them is 1.20x weaker.
Owner principle: the core interaction should give huge scaling; a core worth under about 2x, or `independent`/`overlaps`, is a marginal build, not a compounding one.

| key piece | worth (metric share lost) | EHP share lost | verdict |
|---|---|---|---|
| keystone: Resolute Technique | -3.8% | 0.0% | not_load_bearing removing it RAISES the metric |
| keystone: Dance with Death | 19.9% | 0.0% | confirmed  |
| notable: Surging Avatar | 0.0% | 0.0% | possibly_unmodelled  |

### What limits the winner (calibrated probes)

```
metric HitAilmentDPS = 1,935; EHP 1,160; 15.0s
constraints (pressure = required/actual; > 1 violated):
  ttk@arbiter_ash: 25.44  TTK 1526s vs gate 60s   <- BINDING
  survive@arbiter_ash: 1.12  min hit margin 0.90 (need >= 1)
levers on ttk@arbiter_ash (relief per tier point; relief = share of the pressure removed):
  pen_fire           Damage Penetrates 10% Fire Resistance            relief +3.5%  cost 2.0  price 0.0174/pt
  pen_lightning      Damage Penetrates 10% Lightning Resistance       relief +0.0%  cost 2.0  price 0.0000/pt
  pen_cold           Damage Penetrates 10% Cold Resistance            relief +0.0%  cost 2.0  price 0.0000/pt
  life               +500 to maximum Life                             relief +0.0%  cost 4.0  price 0.0000/pt
  energy_shield      +500 to maximum Energy Shield                    relief +0.0%  cost 4.0  price 0.0000/pt
inert here (parsed, calibrated, no effect): inc_spell_damage, crit_chance, crit_damage, cast_speed, skill_level, added_fire, added_lightning
```

## Notes

- ranking basis: benchmark metrics only (boss time-to-kill with its survival check, pack clear proxy); a candidate missing a benchmark value ranks after those that have it. Per-skill DPS is shown but never ranks across archetypes.
- ablation measures the objective metric under the first benchmark's PoB options, not time-to-kill, and also TotalEHP: a piece is confirmed when removal costs either at least the threshold; a unique key piece is replaced by the best rare for its slot at the screen tier.
