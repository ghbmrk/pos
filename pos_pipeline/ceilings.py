"""Uptime ceilings for mechanics PoB cannot calculate (L5b, docs/loop.md 2.5 step 3, docs/ceilings.md).

Ranking stays on the pure PoB number (the floor). For a mechanic the engine cannot time, `evaluate` also computes the number with
the mechanic ON 100% of the time (the ceiling), using only a PoB config option or a parseable custom line, never an assumed uptime.
The tool reports the ceiling, the headroom (ceiling / floor: how much the mechanic can compound) and the break-even uptime: the
share of the headroom a piece must realise to reach a required gain (e.g. the runner-up piece's measured gain). A ranked band between
floor and ceiling would be false precision (uptime dominates), so none is produced.

Spender skills: PoB computes the per-charge bonus natively for few skills (docs/ceilings.md). For the rest the bonus is read from
PoB's own skill data (`<skill>_damage_+%_final_per_<type>_charge`) and applied as a custom "N% more Damage" line; the engine
computes the result. A spender whose per-charge bonus is not damage-shaped (projectile count, area, duration) is `no_model`.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence

from pos_engine.engine import PobEngine

from . import data
from .actors import blend
from .diagnose import METRIC_KEY

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "third_party" / "PathOfBuilding-PoE2" / "src" / "Data" / "Skills"
KINDS = ("state_on", "spender", "no_own_damage", "needs_data")
CHARGES = ("Power", "Frenzy", "Endurance")


def registry() -> dict:
    return data._load("ceilings.yaml")


def entries() -> list[dict]:
    out = []
    for fam, f in registry()["families"].items():
        for e in f["entries"]:
            out.append({**e, "family": fam})
    return out


def validate_registry() -> list[str]:
    """Structural problems (empty list = ok): unique ids, known kinds, compilable matches, a note, applied levers for state_on."""
    errs, seen = [], set()
    for e in entries():
        i = e.get("id")
        if i in seen:
            errs.append(f"duplicate id {i}")
        seen.add(i)
        if e.get("kind") not in KINDS:
            errs.append(f"{i}: unknown kind {e.get('kind')!r}")
        if not e.get("note"):
            errs.append(f"{i}: no note")
        for m in e.get("match") or []:
            try:
                re.compile(m)
            except re.error as ex:
                errs.append(f"{i}: bad regex {m!r}: {ex}")
        if e.get("kind") == "state_on" and not (e.get("options") or e.get("custom_mods")):
            errs.append(f"{i}: state_on with no options or custom_mods")
    return errs


def match(line: str) -> list[dict]:
    """Registry entries whose `match` hits a stat line (first entry per id)."""
    return [e for e in entries() if any(re.search(m, line, re.I) for m in e.get("match") or [])]


def first_number(line: str) -> float | None:
    m = re.search(r"\d+(?:\.\d+)?", line or "")
    return float(m.group()) if m else None


# --- spender derivation from PoB's skill data ---------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def _skill_blocks() -> dict[str, str]:
    out: dict[str, str] = {}
    for f in sorted(SKILLS.glob("*.lua")):
        txt = f.read_text(encoding="utf-8")
        for m in re.finditer(r'skills\["(\w+)"\] = \{(.*?)\n\}\n', txt, re.S):
            nm = re.search(r'\bname = "([^"]+)"', m.group(2))
            if nm and "support = true" not in m.group(2) and "hidden = true" not in m.group(2):
                out.setdefault(nm.group(1), m.group(2))
    return out


def spender_data(skill: str) -> dict:
    """What PoB's skill data says about a charge spender: charge types consumed and per-charge stats (name, value)."""
    body = _skill_blocks().get(skill)
    if body is None:
        return {"skill": skill, "found": False, "types": [], "stats": []}
    st = re.search(r"skillTypes = \{(.*?)\},\n", body)
    types = [t for t in CHARGES if st and f"SkillConsumes{t}ChargesOnUse" in st.group(1)]
    stats = [(n, float(v)) for n, v in re.findall(r'\{ "([a-z_+%0-9]*charge[a-z_+%0-9]*)", (-?[\d.]+) \},', body)
             if "per_" in n or "consumed" in n or "when_charged" in n]
    return {"skill": skill, "found": True, "types": types, "stats": stats}


