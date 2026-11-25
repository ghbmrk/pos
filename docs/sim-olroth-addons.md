# Olroth's Conviction, Perpetual Charge, Crescendo and Volcanic Eruption in the Infernal Step sim

Extends [sim-oro-infernal-step.md](sim-oro-infernal-step.md) and [sim-hosts-infernal-step.md](sim-hosts-infernal-step.md)
with the add-ons from [census-1-0-unlocks.md](census-1-0-unlocks.md). Run: `python -m pos_pipeline.sim_oro --olroth`
(about 2-4 minutes on 4 cores). Units: x = a normal strike on a good rare 2H. All rows use Eclipse + 4 Shades that copy
afterimages, and the same defence columns as `--defence` (Witchhunter boss cooldown recovery 50% less at 0 Concentration,
mechanics every 15 s). The boss is sized about 10x larger than in the older host tables (`OL_SCALE = 100`), so fights span
many Echoing casts; **absolute numbers are not comparable with the older tables, only rows within this table are.**

## Skill text (poe2db, fetched 2026-11-25)

- Olroth's Conviction (lineage support, req. level 65): "Supported Skills Empower 2 additional Skill uses". Also "Gain 100%
  of Life and Mana Cost as Extra Runic Ward Cost". Allow type EmpowersOtherSkill, excluded IndeterminateEmpowermentAmount.
- Perpetual Charge: "25% chance to not remove Charges but still count as consuming them".
- Crescendo I: supports Strikes with a Final Strike; "Final Strike of Supported Skills can be performed twice in succession".
- Volcanic Eruption: triggers on Hit against Ignited enemies, 0 mana, 0.4 s cooldown, 4 Molten Projectiles, each 20% of
  default Attack Damage, 80% physical converted to fire, 1 m impact radius; supports melee Strikes "you use yourself".
- Infernal Step has no Final Strike (poe2db text), so **Crescendo cannot touch the main skill**. It only matters through
  Shadow Assault (Shade layer).

## How each option is modelled

| Option | Model | Assumption flagged |
|---|---|---|
| Olroth's Conviction | One Echoing cast empowers the cast use plus 2 more Infernal Step uses, each with the same afterimage count (Frenzy spent once). Two readings of the window: **window**: a follow-up use only counts if it starts within Echoing's 10 s Empower window; **free**: all three count. | Window semantics unknown; "once" vs "each use re-consumes Frenzy" is an `olroth_consume` switch (default once). The Runic Ward cost is not modelled. |
| Perpetual Charge | 25% of consumed Frenzy kept (expected value). | Expected value, not sampled. |
| Crescendo | Shade setup via Shadow Assault: 1.2 s a combo, +0.5 s for the second Final Strike, 2 Shades per combo instead of 1. Setup assumption: free (old baseline), once at fight start, or rebuilt before each Eclipse (Shade lifetime outside Eclipse is unpublished). | Combo time and Shade duration are estimates. Shade dash damage during setup ignored. |
| Volcanic Eruption | 0.4 s cooldown, 4 x 20% = 0.8 of a default hit, half the projectiles land on the boss, gets the Oro's per-flame extra fire and No Mercy, not Infernal Step's per-flame more, Echoing or Ambush. | Landing share, damage effectiveness vs Infernal Step's 227%, and that the boss is Ignited. |

## Ranking (measured, assumptions above)

Olroth's cells show: all three uses must start in Echoing's 10 s window / no window limit.

