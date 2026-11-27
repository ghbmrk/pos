# Shade decoys for the Infernal Step build (simulated)

Extends [sim-hosts-infernal-step.md](sim-hosts-infernal-step.md). Run `python -m pos_pipeline.sim_oro --decoy` (about 2 s).
Unit: x a normal strike on a good rare 2H. Witchhunter host (No Mercy + boss slowed), 2x Oro's, Eclipse, Shades that copy
the afterimage portion, pre-ramped, boss sized ~100x, averaged over 8 mechanic phases. Estimates, not game data.

## Source text
- Shade (owner screenshot, 2026-11-27): "Enemies cannot distinguish between you and your Shades, and will target a Shade
  as if it were you." Shades cannot move or act alone; they copy melee attacks only when you Ambush (Eclipse makes every
  attack count as from Stealth and pauses Shade duration).
- Shade life by creator (poe2db, [research/shadow-skill-text.md](/mnt/project-files/research/shadow-skill-text.md)):
  Shroud 97% of your life (7 s cooldown, one Shade at your previous location), Shadow Extraction 64%, Shadow Assault
  641 flat, Duplicity 327 flat. Limit 3, 4 with Golem Hunger. All creators need a dagger (weapon set 2).

## Model
The decoy is one number, coverage c = (share of mechanics aimed at a target) x (1 - chance a mechanic aimed at a Shade
still hits you). With S live Shades and even targeting, the share of mechanics that reach you is

    1 - c * S / (1 + S)

Ideal (c = 1, S = 4): 20% reach you, a x5 cut. A mechanic that reaches you mid-use cancels the use (dodge) or is eaten
(no cancel). A mechanic absorbed by a Shade kills it with chance `shade_death`; a lost Shade is rebuilt before the next
use (2 weapon swaps of 0.25 s plus one 1.2 s Shadow Assault combo, both estimates). New switches: `Assumptions.decoy`,
`shade_death`; `Fight.targeted_share`, `splash`; `Build.shroud_dodge`.

## Must-dodge mechanic every 10 s
| Shades | Decoy geometry | Cancelable: DPS | Reach you/min | Shades lost/min | Not cancelable: DPS | Hits eaten/min | Shades lost/min (no cancel) |
|---|---|---|---|---|---|---|---|
| 0 | No Shades | x16.2 | 3.3 | 0.0 | x65.6 | 3.4 | 0.0 |
| 3 | Shades, no decoy effect (old model) | x31.8 | 3.4 | 0.0 | x159.4 | 3.6 | 0.0 |
| 3 | Ideal: all targeted, no splash, Shades survive | x136.7 | 0.8 | 0.0 | x160.1 | 0.6 | 0.0 |
| 3 | All targeted, no splash, Shade dies per hit | x115.4 | 0.8 | 2.6 | x136.1 | 0.8 | 2.6 |
| 3 | Mixed boss: 60% targeted, 50% splash, 50% death | x83.3 | 2.6 | 0.7 | x154.4 | 2.8 | 0.5 |
| 3 | Mixed boss, Shade dies per hit | x73.5 | 2.8 | 1.6 | x144.4 | 2.7 | 1.4 |
| 3 | Arena-heavy boss: 30% targeted, 50% splash, 50% death | x73.5 | 3.4 | 0.4 | x159.7 | 3.1 | 0.0 |
| 4 | Shades, no decoy effect (old model) | x40.5 | 3.4 | 0.0 | x186.2 | 3.6 | 0.0 |
| 4 | Ideal: all targeted, no splash, Shades survive | x160.2 | 0.5 | 0.0 | x187.2 | 0.6 | 0.0 |
| 4 | All targeted, no splash, Shade dies per hit | x142.4 | 0.5 | 2.7 | x161.6 | 0.5 | 2.7 |
| 4 | Mixed boss: 60% targeted, 50% splash, 50% death | x90.7 | 2.8 | 0.9 | x181.3 | 2.6 | 0.6 |
| 4 | Mixed boss, Shade dies per hit | x85.4 | 2.8 | 1.8 | x172.2 | 2.4 | 1.4 |
| 4 | Arena-heavy boss: 30% targeted, 50% splash, 50% death | x88.3 | 3.1 | 0.4 | x186.9 | 3.2 | 0.0 |

