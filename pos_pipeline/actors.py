"""Second actor per build (K1, docs/second-actor.md): registry access, effects -> PoB config, loud stub.

Nothing here invents game facts: which companion skill gives which effect comes only from data/actors.yaml, and
every effect maps to PoB config keys listed in data/actor_effects.yaml. A `pending` actor raises everywhere.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol, Sequence

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


def assumed_scenario(kind: str, assumed: Mapping[str, Any]) -> dict:
    """The scenario (data/squire_assumed.yaml) an opt-in spec names. Raises KeyError for another actor kind or an unknown id."""
    prof = data.squire_assumed()
    if kind != prof["kind"]:
        raise KeyError(f"assumed what-if exists only for {prof['kind']!r}, not {kind!r}")
    sc = prof["scenarios"]
    if assumed.get("scenario") not in sc:
        raise KeyError(f"unknown assumed scenario {assumed.get('scenario')!r}; known: {sorted(sc)}")
    return sc[assumed["scenario"]]


def assumed_banner(scenario: str | None = None) -> str:
    b = " ".join(data.squire_assumed()["banner"].split())
    return b + (f" Scenario: {scenario}." if scenario else "")


def actor(kind: str, assumed: Mapping[str, Any] | None = None) -> dict:
    """Registry entry. With `assumed` (the spec's opt-in) the pending Squire is overlaid by the ASSUMED profile (K5);
    without it a pending actor stays pending."""
    reg = data.actors()
    if kind not in reg:
        raise KeyError(f"unknown actor kind {kind!r}; known: {sorted(reg)}")
    if assumed is None:
        return reg[kind]
    assumed_scenario(kind, assumed)
    return {**reg[kind], **data.squire_assumed()["actor"], "requires": {}, "assumed": assumed["scenario"]}


def require_available(kind: str, assumed: Mapping[str, Any] | None = None) -> dict:
    a = actor(kind, assumed)
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
    a = require_available(comp.kind, comp.assumed)
    out: list[Effect] = []
    if comp.assumed is not None:   # K5: the scenario's effects, every one labelled ASSUMED; `uptime` overrides them all
        for e in assumed_scenario(comp.kind, comp.assumed)["effects"]:
            up = float(comp.assumed.get("uptime") or e.get("uptime", 1.0))
            out.append(make_effect(e["effect"], e.get("params"), up, e.get("source", "ASSUMED")))
        return out
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
    assumed: str | None = None        # K5: scenario id when the numbers rest on the assumed Squire profile

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


class SeparateBuildModel:
    """`separate_build` model (docs/second-actor.md section 3). The companion is its own PoB build; its effects reach the
    player as config options.

    `player_metric(xml, options)` returns the player's metric with `options` (the effect-driven config layered over
    the config profile; keys the effects do not set must be at their profile/off value). `companion_metric(xml)`
    returns the companion build's own metric, or None when it deals no damage. Effects with uptime < 1 are blended
    over every on/off combination (independent uptimes), at most `MAX_PARTIAL` of them."""
    MAX_PARTIAL = 4

    def __init__(self, kind: str, player_metric: Callable[[str, Mapping[str, Any]], float],
                 companion_metric: Callable[[str], float | None] | None = None, base: Mapping[str, Any] | None = None,
                 assumed: str | None = None):
        self.kind, self.player_metric, self.companion_metric, self.base = kind, player_metric, companion_metric, dict(base or {})
        self.assumed = assumed

    def evaluate(self, main_xml: str, companion_xml: str | None, effects: Sequence[Effect]) -> Combined:
        sure = [e for e in effects if e.uptime >= 1.0]
        part = [e for e in effects if e.uptime < 1.0]
        if len(part) > self.MAX_PARTIAL:
            raise ValueError(f"{len(part)} partial-uptime effects; at most {self.MAX_PARTIAL} (on/off combinations)")
        reset = reset_options(self.base, effects)
        without = self.player_metric(main_xml, {**reset})
        main = 0.0
        for mask in range(1 << len(part)):
            on = [e for i, e in enumerate(part) if mask >> i & 1]
            w = 1.0
            for i, e in enumerate(part):
                w *= e.uptime if mask >> i & 1 else 1.0 - e.uptime
            if w:
                opts = {**reset, **merge_options(self.base, [*sure, *on])}
                main += w * self.player_metric(main_xml, opts)
        comp = 0.0
        if companion_xml is not None and self.companion_metric is not None:
            comp = float(self.companion_metric(companion_xml) or 0.0)
        return Combined(main, comp, without, list(effects), blended=bool(part), assumed=self.assumed)


def reset_options(base: Mapping[str, Any] | None, effects: Sequence[Effect]) -> dict[str, Any]:
    """Off value for every option the effects touch: the config profile's value, else False (bool) / 0 (number).
    Lets a persistent engine config go back to 'effect off' between evaluations."""
    out: dict[str, Any] = {}
    for e in effects:
        for k, v in e.options.items():
            out[k] = (base or {}).get(k, False if isinstance(v, bool) else 0)
    return out


def model_for(kind: str, *, player_metric: Callable[[str, Mapping[str, Any]], float] | None = None,
              companion_metric: Callable[[str], float | None] | None = None,
              base: Mapping[str, Any] | None = None, assumed: Mapping[str, Any] | None = None) -> ActorModel:
    """The evaluation model for an actor. A pending actor gets the loud stub; `separate_build` needs the metric callables
    (the engine-backed ones live in orchestrate.engine_stages). `native_pob` waits for K4 (1.0 data)."""
    a = actor(kind, assumed)
    if a.get("status") != "available":
        return PendingActorModel(kind)
    if a.get("model") == "separate_build":
        if player_metric is None:
            raise ValueError(f"actor {kind!r} uses separate_build: player_metric is required")
        return SeparateBuildModel(kind, player_metric, companion_metric, base, assumed=(assumed or {}).get("scenario"))
    raise NotImplementedError(f"actor {kind!r} is available but model {a.get('model')!r} is not built (K4, needs 1.0 data)")
