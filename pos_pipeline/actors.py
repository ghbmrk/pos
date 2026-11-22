"""Second actor per build (K1, docs/second-actor.md): registry access, effects -> PoB config, loud stub.

Nothing here invents game facts: which companion skill gives which effect comes only from data/actors.yaml, and
every effect maps to PoB config keys listed in data/actor_effects.yaml. A `pending` actor raises everywhere.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence

from . import data
from .spec import Companion


class ActorUnavailable(RuntimeError):
    """The actor's mechanics are not sourced yet (status: pending). Carries the unknowns."""

    def __init__(self, kind: str, unknowns: Sequence[str] = ()):
        self.kind, self.unknowns = kind, list(unknowns)
        super().__init__(f"actor {kind!r} is pending: no sourced data, so no numbers. Unknowns: "
                         + ("; ".join(self.unknowns) or "unlisted"))


class EffectConflict(ValueError):
    """Two effects (or an effect and the config profile) set the same PoB option to different values."""


@dataclass(frozen=True)
class Effect:
    id: str
    options: dict[str, Any]
    uptime: float = 1.0
    source: str = ""


def actor(kind: str) -> dict:
    reg = data.actors()
    if kind not in reg:
        raise KeyError(f"unknown actor kind {kind!r}; known: {sorted(reg)}")
    return reg[kind]


def require_available(kind: str) -> dict:
    a = actor(kind)
    if a.get("status") != "available":
        raise ActorUnavailable(kind, a.get("unknowns") or [])
    return a


def make_effect(eid: str, params: Mapping[str, Any] | None = None, uptime: float = 1.0, source: str = "") -> Effect:
    """Effect id + params -> concrete PoB options. Raises on unknown id, missing/extra params, bad uptime."""
    reg = data.actor_effects()
    if eid not in reg:
        raise KeyError(f"unknown effect {eid!r}; known: {sorted(reg)}")
    spec = reg[eid]
    need, have = set(spec.get("params") or []), set(params or {})
    if need != have:
        raise ValueError(f"effect {eid!r} needs params {sorted(need)}, got {sorted(have)}")
    if not 0.0 < uptime <= 1.0:
        raise ValueError(f"effect {eid!r}: uptime {uptime} outside (0, 1]")
    opts: dict[str, Any] = {}
    for k, v in spec["options"].items():
        if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
            v = (params or {})[v[1:-1]]
        opts[k] = v
    return Effect(eid, opts, uptime, source)


def effects_for(comp: Companion, skill_ids: Sequence[str]) -> list[Effect]:
    """Effects the companion's skills (catalogue ids, resolved by the caller) apply to the player.
    Raises ActorUnavailable for a pending actor."""
    a = require_available(comp.kind)
    out: list[Effect] = []
    for sid in skill_ids:
        for e in (a.get("skill_effects") or {}).get(sid, []):
            out.append(make_effect(e["effect"], e.get("params"), float(e.get("uptime", 1.0)), e.get("source", "")))
    return out


def merge_options(base: Mapping[str, Any] | None, effects: Sequence[Effect], *, include: Sequence[str] | None = None) -> dict[str, Any]:
    """Config profile options + effect options. `include` limits which effect ids apply (None = all).
    Conflicting values raise EffectConflict; never a silent override."""
    out = dict(base or {})
    origin = {k: "config profile" for k in out}
    for e in effects:
        if include is not None and e.id not in include:
            continue
        for k, v in e.options.items():
            if k in out and out[k] != v:
                raise EffectConflict(f"{e.id} sets {k}={v!r} but {origin[k]} set {out[k]!r}")
            out[k], origin[k] = v, e.id
    return out


def blend(on: float, off: float, uptime: float) -> float:
    """Linear uptime blend of a metric evaluated with an effect on and off (approximation; reports flag it)."""
    if not 0.0 <= uptime <= 1.0:
        raise ValueError(f"uptime {uptime} outside [0, 1]")
    return uptime * on + (1.0 - uptime) * off


@dataclass
class Combined:
    main: float                       # player metric with effects applied (blended where uptime < 1)
    companion: float = 0.0            # companion's own metric, 0 if it deals no damage
    without_companion: float | None = None
    effects: list[Effect] = field(default_factory=list)
    blended: bool = False

    @property
    def total(self) -> float:
        return self.main + self.companion


class ActorModel(Protocol):
    def evaluate(self, main_xml: str, companion_xml: str | None, effects: Sequence[Effect]) -> Combined: ...


class PendingActorModel:
    """Stub for an actor without sourced data. Every call fails loudly."""

    def __init__(self, kind: str):
        self.kind = kind

    def evaluate(self, main_xml: str, companion_xml: str | None, effects: Sequence[Effect]) -> Combined:
        raise ActorUnavailable(self.kind, actor(self.kind).get("unknowns") or [])


def model_for(kind: str) -> ActorModel:
    """The evaluation model for an actor. Only the pending stub exists until K2/K4 add real models."""
    a = actor(kind)
    if a.get("status") != "available":
        return PendingActorModel(kind)
    raise NotImplementedError(f"actor {kind!r} is available but model {a.get('model')!r} is not built (K2)")