## Must-dodge mechanic every 15 s
| Shades | Decoy geometry | Cancelable: DPS | Reach you/min | Shades lost/min | Not cancelable: DPS | Hits eaten/min | Shades lost/min (no cancel) |
|---|---|---|---|---|---|---|---|
| 0 | No Shades | x45.2 | 2.6 | 0.0 | x65.8 | 2.4 | 0.0 |
| 3 | Shades, no decoy effect (old model) | x103.0 | 2.6 | 0.0 | x159.7 | 2.5 | 0.0 |
| 3 | Ideal: all targeted, no splash, Shades survive | x144.6 | 0.5 | 0.0 | x160.1 | 0.5 | 0.0 |
| 3 | All targeted, no splash, Shade dies per hit | x132.1 | 0.4 | 1.6 | x144.1 | 0.5 | 1.6 |
| 3 | Mixed boss: 60% targeted, 50% splash, 50% death | x105.0 | 1.8 | 0.4 | x155.8 | 1.6 | 0.5 |
| 3 | Mixed boss, Shade dies per hit | x106.9 | 1.8 | 1.0 | x149.5 | 1.6 | 1.0 |
| 3 | Arena-heavy boss: 30% targeted, 50% splash, 50% death | x99.6 | 2.1 | 0.1 | x160.1 | 2.1 | 0.0 |
| 4 | Shades, no decoy effect (old model) | x113.0 | 2.7 | 0.0 | x186.0 | 2.2 | 0.0 |
| 4 | Ideal: all targeted, no splash, Shades survive | x183.6 | 0.1 | 0.0 | x187.2 | 0.1 | 0.0 |
| 4 | All targeted, no splash, Shade dies per hit | x160.6 | 0.3 | 1.9 | x167.6 | 0.3 | 2.0 |
| 4 | Mixed boss: 60% targeted, 50% splash, 50% death | x123.5 | 1.7 | 0.4 | x186.5 | 1.7 | 0.2 |
| 4 | Mixed boss, Shade dies per hit | x122.9 | 1.6 | 1.0 | x181.2 | 1.7 | 0.8 |
| 4 | Arena-heavy boss: 30% targeted, 50% splash, 50% death | x113.8 | 2.2 | 0.0 | x186.7 | 1.9 | 0.0 |


## Result
- **The decoy attacks the sim's biggest loss.** A full use at F=10 takes ~15 s, so at a 10 s cadence it almost never
  finishes: 4 Shades without decoy give x40 cancelable against a x186 uninterrupted ceiling. With ideal decoys the same
  build reaches x160 (x4). With a mixed boss (60% targeted, 50% splash) it reaches x86-91 (x2.2). At a 15 s cadence the
  gains are x1.6 (ideal) and x1.1 (mixed), because most uses already fit.
- **Decoys also make "no cancel" survivable.** Hits eaten per minute when a use cannot be cancelled fall from 3.6 to
  0.6 (ideal) or 2.4-2.6 (mixed). The no-cancel DPS ceiling (x172-187) then costs about one hit per 2 minutes instead
  of ~4 per minute, if the geometry is ideal.
- **Losing Shades costs little.** Shades that die to every mechanic they absorb (Shadow Assault's 641 flat life will)
  cost 10-15% DPS: about 2-3 Shades per minute to rebuild at ~2 s each, plus the gap. Sturdier Shroud Shades are worth
  at most that 10-15%. Shroud used as the dodge (it interrupts the use like a roll and leaves a Shade where you stood)
  measured within 1% of a plain rebuild, so it is not a separate variant (`decoy_report(shroud=True)`).
- **Coverage c decides everything, and the text says nothing about it.** Arena-wide and ground mechanics ignore decoys;
  a large slam aimed at a Shade that stands next to you still hits you. Melee Shades stand in melee range of the boss,
  so splash is the default, not the exception.
- **The gain is non-linear in c at short cadence.** A full use is worth far more than a cut one, so each interrupt a
  Shade absorbs lets one whole use land. An arena-heavy boss (c = 0.15, ~10% fewer interrupts) still gains x2.2 at a
  10 s cadence, and nothing (x1.0) at 15 s. Mixed boss is c = 0.3.

## Recommendation
Keep 4 Shades (Golem Hunger on weapon set 2). Their DPS layer already doubles the mean; decoy defence is a free second
use of the same Shades. Treat it as a defence layer worth x1.1-x4 depending on the boss, not as a reason to drop
dodge-cancel or other defences until c is measured.

## New 1.0 tests (in order)
1. Targeting rule: does a boss pick uniformly among you and your Shades, the nearest, or the last attacker? Watch which
   target a single-target boss attack (charge, beam, projectile) picks with 1-4 Shades out.
2. Where Shades stand during Infernal Step: do they stay where created, or follow the teleport strikes? This sets splash.
3. Shade survivability against one boss hit (Shadow Assault 641 flat life vs Shroud 97%): do Shades get your defences?
4. Shade duration outside Eclipse (decoys only persist if they last between Eclipses).
5. Already open: does a Shade copy an item-granted skill (Oro's Infernal Step) and its afterimages.
