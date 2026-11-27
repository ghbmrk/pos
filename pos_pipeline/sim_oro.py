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
PC_KEEP = 0.25             # Perpetual Charge: 25% chance not to remove each consumed Charge (poe2db; expected value used)
OLROTH_EXTRA_USES = 2      # Olroth's Conviction: Supported Skills Empower 2 additional Skill uses (poe2db)
ERUPT_CD = 0.4             # Volcanic Eruption cooldown (poe2db)
ERUPT_DMG = 4 * 0.20       # 4 Molten Projectiles at 20% of Default Attack Damage each (poe2db)
ERUPT_HIT = 0.5            # share of projectiles that land on the boss (assumed: mortar, 1 m radius, 5-15 m range)
SA_COMBO = 1.2             # seconds for one Shadow Assault combo of 3 Strikes (estimate: 110% speed, dagger)
SA_FINAL2 = 0.5            # extra seconds for the second Final Strike with Crescendo (estimate)
SHROUD_CD = 7.0            # Shroud cooldown (poe2db L20); Shade at your previous location, 97% of your life
WEAPON_SWAP = 0.25         # seconds per weapon-set swap (estimate); rebuilding Shades swaps to daggers and back
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
    # Olroth's Conviction: True = the extra empowered uses only count if they START within Echoing's 10 s window;
    # False = the three uses all count however long they take. Open question, decides the value.
    olroth_window: bool = True
    # "once": Frenzy is consumed at the Echoing cast and all three uses get that afterimage count (census reading);
    # "each": every empowered use consumes the Frenzy held at that moment (upper bound).
    olroth_consume: str = "once"
    # Shade setup via Shadow Assault: "free" = Shades exist at no cost (old baseline); "once" = built at the start of
    # the fight; "each_eclipse" = Shades expire between Eclipses (duration unpublished) and are rebuilt before each.
    shade_setup: str = "free"
    # Shade decoys (Shade text: "Enemies cannot distinguish between you and your Shades, and will target a Shade as if
    # it were you"). True = a targeted mechanic picks uniformly among you and your live Shades (even targeting is an
    # assumption). shade_death = chance a Shade dies when a mechanic aimed at it lands (Shade life 64-97% of yours,
    # Shade defences unpublished).
    decoy: bool = False
    shade_death: float = 0.0


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
    boss_cdr_less: float = 0.0     # Witchhunter at 0 Concentration: boss cooldown recovery 50% less (0.5 to enable)
    shades: int = 0                # Shades copying each Ambushing melee attack (limit 3, 4 with Golem Hunger)
    shades_copy_echo: bool = False  # Shades also copy the afterimage portion of an empowered use
    olroth: bool = False           # Olroth's Conviction on Echoing Strikes: one cast empowers 3 Infernal Step uses
    perpetual: bool = False        # Perpetual Charge on Echoing Strikes: 25% of consumed Frenzy is kept
    crescendo: bool = False        # Crescendo on Shadow Assault: two Final Strikes, two Shades per combo
    shroud_dodge: bool = False     # dodge a mechanic with Shroud (dagger set) when ready: it interrupts the use like a
                                   # roll, and leaves a Shade where you stood, replacing a lost one at no setup cost
    eruption: bool = False         # Volcanic Eruption on Infernal Step: triggered on Hit against Ignited, 0.4 s cooldown


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
    # Decoy geometry. targeted_share = share of mechanics aimed at a target (the rest are arena-wide or positional and
    # ignore decoys). splash = chance a mechanic aimed at a Shade still hits you (Shades stand in melee range of the boss,
    # next to you, so large AoE aimed at a Shade can still land on you).
    targeted_share: float = 1.0
    splash: float = 0.0
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
    mechanics: int = 0
    dodged: int = 0                 # mechanics that reached you and were dodged (cancel or between uses)
    shades_lost: int = 0


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
    mech_n = 0
    uses = flame_sum = locked = echo_uses = eclipse_uses = 0
    burn_total = 0.0
    emp_left, emp_until, emp_after = 0, -1.0, 0
    erupt_ready = 0.0
    shades_alive = b.shades
    aim_acc = death_acc = 0.0
    dodged = lost = 0
    shroud_ready = 0.0

    def dodge() -> None:
        nonlocal dodged, shades_alive, shroud_ready
        dodged += 1
        if b.shroud_dodge and t >= shroud_ready and shades_alive < b.shades:
            advance(fight.dodge_time + 2 * WEAPON_SWAP, flames >= a.flame_cap)
            shades_alive += 1
            shroud_ready = t + SHROUD_CD
            return
        advance(fight.dodge_time, flames >= a.flame_cap)

    def reaches_you() -> bool:
        """Expected-value decoy roll for one mechanic (deterministic accumulators). Returns True if this mechanic must
        be handled by you; kills Shades in proportion to the mechanics they absorb."""
        nonlocal aim_acc, death_acc, shades_alive, lost
        s_n = shades_alive if a.decoy else 0
        ts = fight.targeted_share
        on_shade = ts * s_n / (1 + s_n)
        aim_acc += 1 - on_shade * (1 - fight.splash)
        death_acc += on_shade * a.shade_death
        while death_acc >= 1 - 1e-9 and shades_alive > 0:
            death_acc -= 1
            shades_alive -= 1
            lost += 1
        if aim_acc >= 1 - 1e-9:
            aim_acc -= 1
            return True
        return False

    def mech_gap() -> float:
        """Seconds to the next boss mechanic. Witchhunter: boss cooldown recovery is up to 50% less in proportion to
        missing Concentration (assumed to scale linearly; source: build doc), so mechanics come up to 2x less often."""
        if b.witchhunter and a.concentration and conc_max > 0 and b.boss_cdr_less:
            return fight.mechanic_every / (1 - b.boss_cdr_less * (1 - conc / conc_max))
        return fight.mechanic_every

    def advance(dt: float, at_cap: bool) -> None:
        nonlocal t, frenzy, conc
        if at_cap:
            frenzy = min(b.max_frenzy, frenzy + frenzy_rate * dt)
        if b.witchhunter and a.concentration and t - last_conc_loss >= CONC_REGEN_DELAY:
            conc = min(conc_max, conc + CONC_REGEN * conc_max * dt)
        t += dt

    def consume_frenzy() -> int:
        """Consume Frenzy; Perpetual Charge keeps 25% of it (expected value). Returns the count consumed."""
        nonlocal frenzy
        n = int(frenzy)
        frenzy -= n * (1 - PC_KEEP if b.perpetual else 1.0)
        return n

    def shade_setup_time() -> float:
        if not b.shades or not b.eclipse or a.shade_setup == "free":
            return 0.0
        combos = math.ceil(b.shades / (2 if b.crescendo else 1))
        return combos * (SA_COMBO + (SA_FINAL2 if b.crescendo else 0.0))

    def hit(amount: float) -> None:
        nonlocal dealt, conc, last_conc_loss
        if b.witchhunter and a.concentration and conc_max > 0:
            amount *= 1 + NO_MERCY_MAX * (1 - conc / conc_max)
            conc = max(0.0, conc - amount)
            last_conc_loss = t
        dealt += amount

    if a.shade_setup != "free":
        advance(shade_setup_time(), flames >= a.flame_cap)
    while dealt < life and t < fight.max_time:
        # flames decay
        if flames and t - last_flame_gain > a.flame_decay:
            flames = 0
        # mechanic outside a use: dodge unless a decoy took it
        if t >= next_mech:
            if reaches_you():
                dodge()
            next_mech += mech_gap()
            mech_n += 1
            continue
        # rebuild Shades lost to mechanics (swap to daggers, Shadow Assault combos, swap back)
        if b.eclipse and shades_alive < b.shades:
            combos = math.ceil((b.shades - shades_alive) / (2 if b.crescendo else 1))
            advance(2 * WEAPON_SWAP + combos * (SA_COMBO + (SA_FINAL2 if b.crescendo else 0.0)), flames >= a.flame_cap)
            shades_alive = b.shades
            continue
        # Eclipse
        if b.eclipse and glory >= 100 and t >= eclipse_until:
            glory -= 100
            if a.shade_setup == "each_eclipse":
                advance(shade_setup_time(), flames >= a.flame_cap)
            advance(b.eclipse_cast, flames >= a.flame_cap)
            eclipse_until = t + b.eclipse_duration
            eclipse_uses += 1
        f_next = min(a.flame_cap, flames + 1)
        olroth_use = False
        if emp_left > 0:
            if a.olroth_window and t > emp_until:
                emp_left = 0           # window closed: the remaining empowers are lost
            else:
                olroth_use = True
        want_echo = (b.echoing and a.echo_mode != "none" and not olroth_use
                     and (not p.echo_at_cap_only or f_next >= a.flame_cap))
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
            afterimages = 2 + per_frenzy * consume_frenzy()
            echo_uses += 1
        elif olroth_use:
            emp_left -= 1
            afterimages = (2 + per_frenzy * consume_frenzy()) if a.olroth_consume == "each" else emp_after
            echo_uses += 1
        elif want_echo and t >= echo_ready_at:
            afterimages = 2 + per_frenzy * consume_frenzy()
            advance(ECHO_CAST, flames >= a.flame_cap)
            if b.olroth:
                emp_left, emp_until, emp_after = OLROTH_EXTRA_USES, t + ECHO_WINDOW, afterimages
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
                next_mech += mech_gap()
                mech_n += 1
                if reaches_you():
                    if a.cancelable:
                        dodge()
                        break
                    locked += 1
            echo_mult = 1.0
            if afterimages and (a.echo_mode == "full" or i == 0):
                echo_mult += ECHO_LESS * afterimages * empower_w
            amb_on = b.eclipse and (use_ambush or t < eclipse_until)
            amb = ambush if amb_on else 1.0
            shade = SHADE_LESS * shades_alive * (echo_mult if b.shades_copy_echo else 1.0) if amb_on else 0.0
            hit(per * (echo_mult + shade) * amb * titan)
            hits = 1 + (afterimages if (afterimages and a.afterimage_crits and echo_mult > 1) else 0)
            if b.eclipse and t >= eclipse_until:
                glory += hits * b.crit_chance * GRIM_BARGAIN_DARK * a.glory_per_darkness
            if b.eruption and t >= erupt_ready:
                hit(ERUPT_DMG * ERUPT_HIT * (1 + k_fire * EXTRA_FIRE_PER_FLAME * f) * titan)
                erupt_ready = t + ERUPT_CD
            advance(dt, flames >= a.flame_cap)
            if flames and t - last_flame_gain > a.flame_decay:
                flames = 0  # expired mid-use; current use keeps its count
    killed = dealt >= life
    return Result(ttk=t, damage=dealt, uses=uses, avg_flames=flame_sum / max(uses, 1), locked_hits=locked, mechanics=mech_n,
                  burn_net_per_min=burn_total / max(t, 1e-9) * 60, echo_uses=echo_uses,
                  eclipse_uses=eclipse_uses, killed=killed, dodged=dodged, shades_lost=lost)