def _damage_stats(stats: Sequence[tuple[str, float]], charge: str) -> tuple[float, float, list[str]]:
    """(percent more Damage per charge, percent more Damage once any charge is held, stat names used). Only
    `*damage_+%_final_per_<type>_charge[_consumed]` and `*damage_+%_final_when_[<type>_]charge[s_consumed|d]` count."""
    per, flat, used = 0.0, 0.0, []
    for n, v in stats:
        if re.search(rf"damage_\+%_final_per_{charge.lower()}_charge", n):
            per += v; used.append(n)
        elif re.search(rf"damage_\+%_final_when_({charge.lower()}_)?charge(s_consumed|d)", n):
            flat += v; used.append(n)
    return per, flat, used


# --- evaluation ---------------------------------------------------------------------------------------------------------------

@dataclass
class Result:
    id: str
    family: str
    kind: str
    status: str               # evaluated | inert | native | derived | no_model | no_own_damage | needs_data | dropped (PoB ignored the line)
    floor: float | None = None
    ceiling: float | None = None
    headroom: float | None = None      # ceiling / floor
    compounding: bool | None = None
    applied: dict = field(default_factory=dict)
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def break_even(floor: float, ceiling: float, required: float) -> dict:
    """Uptime share of the floor->ceiling span needed to reach `required` (same metric). Assumes the metric is linear in uptime
    (true for damage averaged over time; flagged for EHP). `never` = the ceiling itself does not reach `required`."""
    if required <= floor:
        return {"uptime": 0.0, "verdict": "already_met"}
    if ceiling <= floor:
        return {"uptime": None, "verdict": "never"}
    u = (required - floor) / (ceiling - floor)
    return {"uptime": u, "verdict": "never" if u > 1 else "reachable"}


def at_uptime(floor: float, ceiling: float, uptime: float) -> float:
    """Metric at an assumed uptime (an assumption the report labels; uptime 0 reproduces the pure number)."""
    return blend(ceiling, floor, uptime)


def _ratio(floor: float, ceiling: float) -> float | None:
    return ceiling / floor if floor else None


def _read(eng: PobEngine, key: str) -> tuple[float, dict]:
    s = eng.get_stats([key, "PowerCharges", "FrenzyCharges", "EnduranceCharges"]) if key else {}
    st = s.get("stats", {})
    return float(st.get(key) or 0.0), st


def _apply(eng: PobEngine, xml: str, key: str, options: dict | None, custom: str | None, base_options: dict | None) -> tuple[float, int | None]:
    eng.load_build_xml(xml)
    opts = {**(base_options or {}), **(options or {})}
    r = eng.set_config(options=opts or None, custom_mods=custom, keys=[key])
    n = (r.get("customMods") or {}).get("count") if custom else None
    return float((r.get("stats") or {}).get(key) or 0.0), n


