"""Time-step boss-fight simulation of the Oro's Sacrifice / Infernal Step build, with each unverified 1.0
assumption as a switch (docs/sim-oro-infernal-step.md).

PoB cannot model this build: Oro's Sacrifice, Infernal Step, Sacrificial Flame, Echoing Strikes, Eclipse and
Witchhunter's Concentration are 1.0 content or unparsed in the pinned 0.5 data. So this is an analytical
simulation built from tooltip numbers (poe2db 1.0, PoB ModCache text for Concentration). Damage is in relative
units: one Infernal Step strike from one Oro's at 0 flames with no buffs = 1. Generic scaling (gear, tree,
supports) multiplies every scenario equally and is left out.

Run: python -m pos_pipeline.sim_oro [--json out.json]
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from dataclasses import dataclass, field, replace

# ---- facts (tooltips) -------------------------------------------------------------------------------
OROS_APS = 1.51            # Oro's Sacrifice weapon APS incl. its local 21%
SKILL_SPEED = 0.49         # Infernal Step "49% attack speed" (of weapon)
ADD_STRIKE_MORE = 2.13     # additional strikes have 113% more attack speed
MORE_PER_FLAME = 0.15      # Infernal Step 15% more damage per flame
EXTRA_FIRE_PER_FLAME = 0.12  # Oro's 12% of damage as extra fire per flame
BURN_PER_FLAME = 400.0     # fire damage taken per flame on use
ECHO_CD = 12.8             # Echoing Strikes cooldown
ECHO_CAST = 0.8
ECHO_WINDOW = 10.0         # Empower lasts 10 s
ECHO_LESS = 0.5            # afterimages deal 50% less
AMBUSH_PER_DARK = 0.03     # 3% more per Darkness expended
GRIM_BARGAIN_DARK = 5.0    # Darkness per crit
GRIM_BARGAIN_CONSUME = 1.1  # counts as consuming 10% more
NO_MERCY_MAX = 0.40        # up to 40% more by missing Concentration
CONC_FRAC_LIFE = 0.30      # max Concentration = 30% of max life
CONC_REGEN = 0.10          # regains 10%/s of max if not lost in past 5 s
CONC_REGEN_DELAY = 5.0
THRILLING_PER_FRENZY = 1.5  # Deadeye Thrilling Chase: 50% chance a consumed Frenzy Charge counts double (expected value)
AVIDITY_GAIN = 1.5         # Deadeye Avidity: 50% chance of an additional Frenzy Charge per gain (expected value)
TIME_SNAP_CD = 32.0        # Chronomancer Time Snap cooldown at level 20 (poe2db 1.0)
TIME_SNAP_CAST = 0.5       # assumed cast time (unpublished)
SHADE_LESS = 0.5           # Shade portion deals 50% less damage
RARE_BASE_RATIO = 1 / 0.55  # good endgame rare 2H vs Oro's base (estimate in the build doc)


@dataclass(frozen=True)
class Assumptions:
    flame_cap: int = 10            # max Sacrificial Flames (unpublished)
    flame_decay: float = math.inf  # seconds after last gain that all flames expire (unpublished)
    oros_stack: bool = True        # two Oro's per-flame lines (extra fire, Frenzy) both apply
    echo_mode: str = "full"        # full: afterimages replay the whole use; first: first strike only; none
    ambush_persist: bool = True    # Eclipse Ambush at use start covers the whole use
    concentration: bool = True     # the boss has Concentration (No Mercy works)
    afterimage_crits: bool = True  # afterimage crits grant Grim Bargain Darkness (feeds the Glory loop)
    cancelable: bool = True        # a use can be dodge-cancelled
    glory_per_darkness: float = 1.0  # Glory gained per Darkness gained (unpublished)
    preramp: bool = False          # flames (and Frenzy) can be built before the boss and carried into the fight


@dataclass(frozen=True)
class Build:
    two_oros: bool = True          # Giant's Blood + second Oro's
    witchhunter: bool = True
    eclipse: bool = True
    echoing: bool = True
    max_frenzy: int = 8
    max_darkness: int = 30
    inc_attack_speed: float = 0.5  # from gear/tree (estimate)
    crit_chance: float = 0.10
    max_fire_res: float = 0.90
    molten_tenet: bool = True      # 10% of prevented fire damage recouped as life
    eclipse_duration: float = 6.0  # active window (4 s then accelerating drain; estimate)
    eclipse_cast: float = 0.5
    # host / layer options (docs/unlocked-by-1-0.md section 2.2); all off by default = original baseline
    thrilling_chase: bool = False  # Deadeye: consumed Frenzy counts x1.5 (afterimages 2 + 1.5 per Frenzy)
    avidity: bool = False          # Deadeye: Frenzy gain x1.5
    serles_chance: float = 0.0     # Serle's Grit chance an Empower does not count its Attack (take 0.10-0.20)
    serles_window: float = ECHO_WINDOW  # seconds an uncounted Empower lasts after the Echoing cast
    time_snap: bool = False        # Chronomancer: Time Snap resets Echoing's cooldown
    titan_uptime: float = 0.0      # Titan Crushing Impacts: share of time the boss is Heavy Stunned (25% more)
    shades: int = 0                # Shades copying each Ambushing melee attack (limit 3, 4 with Golem Hunger)
    shades_copy_echo: bool = False  # Shades also copy the afterimage portion of an empowered use


@dataclass(frozen=True)
class Policy:
    echo_at_cap_only: bool = True  # do not spend Echoing on ramp uses
    wait_for_echo: float = 4.0     # wait up to this long for Echoing before casting unbuffed
    ramp_cancel: bool = False      # below the flame cap, cancel each use after its first strikes (needs cancelable)
    align: bool = False            # hold an Empowered use until just after the next mechanic if it would be cut


@dataclass(frozen=True)
class Fight:
    boss_life: float = 0.0          # 0 = auto (set per study)
    mechanic_every: float = 15.0    # a must-dodge boss mechanic every N seconds
    first_mechanic: float = 7.5
    dodge_time: float = 1.0
    max_time: float = 1200.0


@dataclass
class Result:
    ttk: float
    damage: float
    uses: int
    avg_flames: float
    locked_hits: int
    burn_net_per_min: float
    echo_uses: int
    eclipse_uses: int
    killed: bool = field(default=True)


def _strike_times(f: int, aps: float) -> list[float]:
    t1 = 1.0 / aps
    n = 2 + 3 * f
    return [t1 if i < 2 else t1 / ADD_STRIKE_MORE for i in range(n)]


def simulate(a: Assumptions, b: Build, p: Policy, fight: Fight) -> Result:
    aps = OROS_APS * SKILL_SPEED * (1 + b.inc_attack_speed)
    k_fire = (2 if (b.two_oros and a.oros_stack) else 1)
    frenzy_rate = (2.0 if (b.two_oros and a.oros_stack) else 1.0) * (AVIDITY_GAIN if b.avidity else 1.0)
    per_frenzy = THRILLING_PER_FRENZY if b.thrilling_chase else 1.0
    titan = 1 + 0.25 * b.titan_uptime
    ambush = 1 + AMBUSH_PER_DARK * b.max_darkness * GRIM_BARGAIN_CONSUME if b.eclipse else 1.0

    life = fight.boss_life
    conc_max = CONC_FRAC_LIFE * life
    conc = conc_max
    last_conc_loss = -1e9

    t = 0.0
    flames = a.flame_cap if a.preramp else 0
    last_flame_gain = 0.0
    frenzy = float(b.max_frenzy) if a.preramp else 0.0
    glory = 100.0 if b.eclipse else 0.0
    eclipse_until = -1.0
    echo_ready_at = 0.0
    snap_ready_at = 0.0
    chain_w = 0.0
    empower_until = -1.0           # an uncounted Empower (Serle's Grit) can still be used until this time
    next_mech = fight.first_mechanic
    dealt = 0.0
    uses = flame_sum = locked = echo_uses = eclipse_uses = 0
    burn_total = 0.0

    def advance(dt: float, at_cap: bool) -> None:
        nonlocal t, frenzy, conc
        if at_cap:
            frenzy = min(b.max_frenzy, frenzy + frenzy_rate * dt)
        if b.witchhunter and a.concentration and t - last_conc_loss >= CONC_REGEN_DELAY:
            conc = min(conc_max, conc + CONC_REGEN * conc_max * dt)
        t += dt

    def hit(amount: float) -> None:
        nonlocal dealt, conc, last_conc_loss
        if b.witchhunter and a.concentration and conc_max > 0:
            amount *= 1 + NO_MERCY_MAX * (1 - conc / conc_max)
            conc = max(0.0, conc - amount)
            last_conc_loss = t
        dealt += amount

    while dealt < life and t < fight.max_time:
        # flames decay
        if flames and t - last_flame_gain > a.flame_decay:
            flames = 0
        # mechanic outside a use: dodge
        if t >= next_mech:
            advance(fight.dodge_time, flames >= a.flame_cap)
            next_mech += fight.mechanic_every
            continue
        # Eclipse
        if b.eclipse and glory >= 100 and t >= eclipse_until:
            glory -= 100
            advance(b.eclipse_cast, flames >= a.flame_cap)
            eclipse_until = t + b.eclipse_duration
            eclipse_uses += 1
        f_next = min(a.flame_cap, flames + 1)
        want_echo = b.echoing and a.echo_mode != "none" and (not p.echo_at_cap_only or f_next >= a.flame_cap)
        if want_echo and b.time_snap and t < echo_ready_at and t >= snap_ready_at:
            advance(TIME_SNAP_CAST, flames >= a.flame_cap)
            echo_ready_at = t
            snap_ready_at = t - TIME_SNAP_CAST + TIME_SNAP_CD
        free_empower = want_echo and b.serles_chance > 0 and t <= empower_until
        if want_echo and not free_empower and t < echo_ready_at and echo_ready_at - t <= p.wait_for_echo:
            advance(echo_ready_at - t, flames >= a.flame_cap)
            continue
        afterimages = 0
        if (p.align and a.cancelable and want_echo and t >= echo_ready_at
                and next_mech - t < ECHO_CAST + sum(_strike_times(f_next, aps))):
            advance(next_mech - t, flames >= a.flame_cap)
            continue
        empower_w = 1.0
        if free_empower:
            # Serle's Grit: the previous cast's Empower survived with probability serles_chance (expected value)
            empower_w = chain_w
            chain_w *= b.serles_chance
            afterimages = 2 + per_frenzy * int(frenzy)
            frenzy -= int(frenzy)
            echo_uses += 1
        elif want_echo and t >= echo_ready_at:
            afterimages = 2 + per_frenzy * int(frenzy)
            frenzy -= int(frenzy)
            advance(ECHO_CAST, flames >= a.flame_cap)
            echo_ready_at = t - ECHO_CAST + ECHO_CD
            empower_until = t + b.serles_window if b.serles_chance > 0 else -1.0
            chain_w = b.serles_chance
            echo_uses += 1
        # Infernal Step use
        flames = min(a.flame_cap, flames + 1)
        last_flame_gain = t
        f = flames
        uses += 1
        flame_sum += f
        res = b.max_fire_res
        burn = BURN_PER_FLAME * f
        burn_total += burn * (1 - res) - (0.1 * burn * res if b.molten_tenet else 0.0)
        per = (1 + MORE_PER_FLAME * f) * (1 + k_fire * EXTRA_FIRE_PER_FLAME * f)
        use_ambush = a.ambush_persist and t < eclipse_until
        cut = p.ramp_cancel and a.cancelable and f < a.flame_cap and not afterimages
        for i, dt in enumerate(_strike_times(f, aps)):
            if dealt >= life or (cut and i >= 2):
                break
            if t >= next_mech:
                next_mech += fight.mechanic_every
                if a.cancelable:
                    advance(fight.dodge_time, flames >= a.flame_cap)
                    break
                locked += 1
            echo_mult = 1.0
            if afterimages and (a.echo_mode == "full" or i == 0):
                echo_mult += ECHO_LESS * afterimages * empower_w
            amb_on = b.eclipse and (use_ambush or t < eclipse_until)
            amb = ambush if amb_on else 1.0
            shade = SHADE_LESS * b.shades * (echo_mult if b.shades_copy_echo else 1.0) if amb_on else 0.0
            hit(per * (echo_mult + shade) * amb * titan)
            hits = 1 + (afterimages if (afterimages and a.afterimage_crits and echo_mult > 1) else 0)
            if b.eclipse and t >= eclipse_until:
                glory += hits * b.crit_chance * GRIM_BARGAIN_DARK * a.glory_per_darkness
            advance(dt, flames >= a.flame_cap)
            if flames and t - last_flame_gain > a.flame_decay:
                flames = 0  # expired mid-use; current use keeps its count
    killed = dealt >= life
    return Result(ttk=t, damage=dealt, uses=uses, avg_flames=flame_sum / max(uses, 1), locked_hits=locked,
                  burn_net_per_min=burn_total / max(t, 1e-9) * 60, echo_uses=echo_uses,
                  eclipse_uses=eclipse_uses, killed=killed)


POLICIES = [Policy(c, w, rc, al) for c in (True, False) for w in (0.0, 4.0, 13.0) for rc in (False, True)
            for al in (False, True)]


def best(a: Assumptions, b: Build, fight: Fight) -> tuple[Result, Policy]:
    runs = [(simulate(a, b, p, fight), p) for p in POLICIES]
    return min(runs, key=lambda rp: (rp[0].ttk, -rp[0].damage))


def rare_dps(b: Build) -> float:
    """Reference: a normal one-hit Strike on a good endgame rare 2H, same generic scaling, no tricks.
    Runs at ~100% of weapon speed (Infernal Step runs at 49%), so in sim units/s it is rare_ratio * weapon APS."""
    return RARE_BASE_RATIO * OROS_APS * (1 + b.inc_attack_speed)


# ---- studies --------------------------------------------------------------------------------------
# Subjective probabilities (estimates, not measured) for the probability-weighted view.
SPACE = {
    "flame_cap": [(5, 0.3), (10, 0.4), (20, 0.3)],
    "flame_decay": [(math.inf, 0.6), (8.0, 0.4)],
    "preramp": [(True, 0.5), (False, 0.5)],
    "oros_stack": [(True, 0.6), (False, 0.4)],
    "echo_mode": [("full", 0.5), ("first", 0.35), ("none", 0.15)],
    "ambush_persist": [(True, 0.7), (False, 0.3)],
    "concentration": [(True, 0.8), (False, 0.2)],
    "afterimage_crits": [(True, 0.6), (False, 0.4)],
    "cancelable": [(True, 0.5), (False, 0.5)],
}
FIGHT_SECONDS = (60.0, 180.0)  # boss life = rare reference DPS x this many seconds x RARE_FIGHT_SCALE
RARE_FIGHT_SCALE = 10.0        # boss is sized for a build ~10x the plain rare (estimate, any big number works)


def no_mercy_avg(life_fraction_per_hit: float = 1e-3) -> float:
    """Time-averaged No Mercy multiplier for steady hits that kill the boss (Concentration 30% of life)."""
    conc, dealt, n = CONC_FRAC_LIFE, 0.0, 0
    while dealt < 1.0:
        amt = life_fraction_per_hit * (1 + NO_MERCY_MAX * (1 - conc / CONC_FRAC_LIFE))
        conc, dealt, n = max(0.0, conc - amt), dealt + amt, n + 1
    return 1.0 / (n * life_fraction_per_hit)


def fight_dps(a: Assumptions, b: Build, seconds: float, fight: Fight | None = None) -> tuple[float, Result, Policy]:
    fight = replace(fight or Fight(), boss_life=rare_dps(Build()) * RARE_FIGHT_SCALE * seconds)
    r, p = best(a, b, fight)
    return (fight.boss_life / r.ttk if r.killed else r.damage / r.ttk), r, p


def run_all(b: Build | None = None) -> dict:
    b = b or Build()
    ref = rare_dps(b)
    keys = list(SPACE)
    rows = []
    for combo in itertools.product(*(SPACE[k] for k in keys)):
        a = Assumptions(**{k: v for k, (v, _) in zip(keys, combo)})
        row = {k: (v if v != math.inf else "none") for k, (v, _) in zip(keys, combo)}
        row["prob"] = math.prod(pr for _, pr in combo)
        for sec in FIGHT_SECONDS:
            d, r, p = fight_dps(a, b, sec)
            row[f"x_rare_{int(sec)}"] = round(d / ref, 2)
            row[f"ttk_{int(sec)}"] = round(r.ttk, 1) if r.killed else None
            row[f"flames_{int(sec)}"] = round(r.avg_flames, 1)
            row[f"locked_per_min_{int(sec)}"] = round(r.locked_hits / r.ttk * 60, 1)
        rows.append(row)
    return {"reference": "normal strike on a good rare 2H, no ascendancy (x1.0)",
            "witchhunter_on_reference": round(no_mercy_avg(), 3), "rows": rows}


def _wpct(vals: list[tuple[float, float]], q: float) -> float:
    vals = sorted(vals)
    tot, acc = sum(w for _, w in vals), 0.0
    for v, w in vals:
        acc += w
        if acc >= q * tot:
            return v
    return vals[-1][0]


SINGLE_FAILURES = {
    "Everything holds": {},
    "Flame cap 5": {"flame_cap": 5},
    "Flame cap 20": {"flame_cap": 20},
    "Flames expire 8 s after last gain": {"flame_decay": 8.0},
    "Two Oro's lines don't stack": {"oros_stack": False},
    "Afterimages copy first strike only": {"echo_mode": "first"},
    "Echoing can't empower Infernal Step": {"echo_mode": "none"},
    "Ambush doesn't persist across the use": {"ambush_persist": False},
    "No Concentration on the boss": {"concentration": False},
    "Afterimage crits give no Darkness": {"afterimage_crits": False},
    "Use can't be cancelled (you eat mechanics)": {"cancelable": False},
}


def report(b: Build | None = None) -> str:
    b = b or Build()
    ref = rare_dps(b)
    plain = Build(two_oros=False, witchhunter=False, eclipse=False, echoing=False)
    L = []
    L.append("### Single assumption failures (DPS as a multiple of a normal strike on a good rare; best policy)\n")
    L.append("| Scenario | Pre-ramped, 60 s boss | Pre-ramped, 180 s boss | Cold start, 60 s boss | Cold start, 180 s boss "
             "| Avg flames (cold, 180 s) | Hits eaten/min |")
    L.append("|---|---|---|---|---|---|---|")
    for name, kw in SINGLE_FAILURES.items():
        cells, extra = [], ""
        for pre in (True, False):
            for sec in FIGHT_SECONDS:
                d, r, _ = fight_dps(Assumptions(preramp=pre, **kw), b, sec)
                cells.append(f"x{d / ref:.1f}")
                if not pre and sec == FIGHT_SECONDS[1]:
                    extra = f"| {r.avg_flames:.1f} | {r.locked_hits / r.ttk * 60:.1f} |"
        L.append(f"| {name} | " + " | ".join(cells) + " " + extra)
    cells = []
    for pre in (True, False):
        for sec in FIGHT_SECONDS:
            d, _, _ = fight_dps(Assumptions(preramp=pre), plain, sec)
            cells.append(f"x{d / ref:.1f}")
    L.append("| *Plain Infernal Step: one Oro's, no ascendancy, Echoing or Eclipse* | " + " | ".join(cells) + " | | |")
    L.append(f"| *Good rare + Witchhunter, normal strike* | x{no_mercy_avg():.2f} | | | | | |")

    L.append("\n### Mechanic cadence and attack speed (everything holds)\n")
    L.append("| Must-dodge mechanic every | inc. attack speed | Pre-ramped, 60 s | Cold, 180 s |")
    L.append("|---|---|---|---|")
    for mech in (None, 30.0, 15.0, 10.0):
        for ias in (0.5, 1.0):
            fight = Fight(mechanic_every=mech or 1e9, first_mechanic=(mech or 1e9) / 2)
            bb = replace(b, inc_attack_speed=ias)
            r1 = fight_dps(Assumptions(preramp=True), bb, 60.0, fight)[0] / rare_dps(bb)
            r2 = fight_dps(Assumptions(), bb, 180.0, fight)[0] / rare_dps(bb)
            L.append(f"| {f'{mech:.0f} s' if mech else 'never'} | {ias:.0%} | x{r1:.1f} | x{r2:.1f} |")

    out = run_all(b)
    rows = out["rows"]
    L.append(f"\n### All {len(rows)} combinations, weighted by the estimated probabilities\n")
    L.append("| Fight | P10 | Median | P90 | Weighted mean | Share above x10 |")
    L.append("|---|---|---|---|---|---|")
    for sec in FIGHT_SECONDS:
        key = f"x_rare_{int(sec)}"
        vals = [(r[key], r["prob"]) for r in rows]
        mean = sum(v * w for v, w in vals) / sum(w for _, w in vals)
        above = sum(w for v, w in vals if v > 10) / sum(w for _, w in vals)
        L.append(f"| {int(sec)} s boss | x{_wpct(vals, .1):.1f} | x{_wpct(vals, .5):.1f} | x{_wpct(vals, .9):.1f} "
                 f"| x{mean:.1f} | {above:.0%} |")
    L.append("\n### Which assumption matters most (weighted mean DPS given each value, 180 s boss)\n")
    L.append("| Assumption | Value: weighted mean | Spread |")
    L.append("|---|---|---|")
    key = f"x_rare_{int(FIGHT_SECONDS[1])}"
    spreads = []
    for k, opts in SPACE.items():
        parts, means = [], []
        for v, _ in opts:
            vv = v if v != math.inf else "none"
            sel = [(r[key], r["prob"]) for r in rows if r[k] == vv]
            m = sum(x * w for x, w in sel) / sum(w for _, w in sel)
            parts.append(f"{vv}: x{m:.1f}")
            means.append(m)
        spreads.append((max(means) / min(means), k, ", ".join(parts)))
    for sp, k, txt in sorted(spreads, reverse=True):
        L.append(f"| {k} | {txt} | x{sp:.1f} |")
    return "\n".join(L), out


HOSTS = {
    "Witchhunter (No Mercy)": dict(),
    "Deadeye (Thrilling Chase + Avidity)": dict(witchhunter=False, thrilling_chase=True, avidity=True),
    "Chronomancer (Time Snap)": dict(witchhunter=False, time_snap=True),
    "Titan (Crushing Impacts, 60% heavy-stunned uptime, assumed)": dict(witchhunter=False, titan_uptime=0.6),
    "No ascendancy bucket (floor)": dict(witchhunter=False),
}
LAYERS = {
    "": dict(),
    " + Serle's Grit 15% (drops 2nd Oro's)": dict(two_oros=False, serles_chance=0.15),
    " + 3 Shades, copy the strike only": dict(shades=3),
    " + 3 Shades, also copy afterimages": dict(shades=3, shades_copy_echo=True),
    " + 4 Shades, also copy afterimages": dict(shades=4, shades_copy_echo=True),
}
HOST_SCENARIOS = {
    "Everything holds": {},
    "Afterimages first strike only": {"echo_mode": "first"},
    "Flame cap 5": {"flame_cap": 5},
    "Flame cap 20": {"flame_cap": 20},
    "No dodge-cancel": {"cancelable": False},
}


def host_report() -> str:
    """Rank ascendancy hosts and add-on layers by simulation. x = multiple of a normal strike on a good rare 2H."""
    ref = rare_dps(Build())
    sec = FIGHT_SECONDS[1]
    keys = list(SPACE)
    combos = [(Assumptions(**{k: v for k, (v, _) in zip(keys, c)}), math.prod(pr for _, pr in c))
              for c in itertools.product(*(SPACE[k] for k in keys))]
    rows = []
    for hn, hk in HOSTS.items():
        for ln, lk in LAYERS.items():
            b = replace(Build(), **hk, **lk)
            cells = []
            for pre in (True, False):
                for name, kw in list(HOST_SCENARIOS.items())[:1] + [list(HOST_SCENARIOS.items())[1]]:
                    cells.append(fight_dps(Assumptions(preramp=pre, **kw), b, sec)[0] / ref)
            stress = [fight_dps(Assumptions(preramp=True, **kw), b, sec)[0] / ref for n, kw in list(HOST_SCENARIOS.items())[2:]]
            tot = sum(w for _, w in combos)
            mean = sum(fight_dps(a, b, sec)[0] / ref * w for a, w in combos) / tot
            rows.append((mean, hn + ln, cells, stress))
    L = ["| Rank | Host + layer | Weighted mean | Pre-ramped, holds | Cold, holds | Pre-ramped, first-strike replay "
         "| Cap 5 | Cap 20 | No cancel |", "|---|---|---|---|---|---|---|---|---|"]
    for i, (mean, name, c, st) in enumerate(sorted(rows, reverse=True), 1):
        L.append(f"| {i} | {name} | x{mean:.1f} | x{c[0]:.1f} | x{c[2]:.1f} | x{c[1]:.1f} | "
                 + " | ".join(f"x{v:.1f}" for v in st) + " |")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hosts", action="store_true", help="print the ascendancy host and layer ranking only")
    ap.add_argument("--json", help="also write every combination's row to this file")
    args = ap.parse_args(argv)
    if args.hosts:
        print(host_report())
        return
    text, out = report()
    print(text)
    if args.json:
        with open(args.json, "w") as fh:
            json.dump(out, fh, indent=1, default=str)


if __name__ == "__main__":
    main()