POLICIES = [Policy(c, w, rc, al) for c in (True, False) for w in (0.0, 4.0, 13.0) for rc in (False, True)
            for al in (False, True)]


def best(a: Assumptions, b: Build, fight: Fight, policies: list | None = None) -> tuple[Result, Policy]:
    runs = [(simulate(a, b, p, fight), p) for p in (policies or POLICIES)]
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


def fight_dps(a: Assumptions, b: Build, seconds: float, fight: Fight | None = None, scale: float = RARE_FIGHT_SCALE,
              policies: list | None = None) -> tuple[float, Result, Policy]:
    fight = replace(fight or Fight(), boss_life=rare_dps(Build()) * scale * seconds)
    r, p = best(a, b, fight, policies)
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


def defence_report() -> str:
    """Defence proxies per host: mechanics the build must dodge, hits eaten when a use can't be cancelled, and what
    those cost in DPS terms. Fire burn is the same for every host (90% max fire res, Molten Tenet), so it is not a column."""
    ref = rare_dps(Build())
    sec = FIGHT_SECONDS[1]
    hosts = {"Witchhunter (No Mercy + boss slowed)": dict(boss_cdr_less=0.5),
             "Witchhunter, slow not applied": dict(),
             "Deadeye": HOSTS["Deadeye (Thrilling Chase + Avidity)"],
             "Chronomancer": HOSTS["Chronomancer (Time Snap)"],
             "No bucket": HOSTS["No ascendancy bucket (floor)"]}
    L = ["| Host | Mechanics every | Cancelable: DPS | Mechanics faced/min (cancelable) | Not cancelable: DPS "
         "| Not cancelable: hits eaten/min | DPS per hit eaten (uncancelable) |", "|---|---|---|---|---|---|---|"]
    for mech in (15.0, 10.0):
        for name, hk in hosts.items():
            b = replace(Build(), eclipse=True, shades=4, shades_copy_echo=True, **hk)
            fight = Fight(mechanic_every=mech, first_mechanic=mech / 2)
            cols = []
            for canc in (True, False):
                d, r, _ = fight_dps(Assumptions(preramp=True, cancelable=canc), b, sec, fight, scale=100.0)
                cols.append((d / ref, r))
            (d1, r1), (d2, r2) = cols
            eaten = r2.locked_hits / r2.ttk * 60
            L.append(f"| {name} | {mech:.0f} s | x{d1:.1f} | {r1.mechanics / r1.ttk * 60:.1f} | x{d2:.1f} | {eaten:.1f} "
                     f"| {'n/a' if eaten == 0 else f'x{d2 / eaten:.1f}'} |")
    return "\n".join(L)