def evaluate(xml: str, ids: Sequence[str] | None = None, *, metric: str = "FullDPS", lines: dict[str, str] | None = None,
             base_options: dict | None = None, engine: PobEngine | None = None) -> list[Result]:
    """Floor, ceiling and headroom for registry entries (all of them when `ids` is None) on a build.
    `lines` maps entry id -> the piece's stat line (fills `{n}`). Every entry reloads the build: no option leaks between entries."""
    key = METRIC_KEY.get(metric, metric)
    reg = {e["id"]: e for e in entries()}
    want = list(ids) if ids else list(reg)
    unknown = [i for i in want if i not in reg]
    if unknown:
        raise ValueError(f"unknown ceiling ids {unknown}; known: {sorted(reg)}")
    ratio_min = float(registry()["compounding_ratio"])
    eng = engine or PobEngine()
    own = engine is None
    out: list[Result] = []
    try:
        floor, _ = _apply(eng, xml, key, None, None, base_options)
        main = (eng.get_stats([key]) or {}).get("mainSkill")
        for i in want:
            e = reg[i]
            r = Result(i, e["family"], e["kind"], "evaluated", note=e["note"])
            if e["kind"] in ("no_own_damage", "needs_data"):
                r.status = e["kind"]
                if e["kind"] == "no_own_damage":
                    r.floor = r.ceiling = floor
                    r.headroom = 1.0 if floor else None
                    r.compounding = False
                out.append(r)
                continue
            if e["kind"] == "state_on":
                custom = e.get("custom_mods")
                if custom:
                    n = first_number((lines or {}).get(i, "")) or e.get("default_n")
                    custom = custom.replace("{n}", f"{n:g}")
                r.floor = floor
                r.ceiling, cnt = _apply(eng, xml, key, e.get("options"), custom, base_options)
                r.applied = {k: v for k, v in (("options", e.get("options")), ("custom_mods", custom)) if v}
                if custom and not cnt:
                    r.status, r.note = "dropped", f"PoB parsed 0 mods from {custom!r}: ceiling not computed. " + r.note
                    r.ceiling = None
            else:  # spender
                _spender(eng, xml, key, main, floor, r, base_options)
            if r.ceiling is not None and r.status == "evaluated" and r.floor is not None and abs(r.ceiling - r.floor) <= 1e-9 * max(1.0, abs(r.floor)):
                r.status, r.note = "inert", "Applied and parsed, but nothing in this build reads the state (ceiling = floor): no value here at any uptime. " + r.note
            if r.ceiling is not None and r.floor:
                r.headroom = _ratio(r.floor, r.ceiling)
                r.compounding = bool(r.headroom and r.headroom >= ratio_min)
            out.append(r)
    finally:
        if own:
            eng.close()
    return out


def _spender(eng: PobEngine, xml: str, key: str, main: str | None, floor: float, r: Result, base_options: dict | None) -> None:
    sd = spender_data(main or "")
    r.floor = floor
    if not sd["types"]:
        r.status, r.note, r.floor = "no_model", f"main skill {main!r} does not consume charges (or is not in PoB's skill data): nothing to bound", None
        return
    opts = {f"use{t}Charges": True for t in sd["types"]}
    native, _ = _apply(eng, xml, key, opts, None, base_options)
    r.applied = {"options": opts}
    if abs(native - floor) > 1e-9 * max(1.0, abs(floor)):
        r.status, r.ceiling = "native", native
        r.note = f"PoB computes {main}'s per-charge bonus itself (charges at maximum: {native:.4g} vs {floor:.4g}): modelled_confirmed, not a registry gap."
        return
    lines, used = derived_lines(eng, xml, key, sd, base_options)
    if not lines:
        r.status, r.ceiling = "no_model", None
        r.note = (f"PoB does not move {main} with charges and its per-charge stats {[n for n, _ in sd['stats']] or 'none'} are not "
                  "damage-shaped (count, area, duration): no ceiling without an assumption about what the bonus is worth.")
        return
    line = "\n".join(lines)
    c, cnt = _apply(eng, xml, key, opts, line, base_options)
    r.applied = {"options": opts, "custom_mods": line, "from_stats": used}
    if cnt != len(lines):
        r.status, r.ceiling, r.note = "dropped", None, f"PoB parsed {cnt} of {len(lines)} lines {lines}"
        return
    r.status, r.ceiling = "derived", c
    r.note = (f"PoB does not move {main} with charges. Per-charge bonus read from PoB's skill data {used} at the build's maximum charges, "
              "applied as a custom line: all damage of the skill counts, so this is an upper bound when PoB's own gating would exclude part of it.")


