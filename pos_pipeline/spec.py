"""BuildSpec: the YAML contract between the LLM front and the pipeline. Pure structure; no game knowledge here."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class SpecError(ValueError):
    """Structural problem (wrong type, unknown key). Game-data problems are Issues from validate()."""


_TOP = {"pob_sha", "class", "ascendancy", "level", "main_skill", "fixed", "axes", "tiers", "config_profile", "objective", "benchmarks", "companion", "conditions"}
_FIXED = {"keystones", "notables", "uniques", "supports"}
_OBJ = {"maximise", "floors"}
_COMP = {"kind", "skills", "gear", "assumed"}


@dataclass
class CompanionSkill:
    gem: str
    supports: list[str] = field(default_factory=list)


@dataclass
class Companion:
    """Second actor (docs/second-actor.md): its own skills and gear bases. Effects come from data/actors.yaml."""
    kind: str
    skills: list[CompanionSkill] = field(default_factory=list)
    gear: dict[str, str] = field(default_factory=dict)
    assumed: dict[str, Any] | None = None   # K5 opt-in what-if: {scenario: id, uptime?: 0-1}; see data/squire_assumed.yaml


@dataclass
class BuildSpec:
    pob_sha: str
    class_: str
    ascendancy: str | None
    level: int
    main_skill: str
    supports: list[str] = field(default_factory=list)
    keystones: list[str] = field(default_factory=list)
    notables: list[str] = field(default_factory=list)
    uniques: list[str] = field(default_factory=list)
    axes: dict[str, list[str]] = field(default_factory=dict)
    tiers: list[str] = field(default_factory=list)
    config_profile: str = "pinnacle_boss"
    benchmarks: list[str] = field(default_factory=list)   # ids from data/benchmarks.yaml, scored per tier (B4)
    maximise: str = "auto"
    floors: dict[str, Any] = field(default_factory=lambda: {"resist_capped": True})
    companion: Companion | None = None
    conditions: list[str] = field(default_factory=list)   # names from data/config_profiles.yaml `conditions` (I11)


def _only(d: Any, allowed: set[str], where: str) -> dict:
    if not isinstance(d, dict):
        raise SpecError(f"{where} must be a mapping")
    extra = set(d) - allowed
    if extra:
        raise SpecError(f"{where}: unknown key(s) {sorted(extra)}; allowed {sorted(allowed)}")
    return d


def _strs(v: Any, where: str) -> list[str]:
    if v is None:
        return []
    if not isinstance(v, list) or not all(isinstance(x, str) and x for x in v):
        raise SpecError(f"{where} must be a list of non-empty strings")
    return list(v)


def _companion(v: Any) -> Companion | None:
    if v is None:
        return None
    c = _only(v, _COMP, "companion")
    if not isinstance(c.get("kind"), str) or not c["kind"]:
        raise SpecError("companion.kind must be a non-empty string")
    skills_raw = c.get("skills") or []
    if not isinstance(skills_raw, list):
        raise SpecError("companion.skills must be a list")
    skills = []
    for i, sk in enumerate(skills_raw):
        sk = _only(sk, {"gem", "supports"}, f"companion.skills[{i}]")
        if not isinstance(sk.get("gem"), str) or not sk["gem"]:
            raise SpecError(f"companion.skills[{i}].gem must be a non-empty string")
        skills.append(CompanionSkill(sk["gem"], _strs(sk.get("supports"), f"companion.skills[{i}].supports")))
    gear = c.get("gear") or {}
    if not isinstance(gear, dict) or not all(isinstance(k, str) and isinstance(b, str) and b for k, b in gear.items()):
        raise SpecError("companion.gear must be a mapping of slot -> base name")
    assumed = c.get("assumed")
    if assumed is not None:
        assumed = _only(assumed, {"scenario", "uptime"}, "companion.assumed")
        if not isinstance(assumed.get("scenario"), str) or not assumed["scenario"]:
            raise SpecError("companion.assumed.scenario must be a non-empty string")
        up = assumed.get("uptime")
        if up is not None and (isinstance(up, bool) or not isinstance(up, (int, float)) or not 0 < up <= 1):
            raise SpecError("companion.assumed.uptime must be a number in (0, 1]")
        assumed = dict(assumed)
    return Companion(c["kind"], skills, dict(gear), assumed)


def parse_spec(data: Any) -> BuildSpec:
    d = _only(data, _TOP, "spec")
    for req in ("pob_sha", "class", "level", "main_skill", "tiers"):
        if req not in d:
            raise SpecError(f"spec: missing required key {req!r}")
    if not isinstance(d["pob_sha"], str) or not d["pob_sha"]:
        raise SpecError("pob_sha must be a string (quote hex like 0123456 so YAML keeps it a string)")
    if not isinstance(d["class"], str):
        raise SpecError("class must be a string")
    if isinstance(d["level"], bool) or not isinstance(d["level"], int):
        raise SpecError("level must be an integer")
    ms = _only(d["main_skill"], {"gem"}, "main_skill")
    if not isinstance(ms.get("gem"), str):
        raise SpecError("main_skill.gem must be a string")
    fixed = _only(d.get("fixed") or {}, _FIXED, "fixed")
    obj = _only(d.get("objective") or {}, _OBJ, "objective")
    axes = {} if d.get("axes") is None else d["axes"]
    if not isinstance(axes, dict):
        raise SpecError("axes must be a mapping of axis name -> list of values")
    floors = obj.get("floors", {"resist_capped": True})
    if not isinstance(floors, dict):
        raise SpecError("objective.floors must be a mapping")
    if d.get("ascendancy") is not None and not isinstance(d["ascendancy"], str):
        raise SpecError("ascendancy must be a string")
    return BuildSpec(
        pob_sha=d["pob_sha"], class_=d["class"], ascendancy=d.get("ascendancy"), level=d["level"],
        main_skill=ms["gem"],
        supports=_strs(fixed.get("supports"), "fixed.supports"),
        keystones=_strs(fixed.get("keystones"), "fixed.keystones"),
        notables=_strs(fixed.get("notables"), "fixed.notables"),
        uniques=_strs(fixed.get("uniques"), "fixed.uniques"),
        axes={k: _strs(v, f"axes.{k}") for k, v in axes.items()},
        tiers=_strs(d["tiers"], "tiers"),
        config_profile=d.get("config_profile", "pinnacle_boss"), benchmarks=_strs(d.get("benchmarks"), "benchmarks"),
        maximise=obj.get("maximise", "auto"), floors=floors, companion=_companion(d.get("companion")), conditions=_strs(d.get("conditions"), "conditions"),
    )


def load_spec(path: Path | str) -> BuildSpec:
    return parse_spec(yaml.safe_load(Path(path).read_text(encoding="utf-8")))