DECOY_GEOMETRY = {
    # name: (targeted_share, splash, shade_death)
    "Ideal: all targeted, no splash, Shades survive": (1.0, 0.0, 0.0),
    "All targeted, no splash, Shade dies per hit": (1.0, 0.0, 1.0),
    "Mixed boss: 60% targeted, 50% splash, 50% death": (0.6, 0.5, 0.5),
    "Mixed boss, Shade dies per hit": (0.6, 0.5, 1.0),
    "Arena-heavy boss: 30% targeted, 50% splash, 50% death": (0.3, 0.5, 0.5),
}


DECOY_PHASES = 8


def decoy_report(mech: float = 10.0, shroud: bool = False) -> str:
    """Shade decoys: mechanics that reach you, hits eaten when a use can't be cancelled, Shades lost, and DPS, for the
    Witchhunter host (No Mercy + boss slowed) with echo-copying Shades, pre-ramped, Shades built once and rebuilt
    (weapon swap + Shadow Assault) whenever one dies."""
    ref = rare_dps(Build())
    sec = FIGHT_SECONDS[1]
    L = ["| Shades | Decoy geometry | Cancelable: DPS | Reach you/min | Shades lost/min | Not cancelable: DPS "
         "| Hits eaten/min | Shades lost/min (no cancel) |", "|---|---|---|---|---|---|---|---|"]
    rows = [(0, "No Shades", None)]
    for n in (3, 4):
        rows.append((n, "Shades, no decoy effect (old model)", None))
        rows += [(n, g, v) for g, v in DECOY_GEOMETRY.items()]
    if shroud:
        rows += [(4, "Shroud-as-dodge + " + g, v) for g, v in DECOY_GEOMETRY.items() if v[2] > 0]
    for n, name, geo in rows:
        b = replace(Build(), eclipse=True, shades=n, shades_copy_echo=True, boss_cdr_less=0.5,
                    shroud_dodge=name.startswith("Shroud"))
        ts, sp, death = geo or (1.0, 0.0, 0.0)
        cols = []
        for canc in (True, False):
            a = Assumptions(preramp=True, cancelable=canc, shade_setup="once", decoy=geo is not None, shade_death=death)
            acc = [0.0, 0.0, 0.0, 0.0]
            for k in range(DECOY_PHASES):  # average over mechanic phase: one phase is noisy (use length vs cadence)
                fight = Fight(mechanic_every=mech, first_mechanic=mech * (k + 0.5) / DECOY_PHASES,
                              targeted_share=ts, splash=sp)
                d, r, _ = fight_dps(a, b, sec, fight, scale=100.0, policies=OL_POLICIES)
                for i, v in enumerate((d / ref, r.dodged, r.locked_hits, r.shades_lost)):
                    acc[i] += (v if i == 0 else v / r.ttk * 60) / DECOY_PHASES
            cols.append(acc)
        (d1, y1, _, s1), (d2, _, e2, s2) = cols
        L.append(f"| {n} | {name} | x{d1:.1f} | {y1:.1f} | {s1:.1f} | x{d2:.1f} | {e2:.1f} | {s2:.1f} |")
    return "\n".join(L)