def derived_lines(eng: PobEngine, xml: str, key: str, sd: dict, base_options: dict | None = None) -> tuple[list[str], list[str]]:
    """Custom lines that reproduce a spender's per-charge damage at the build's maximum charges, from PoB's skill data."""
    lines, used = [], []
    for t in sd["types"]:
        _, st = _read_after(eng, xml, key, {f"use{t}Charges": True}, base_options)
        n = float(st.get(f"{t}Charges") or 0)
        per, flat, u = _damage_stats(sd["stats"], t)
        if n and per:
            lines.append(f"{per * n:g}% more Damage")
        if n and flat:
            lines.append(f"{flat:g}% more Damage")
        used += u
    return lines, used


def _read_after(eng: PobEngine, xml: str, key: str, options: dict, base_options: dict | None) -> tuple[float, dict]:
    eng.load_build_xml(xml)
    r = eng.set_config(options={**(base_options or {}), **options}, keys=[key, "PowerCharges", "FrenzyCharges", "EnduranceCharges"])
    st = r.get("stats") or {}
    return float(st.get(key) or 0.0), st


def interaction(results: Sequence[Result], xml: str, *, metric: str = "FullDPS", engine: PobEngine | None = None) -> dict | None:
    """All evaluated state_on / derived ceilings on at once vs the sum of single gains: the compounding the owner principle asks to
    see. synergy > 0 = the mechanics multiply rather than add."""
    cand = [r for r in results if r.status in ("evaluated", "derived") and r.ceiling is not None and r.floor and r.applied]
    on, taken, skipped = [], set(), []
    for r in cand:   # entries that set the same option are one state, not two: keep the first
        o = set((r.applied.get("options") or {}))
        if o & taken:
            skipped.append(r.id)
            continue
        taken |= o
        on.append(r)
    if len(on) < 2:
        return None
    key = METRIC_KEY.get(metric, metric)
    opts: dict = {}
    custom: list[str] = []
    for r in on:
        opts.update(r.applied.get("options") or {})
        if r.applied.get("custom_mods"):
            custom.append(r.applied["custom_mods"])
    eng = engine or PobEngine()
    try:
        joint, _ = _apply(eng, xml, key, opts, "\n".join(custom) or None, None)
    finally:
        if engine is None:
            eng.close()
    floor = on[0].floor
    singles = sum(r.ceiling - floor for r in on)
    return {"ids": [r.id for r in on], "floor": floor, "joint": joint, "sum_of_single_gains": singles,
            "joint_gain": joint - floor, "synergy": (joint - floor) - singles, "skipped_overlapping": skipped}


def render(results: Sequence[Result], metric: str = "FullDPS", required: float | None = None, joint: dict | None = None) -> str:
    L = [f"Uptime ceilings on {metric} (floor = pure PoB; ceiling = mechanic ON 100% of the time; no uptime assumed)"]
    for r in results:
        if r.status in ("no_own_damage", "needs_data"):
            L.append(f"- {r.id} [{r.family}] {r.status}: {r.note}")
            continue
        if r.ceiling is None or r.status == "inert":
            L.append(f"- {r.id} [{r.family}] {r.status}: {r.note}")
            continue
        h = f"x{r.headroom:.2f}" if r.headroom else "n/a"
        tag = "compounding" if r.compounding else "marginal"
        s = f"- {r.id} [{r.family}] {r.status}: floor {r.floor:.4g} -> ceiling {r.ceiling:.4g} ({h}, {tag})"
        if required is not None and r.floor is not None:
            b = break_even(r.floor, r.ceiling, required)
            s += f"; to reach {required:.4g} needs uptime {b['uptime']:.0%}" if b["uptime"] is not None and b["verdict"] != "never" else f"; {b['verdict']} even at 100% uptime"
        L.append(s)
    if joint:
        L.append(f"- joint (all on): {joint['joint']:.4g}; sum of single gains {joint['sum_of_single_gains']:.4g}, joint gain {joint['joint_gain']:.4g}, synergy {joint['synergy']:+.4g}")
    return "\n".join(L)
