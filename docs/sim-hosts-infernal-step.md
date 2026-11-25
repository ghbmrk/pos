# Infernal Step host comparison (simulated)

Extends [sim-oro-infernal-step.md](sim-oro-infernal-step.md) with host and layer switches in `pos_pipeline/sim_oro.py`.
Run `python -m pos_pipeline.sim_oro --hosts` (about 11 minutes). Unit: x a normal strike on a good rare 2H, 180 s boss.
Weighted mean uses the sim's subjective probabilities over the 1,152 assumption combinations. Estimates, not game data.

## Ranking
| Rank | Host + layer | Weighted mean | Pre-ramped, holds | Cold, holds | Pre-ramped, first-strike replay | Cap 5 | Cap 20 | No cancel |
|---|---|---|---|---|---|---|---|---|
| 1 | Deadeye (Thrilling Chase + Avidity) + 4 Shades, also copy afterimages | x39.2 | x61.8 | x34.7 | x9.6 | x39.1 | x345.0 | x174.9 |
| 2 | Witchhunter (No Mercy) + 4 Shades, also copy afterimages | x38.0 | x61.8 | x29.6 | x10.2 | x30.7 | x345.0 | x174.9 |
| 3 | Titan (Crushing Impacts, 60% heavy-stunned uptime, assumed) + 4 Shades, also copy afterimages | x34.3 | x59.2 | x29.0 | x9.9 | x29.3 | x319.1 | x155.7 |
| 4 | Deadeye (Thrilling Chase + Avidity) + 3 Shades, also copy afterimages | x32.1 | x59.2 | x31.1 | x8.2 | x36.7 | x296.9 | x155.7 |
| 5 | Witchhunter (No Mercy) + 3 Shades, also copy afterimages | x31.6 | x59.2 | x29.0 | x10.0 | x29.1 | x296.9 | x150.2 |
| 6 | Chronomancer (Time Snap) + 4 Shades, also copy afterimages | x31.3 | x61.9 | x36.9 | x8.9 | x20.5 | x296.9 | x140.3 |
| 7 | No ascendancy bucket (floor) + 4 Shades, also copy afterimages | x30.0 | x56.8 | x28.4 | x8.8 | x25.3 | x296.9 | x140.3 |
| 8 | Titan (Crushing Impacts, 60% heavy-stunned uptime, assumed) + 3 Shades, also copy afterimages | x29.3 | x56.8 | x28.4 | x9.4 | x25.2 | x277.5 | x135.8 |
| 9 | Chronomancer (Time Snap) + 3 Shades, also copy afterimages | x27.3 | x58.5 | x35.6 | x7.5 | x19.6 | x260.5 | x120.4 |
| 10 | No ascendancy bucket (floor) + 3 Shades, also copy afterimages | x26.3 | x54.0 | x27.7 | x7.5 | x24.0 | x260.5 | x120.4 |
| 11 | Witchhunter (No Mercy) + 3 Shades, copy the strike only | x17.9 | x44.1 | x25.4 | x9.8 | x13.0 | x95.4 | x76.4 |
| 12 | Deadeye (Thrilling Chase + Avidity) + 3 Shades, copy the strike only | x17.5 | x42.7 | x27.0 | x7.3 | x13.4 | x93.3 | x73.8 |
| 13 | Titan (Crushing Impacts, 60% heavy-stunned uptime, assumed) + 3 Shades, copy the strike only | x16.6 | x40.7 | x24.4 | x8.6 | x11.7 | x85.8 | x69.0 |
| 14 | Chronomancer (Time Snap) + 3 Shades, copy the strike only | x15.7 | x40.7 | x28.3 | x6.9 | x11.4 | x90.5 | x61.1 |
| 15 | Deadeye (Thrilling Chase + Avidity) | x14.7 | x39.9 | x24.5 | x5.7 | x12.8 | x84.1 | x64.8 |
| 16 | Witchhunter (No Mercy) | x14.7 | x39.6 | x24.2 | x7.0 | x11.1 | x84.1 | x63.8 |
| 17 | No ascendancy bucket (floor) + 3 Shades, copy the strike only | x14.3 | x37.8 | x23.3 | x6.9 | x10.7 | x62.7 | x61.1 |
| 18 | Titan (Crushing Impacts, 60% heavy-stunned uptime, assumed) | x13.4 | x36.8 | x23.1 | x6.3 | x10.2 | x62.7 | x57.0 |
| 19 | Chronomancer (Time Snap) | x13.0 | x36.9 | x25.1 | x5.3 | x9.2 | x78.8 | x47.3 |
| 20 | No ascendancy bucket (floor) | x11.9 | x34.2 | x22.0 | x5.3 | x8.3 | x60.1 | x47.3 |
| 21 | Deadeye (Thrilling Chase + Avidity) + Serle's Grit 15% (drops 2nd Oro's) | x11.4 | x29.3 | x22.2 | x3.7 | x7.5 | x53.4 | x42.1 |
| 22 | Witchhunter (No Mercy) + Serle's Grit 15% (drops 2nd Oro's) | x11.3 | x29.3 | x22.3 | x4.7 | x7.5 | x54.1 | x41.7 |
| 23 | Titan (Crushing Impacts, 60% heavy-stunned uptime, assumed) + Serle's Grit 15% (drops 2nd Oro's) | x10.2 | x26.9 | x20.1 | x4.1 | x6.6 | x50.3 | x35.4 |
| 24 | No ascendancy bucket (floor) + Serle's Grit 15% (drops 2nd Oro's) | x9.1 | x23.5 | x18.8 | x3.5 | x5.5 | x43.3 | x31.7 |
| 25 | Chronomancer (Time Snap) + Serle's Grit 15% (drops 2nd Oro's) | x9.0 | x23.5 | x18.8 | x3.5 | x5.5 | x43.2 | x31.7 |