ADDONS = {
    "Base (Echoing only)": dict(),
    "+ Perpetual Charge": dict(perpetual=True),
    "+ Volcanic Eruption": dict(eruption=True),
    "+ Crescendo (Shadow Assault)": dict(crescendo=True),
    "+ Olroth's Conviction": dict(olroth=True),
    "+ Olroth's + Perpetual Charge": dict(olroth=True, perpetual=True),
    "+ Olroth's + Perpetual + Eruption + Crescendo": dict(olroth=True, perpetual=True, eruption=True, crescendo=True),
}
OLROTH_HOSTS = {"Witchhunter": dict(boss_cdr_less=0.5), "Deadeye": HOSTS["Deadeye (Thrilling Chase + Avidity)"]}


OL_SCALE = 100.0  # boss sized for ~10x the build's plain DPS: long enough for 10+ uses, so empower counts show
OL_POLICIES = [p for p in POLICIES if not p.ramp_cancel]  # ramp-cancel never wins at the cap; halves the run time


def _olroth_row(job):
    hn, an = job
    ref = rare_dps(Build())
    sec = FIGHT_SECONDS[1]
    keys = list(SPACE)
    combos = [(Assumptions(**{k: v for k, (v, _) in zip(keys, c)}), math.prod(pr for _, pr in c))
              for c in itertools.product(*(SPACE[k] for k in keys))]
    tot = sum(w for _, w in combos)
    b = replace(Build(), eclipse=True, shades=4, shades_copy_echo=True, **OLROTH_HOSTS[hn], **ADDONS[an])
    wins = (True, False) if b.olroth else (True,)

    def dps(a, fight=None):
        return fight_dps(a, b, sec, fight, OL_SCALE, OL_POLICIES)

    means = [sum(dps(replace(a, olroth_window=win, shade_setup="once"))[0] / ref * w for a, w in combos) / tot
             for win in wins]

    def pre(win=True, **kw):
        return dps(Assumptions(preramp=True, olroth_window=win, shade_setup="once", **kw))[0] / ref
    holds = [pre(w) for w in wins]
    cold = dps(Assumptions(olroth_window=True, shade_setup="once"))[0] / ref
    nocancel = [pre(w, cancelable=False) for w in wins]
    cap20 = [pre(w, flame_cap=20) for w in wins]
    cap5 = pre(True, flame_cap=5)
    fight = Fight(mechanic_every=15.0, first_mechanic=7.5)
    r1 = dps(Assumptions(preramp=True, olroth_window=True, shade_setup="once"), fight)[1]
    r2 = dps(Assumptions(preramp=True, olroth_window=True, shade_setup="once", cancelable=False), fight)[1]
    return (sum(means) / len(means), hn, an, b.olroth, means, holds, cold, cap5, cap20, nocancel,
            r1.mechanics / r1.ttk * 60, r2.locked_hits / r2.ttk * 60)


