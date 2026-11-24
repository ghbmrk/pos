# Oro's Infernal Step: simulation with and without its assumptions

Owner ask: cmsg_01RxGYnd78N9kMbbAJ5pWDhUVqtjhLTM9WPsoges58fAVF ("run a sim against this build with and without its
various assumptions"). The build is in [build-oro-infernal-step.md](build-oro-infernal-step.md).

**Everything here is an estimate.** The PoB engine can't run this build. Oro's Sacrifice, Infernal Step, Sacrificial
Flame, Echoing Strikes and Eclipse are 1.0 content. Witchhunter's Concentration lines are unparsed in the pinned 0.5
data. So `pos_pipeline/sim_oro.py` is a separate time-step simulation of a boss fight, built from the tooltip numbers.
Each unverified rule is a switch. Re-run it with `python -m pos_pipeline.sim_oro [--json rows.json]`.

## What the sim models

**Facts it uses** (poe2db 1.0 tooltips, PoB ModCache text):
- Infernal Step: 2+3F strikes, 49% weapon speed, additional strikes 113% faster, 15% more per flame.
- Oro's: 1.51 APS, 12% extra fire per flame, 1 Frenzy per second at max flames.
- Echoing Strikes: 12.8 s cooldown, 0.8 s cast, 2 + Frenzy afterimages at 50% less damage.
- Ambush: 3% per Darkness, with 30 max Darkness and Grim Bargain's ×1.1 consumption. Grim Bargain gives +5 Darkness
  per crit.
- No Mercy: up to 40% more by missing Concentration. Concentration is 30% of the boss's life, is broken 1:1 by damage,
  and regenerates after 5 s without loss.

**Build** (the doc's recommended setup):
- Two Oro's via Giant's Blood, Witchhunter, Echoing Strikes and Eclipse.
- 8 max Frenzy, 50% increased attack speed, 10% crit.

**Fight:**
- A must-dodge mechanic every 15 s.
- A 60 s boss and a 180 s boss.
- Boss life is fixed, sized at 10× a plain rare build's DPS × the fight length.

**Policy.** For each scenario the sim tries 48 play patterns and keeps the fastest kill:
- whether to save Echoing for capped uses
- how long to wait for its cooldown
- whether to cancel ramp uses early
- whether to hold an Empowered use until after the next mechanic

**Assumptions switched**, with the subjective probability (an estimate) used for weighting:

| Switch | Values (probability) |
|---|---|
| Sacrificial Flame cap | 5 (0.3), 10 (0.4), 20 (0.3) |
| Flame decay | none (0.6), all expire 8 s after last gain (0.4) |
| Pre-ramp: flames and Frenzy can be built before the boss | yes (0.5), no (0.5) |
| Two Oro's per-flame lines both apply | yes (0.6), no (0.4) |
| Echoing afterimages | replay the whole use (0.5), first strike only (0.35), can't empower Infernal Step (0.15) |
| Eclipse Ambush persists across the use | yes (0.7), no: only strikes inside Eclipse's ~6 s window (0.3) |
| Boss has Concentration | yes (0.8), no (0.2) |
| Afterimage crits give Darkness (the Glory loop) | yes (0.6), no (0.4) |
| A use can be dodge-cancelled | yes (0.5), no: you eat the mechanic (0.5) |

**Units.** Results are DPS as a multiple of a normal one-hit Strike on a good endgame rare 2H, with no ascendancy.
Gear, tree and support scaling multiply every row equally, so they are left out. On that scale a good rare with
Witchhunter is ×1.33.

## Results

### Single assumption failures (DPS as a multiple of a normal strike on a good rare; best policy)

| Scenario | Pre-ramped, 60 s boss | Pre-ramped, 180 s boss | Cold start, 60 s boss | Cold start, 180 s boss | Avg flames (cold, 180 s) | Hits eaten/min |
|---|---|---|---|---|---|---|
| Everything holds | x30.4 | x39.6 | x11.5 | x24.2 | 6.8 | 0.0 |
| Flame cap 5 | x13.4 | x11.1 | x9.8 | x9.5 | 4.7 | 0.0 |
| Flame cap 20 | x115.0 | x84.1 | x10.4 | x25.1 | 11.7 | 0.0 |
| Flames expire 8 s after last gain | x16.9 | x14.6 | x7.0 | x11.5 | 5.6 | 0.0 |
| Two Oro's lines don't stack | x19.5 | x27.3 | x10.1 | x20.0 | 7.0 | 0.0 |
| Afterimages copy first strike only | x6.6 | x7.0 | x5.7 | x6.4 | 8.4 | 0.0 |
| Echoing can't empower Infernal Step | x5.9 | x6.3 | x5.1 | x5.9 | 8.4 | 0.0 |
| Ambush doesn't persist across the use | x29.2 | x32.5 | x11.5 | x22.4 | 6.8 | 0.0 |
| No Concentration on the boss | x20.6 | x34.2 | x10.3 | x22.0 | 6.8 | 0.0 |
| Afterimage crits give no Darkness | x30.4 | x29.0 | x11.5 | x19.7 | 7.0 | 0.0 |
| Use can't be cancelled (you eat mechanics) | x58.3 | x63.8 | x7.2 | x16.0 | 6.2 | 3.2 |
| *Plain Infernal Step: one Oro's, no ascendancy, Echoing or Eclipse* | x2.7 | x2.7 | x2.6 | x2.7 | | |
| *Good rare + Witchhunter, normal strike* | x1.33 | | | | | |

### Mechanic cadence and attack speed (everything holds)

| Must-dodge mechanic every | inc. attack speed | Pre-ramped, 60 s | Cold, 180 s |
|---|---|---|---|
| never | 50% | x58.3 | x27.6 |
| never | 100% | x55.9 | x25.7 |
| 30 s | 50% | x58.3 | x27.3 |
| 30 s | 100% | x55.9 | x23.1 |
| 15 s | 50% | x30.4 | x24.2 |
| 15 s | 100% | x39.7 | x23.2 |
| 10 s | 50% | x23.8 | x17.6 |
| 10 s | 100% | x21.9 | x19.0 |

### All 1152 combinations, weighted by the estimated probabilities

| Fight | P10 | Median | P90 | Weighted mean | Share above x10 |
|---|---|---|---|---|---|
| 60 s boss | x1.9 | x6.1 | x45.3 | x15.5 | 28% |
| 180 s boss | x1.9 | x6.6 | x28.2 | x14.7 | 34% |

### Which assumption matters most (weighted mean DPS given each value, 180 s boss)

| Assumption | Value: weighted mean | Spread |
|---|---|---|
| flame_cap | 5: x4.9, 10: x11.3, 20: x28.9 | x5.8 |
| echo_mode | full: x24.3, first: x5.1, none: x4.7 | x5.1 |
| preramp | True: x21.7, False: x7.6 | x2.8 |
| flame_decay | none: x18.2, 8.0: x9.3 | x2.0 |
| oros_stack | True: x17.0, False: x11.2 | x1.5 |
| cancelable | True: x12.5, False: x16.8 | x1.3 |
| concentration | True: x15.3, False: x11.9 | x1.3 |
| ambush_persist | True: x15.4, False: x12.9 | x1.2 |
| afterimage_crits | True: x15.1, False: x14.0 | x1.1 |


## Findings

1. **The time-domain total is about half the static estimate when the boss has mechanics.**
   - The doc's static stack was ×137 per strike, or about ×25 over plain Infernal Step.
   - With no mechanics, the sim reproduces most of that: ×20–22. The gap is Echoing and Eclipse downtime.
   - With a dodge every 15 s, it falls to ×11–14 over plain, which is ×30–40 over a rare.
   - The cause: at F=10, one use takes about 15 s, which is longer than the gap between mechanics. Dodging cuts the
     Empowered use short, and holding the cast until after a dodge doesn't help, because the use still doesn't fit.
2. **Two switches decide the build. Everything else is secondary.**
   - **Afterimage replay** moves the weighted mean ×5. With full replay it is ×24; with first-strike-only it is ×5,
     barely above no Echoing at all.
   - **Flame cap** also moves it ×6: ×5 at a cap of 5, ×11 at 10 and ×29 at 20.
3. **New: ramp time is a first-order problem the doc missed.**
   - Reaching F=10 from zero takes about 90 s of strikes, because each ramp use is a full 2+3F sequence. A 60 s boss
     dies before the build is online. Cold-start DPS is about a third of pre-ramped.
   - What helps, in order:
     - flames carried into the arena, if they don't decay and survive the zone change
     - ramp uses cancelled after two strikes, if cancelling works
     - a lower cap, if it turns out low
   - A cap of 20 is ×115 pre-ramped but only ×10 from a cold start in a 60 s fight.
4. **Ambush persistence and the afterimage-crit Glory loop matter little (×1.1–1.2).**
   - Eclipse's own ~6 s window already covers much of each use.
   - The Glory loop only matters in long fights, where Eclipse would otherwise fire once.
   - Recommendation: demote both tests.
5. **Being unable to cancel raises paper DPS (×58–64) but means eating about 3 mechanics a minute.** On an uber that
   is probably not survivable, so treat those rows as an upper bound that needs a tank check. They also lift the
   weighted mean.
6. **Probability-weighted outlook** (using the subjective weights above): median about ×6.5, mean about ×15, and about
   a 30% chance of beating ×10.
   - The floor (P10) is about ×1.9.
   - Plain Infernal Step with one Oro's is a robust ×2.7 even without ascendancy, so the build degrades to a usable
     F-scaling build rather than failing.
7. **Faster attacks are not a free bucket.** Echoing's cooldown is fixed, so faster uses spend more time unbuffed. With
   no mechanics, 100% increased attack speed scores slightly lower relative to a rare. Speed helps only when it makes a
   use fit between mechanics.

## Revised 1.0 test order (recommendation)

1. **Afterimage replay** (Perforate proxy first): it is the ×5 switch.
2. **Flame cap, decay, and whether flames survive entering a boss arena**: this is the ×6 switch plus the ramp problem.
3. **Cancelability**: it decides whether ramp-cancel works and whether ubers are survivable.
4. Two Oro's stacking: ×1.5. Buy the second Oro's only after tests 1 and 2.
5. Ambush persistence, then afterimage crits: ×1.1–1.2, low priority.

## Not modelled

- Death and survival beyond counting the mechanics eaten during a locked use.
- The fire burn.
- Boss movement and phases.
- The Cyclone mobile phase.
- Shades, Whispers and the Rage/Darkness lever.
- Glory per Darkness is fixed at 1.0 (unpublished).

Enemy mechanics are a fixed 15 s cadence, which is a crude stand-in for uber Arbiter (its timeline is unsourced). The
probabilities are judgement, not data. Swap them in `SPACE` once 1.0 text is out.