## Result
- **Layer matters more than host.** Shades that also copy the afterimage portion roughly double the mean (x14.7 -> x31-39). Shades copying only the strike add about x3 (x14.7 -> x17.9). The doc's x1.25 / x2.5 range reproduces: x2.4 mean for echo-copying Shades.
- **Host spread is small, ordered Deadeye ~ Witchhunter > Titan > Chronomancer > none.** Without Shades, Deadeye and Witchhunter tie (x14.7). With 4 echo-copying Shades Deadeye leads (x39.2 vs x38.0) because Thrilling Chase raises afterimage count; it also wins at flame cap 5 (x39 vs x31). Witchhunter's bucket is fixed; Deadeye's grows with max Frenzy.
- **Time Snap helps only when cold** (x36.9 vs x28.4 cold, best of any host) but loses when pre-ramped/capped because No Mercy and Thrilling Chase are worth more. Not the mean winner.
- **Serle's Grit is a net loss** (x11 vs x14.7): the 10 s Empower window expires before a 10-20 s use ends, so the saved Empower rarely applies, while the second Oro's is lost. Only helps if the window is not wall-clock (`serles_window` switch).
- The old estimate of x50-130 overstated: measured x59-62 pre-ramped holding, x30-37 cold, mean x31-39 weighted.

## Assumptions to flag
- Thrilling Chase and Avidity use expected values (x1.5 each); max Frenzy unchanged (8).
- Serle's chance 15% (range 10-20%), window = Echoing's 10 s.
- Time Snap cast 0.5 s (unpublished), 32 s cooldown, resets only Echoing.
- Titan uptime 60% heavy-stunned is a guess.
- Shades require Eclipse (Ambush); limit 3, 4 with Golem Hunger; 50% less; whether they copy afterimages is the decider (subjective 0.25 per doc, so the weighted mean here treats it as a scenario, not weighted by that probability).
- "No cancel" and Cap 20 columns report DPS only; damage taken while locked is not counted, so "No cancel" looks better than reality.
- No ascendancy-specific survivability, damage taken, or point costs are modelled.