def olroth_report() -> str:
    """Rank Olroth's Conviction, Perpetual Charge, Crescendo and Volcanic Eruption add-ons on the Witchhunter and Deadeye
    hosts with the 4-Shade echo-copying layer. x = multiple of a normal strike on a good rare 2H (boss sized ~10x that
    over 180 s, so fights are long enough for several Echoing casts). Mean = probability-weighted over SPACE; for
    Olroth's it is shown for both window readings; Shade setup is paid once."""
    from multiprocessing import Pool
    ref = rare_dps(Build())
    sec = FIGHT_SECONDS[1]
    with Pool(4) as pool:
        rows = pool.map(_olroth_row, [(hn, an) for hn in OLROTH_HOSTS for an in ADDONS])

    def two(v):
        return f"x{v[0]:.1f}" if len(v) == 1 else f"x{v[0]:.1f} / x{v[1]:.1f}"
    L = ["Olroth's cells show: all three uses must start in Echoing's 10 s window / no window limit.", "",
         "| Rank | Host + add-on | Weighted mean | Pre-ramped, holds | Cold, holds | Cap 5 | Cap 20 | No cancel "
         "| Mechanics faced/min | Hits eaten/min (no cancel) |", "|---|---|---|---|---|---|---|---|---|---|"]
    for i, (mean, hn, an, ol, means, holds, cold, cap5, cap20, nc, mech, eaten) in enumerate(sorted(rows, key=lambda r: -r[0]), 1):
        L.append(f"| {i} | {hn} {an} | {two(means)} | {two(holds)} | x{cold:.1f} | x{cap5:.1f} | {two(cap20)} | {two(nc)} "
                 f"| {mech:.1f} | {eaten:.1f} |")
    L += ["", "Crescendo on Shadow Assault under each Shade-setup assumption (Witchhunter, 4 echo-copying Shades, pre-ramped, holds):", "",
          "| Shade setup | No Crescendo | Crescendo | Gain |", "|---|---|---|---|"]
    for ss, label in (("free", "Free (old baseline)"), ("once", "Built once at fight start"),
                      ("each_eclipse", "Rebuilt before every Eclipse")):
        v = []
        for cres in (False, True):
            b = replace(Build(), eclipse=True, shades=4, shades_copy_echo=True, crescendo=cres)
            v.append(fight_dps(Assumptions(preramp=True, shade_setup=ss), b, sec, None, OL_SCALE, OL_POLICIES)[0] / ref)
        L.append(f"| {label} | x{v[0]:.1f} | x{v[1]:.1f} | {v[1] / v[0] - 1:+.1%} |")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hosts", action="store_true", help="print the ascendancy host and layer ranking only")
    ap.add_argument("--olroth", action="store_true", help="rank Olroth's Conviction, Perpetual Charge, Crescendo, Eruption add-ons")
    ap.add_argument("--defence", action="store_true", help="print defence proxies per host")
    ap.add_argument("--decoy", action="store_true", help="print the Shade decoy defence table")
    ap.add_argument("--json", help="also write every combination's row to this file")
    args = ap.parse_args(argv)
    if args.olroth:
        print(olroth_report())
        return
    if args.decoy:
        print(decoy_report(10.0))
        print()
        print(decoy_report(15.0))
        return
    if args.defence:
        print(defence_report())
        return
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