| Rank | Host + add-on | Weighted mean | Pre-ramped, holds | Cold, holds | Cap 5 | Cap 20 | No cancel | Mechanics faced/min | Hits eaten/min (no cancel) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Deadeye + Olroth's + Perpetual + Eruption + Crescendo | x32.5 / x33.6 | x172.8 / x178.3 | x100.3 | x52.1 | x423.9 / x432.0 | x191.6 / x198.4 | 4.0 | 3.8 |
| 2 | Witchhunter + Olroth's + Perpetual + Eruption + Crescendo | x32.3 / x33.3 | x179.5 / x183.9 | x102.5 | x53.4 | x454.2 / x463.5 | x190.8 / x197.5 | 2.4 | 2.5 |
| 3 | Deadeye + Olroth's + Perpetual Charge | x31.6 / x32.7 | x169.9 / x175.2 | x99.0 | x52.6 | x410.3 / x418.0 | x188.0 / x194.5 | 4.0 | 3.8 |
| 4 | Deadeye + Olroth's Conviction | x31.3 / x32.5 | x169.9 / x175.2 | x99.0 | x52.6 | x410.3 / x418.0 | x188.0 / x194.5 | 4.0 | 3.8 |
| 5 | Witchhunter + Olroth's + Perpetual Charge | x31.0 / x32.1 | x176.3 / x180.6 | x96.1 | x53.3 | x438.7 / x447.4 | x187.2 / x193.6 | 2.4 | 2.5 |
| 6 | Witchhunter + Olroth's Conviction | x30.7 / x32.0 | x176.3 / x180.6 | x96.1 | x53.3 | x438.7 / x447.4 | x187.2 / x193.6 | 2.4 | 2.5 |
| 7 | Deadeye + Crescendo (Shadow Assault) | x27.9 | x136.2 | x100.0 | x30.5 | x267.8 | x190.8 | 4.1 | 3.8 |
| 8 | Deadeye + Volcanic Eruption | x27.8 | x135.2 | x92.5 | x30.5 | x253.6 | x188.8 | 4.1 | 3.8 |
| 9 | Deadeye + Perpetual Charge | x27.4 | x135.2 | x92.3 | x30.1 | x253.6 | x188.0 | 4.1 | 3.8 |
| 10 | Deadeye Base (Echoing only) | x27.4 | x135.2 | x92.3 | x30.1 | x253.6 | x188.0 | 4.1 | 3.8 |
| 11 | Witchhunter + Volcanic Eruption | x26.5 | x117.1 | x87.6 | x28.1 | x256.0 | x188.0 | 2.7 | 2.5 |
| 12 | Witchhunter + Crescendo (Shadow Assault) | x26.4 | x116.9 | x94.4 | x26.3 | x251.9 | x189.9 | 2.7 | 2.5 |
| 13 | Witchhunter + Perpetual Charge | x25.9 | x116.5 | x87.5 | x25.6 | x254.5 | x187.2 | 2.7 | 2.5 |
| 14 | Witchhunter Base (Echoing only) | x25.9 | x116.5 | x87.5 | x25.6 | x254.5 | x187.2 | 2.7 | 2.5 |

Crescendo on Shadow Assault under each Shade-setup assumption (Witchhunter, 4 echo-copying Shades, pre-ramped, holds):

| Shade setup | No Crescendo | Crescendo | Gain |
|---|---|---|---|
| Free (old baseline) | x141.5 | x141.5 | +0.0% |
| Built once at fight start | x135.2 | x136.2 | +0.7% |
| Rebuilt before every Eclipse | x66.4 | x84.5 | +27.2% |


## Reading it

- **Olroth's Conviction is the only add-on that matters** and it is solid: pre-ramped holds x117 -> x176 on Witchhunter
  (+51%), cap 20 x255 -> x439 (+72%), weighted mean x25.9 -> x31-32 (+20-24%). Deadeye gets the same lift.
- **The window question matters only when uses run long.** With mechanics every 15 s and dodge-cancelling, uses are cut
  at about 7 s, so all three uses fit and window vs free differ by about 3%. With no cancelling a use runs about 14.5 s
  at 10 flames, longer than the window, so the extra uses are lost: Olroth's gives +0% (window) versus +3% (free). So
  the real gain depends on cancelling a use early, which is itself an unverified 1.0 behaviour. If uses cannot be
  cancelled and the window holds, skip Olroth's.
- **Perpetual Charge: zero.** Two Oro's refill Frenzy at 2/s, so 25% retention changes nothing. Drop it.
- **Volcanic Eruption: +0.5-2%** (weighted mean x25.9 -> x26.5 Witchhunter; pre-ramped x116.5 -> x117.1; none on Deadeye
  pre-ramped), a flat addition, as the census expected. Cheap but not a decision driver.
- **Crescendo: +1% if Shades are built once, +27% if Shades expire and are rebuilt each Eclipse** (x66 -> x85). Value hinges on
  unpublished Shade duration; it is a speed-up of rebuilds, not a multiplier.
- **Hosts:** Deadeye leads DPS slightly with Olroth's (x31.3 vs x30.7 mean) but Witchhunter faces 2.4 mechanics/min against
  4.0 and eats 2.5 hits/min against 3.8 when a use cannot be cancelled. Recommendation, not fact: Witchhunter stays the
  better host once defence is weighed; no add-on changes defence.
- Olroth's own cost (Life and Mana cost as extra Runic Ward cost) is a defence/resource unknown; Runic Ward is unmodelled.

## Not modelled

Runic Ward, Shade damage during setup, Eruption's real hit rate, per-use Frenzy re-consumption as default, any change to
defence from the add-ons themselves.
