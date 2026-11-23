"""Loaders for the hand-authored YAML under data/ (profiles, metrics, limitations, rules)."""
from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[1] / "data"


@lru_cache(maxsize=None)
def _load(name: str) -> dict:
    return yaml.safe_load((DATA / name).read_text(encoding="utf-8"))


def profiles() -> dict[str, dict]:
    return _load("config_profiles.yaml")["profiles"]


def conditions() -> dict[str, dict]:
    return _load("config_profiles.yaml").get("conditions") or {}


def conditions_not_in_fight(names, kind: str) -> tuple[dict, list[str]]:
    """Options that switch off the declared conditions which cannot hold in a benchmark of `kind` (boss | pack), and
    their names. A condition without `fights` holds in both."""
    table = conditions()
    off: dict = {}
    dropped: list[str] = []
    for n in names or ():
        fights = table[n].get("fights")
        if fights and kind not in fights:
            dropped.append(n)
            off.update({k: (False if isinstance(v, bool) else 0) for k, v in table[n]["options"].items()})
    return off, dropped


def condition_options(names) -> dict:
    """PoB config options for declared condition names, merged in order (later names win)."""
    table = conditions()
    out: dict = {}
    for n in names or ():
        out.update(table[n]["options"])
    return out


def profile_hash(name: str) -> str:
    """Stable hash of a profile's options and custom mods; part of the result-cache key."""
    p = profiles()[name]
    canon = json.dumps({"options": p.get("options") or {}, "custom_mods": p.get("custom_mods") or ""}, sort_keys=True)
    return hashlib.sha256(canon.encode()).hexdigest()[:12]


def metrics() -> dict:
    return _load("metrics.yaml")


def limitations() -> list[dict]:
    return _load("limitations.yaml")["limitations"]


def rules() -> dict:
    return _load("rules.yaml")


def metric_for(skill_types: list[str]) -> dict:
    """Objective metric for a skill: {metric: key|None, note}. First matching rule in data/metrics.yaml wins."""
    have = set(skill_types or [])
    m = metrics()
    for r in m["rules"]:
        if r.get("any") and not have & set(r["any"]):
            continue
        if r.get("all") and not set(r["all"]) <= have:
            continue
        if r.get("none") and have & set(r["none"]):
            continue
        return {"metric": r["metric"], "note": r["note"]}
    return dict(m["default"])


def ideation() -> dict:
    return _load("ideation.yaml")


def actors() -> dict[str, dict]:
    return _load("actors.yaml")["actors"]


def squire_assumed() -> dict:
    """K5: the ASSUMED Squire profile (data/squire_assumed.yaml). Not game data; used only when a spec opts in."""
    return _load("squire_assumed.yaml")


def actor_effects() -> dict[str, dict]:
    return _load("actor_effects.yaml")["effects"]
