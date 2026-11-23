"""Support search (G5, docs/supports.md): choose the support gems for the main skill's socket group.

Single-swap deltas for every eligible support, then a beam search over the best of them up to the socket
limit. Eligibility (skill-type requirements incl. `add_types`, one support per `family`, no duplicates) is
enforced here because PoB silently ignores a duplicate / family clash / type-incompatible support while
still counting it as socketed (measured, docs/supports.md): such a candidate would score as a free no-op.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Collection, Sequence

from pos_catalogue import Catalogue
from pos_catalogue.catalogue import can_support
from pos_pool.pool import EnginePool, Job

from . import data
from .assemble import _gem_line

DEFAULT_BEAM = 5
DEFAULT_TOP = 12
OUTLIER_FACTOR = 3.0  # a single support adding more than this x the baseline is flagged for audit
MIN_GAIN = 1e-9  # relative; a support must beat its parent set by more than this to be kept


@dataclass
class Scored:
    supports: tuple[str, ...]          # catalogue support ids, in socket order
    value: float | None = None         # metric value; None = evaluation failed
    stats: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class SupportSearch:
    skill: str
    metric: str
    baseline: Scored                   # fixed supports only
    singles: list[tuple[str, float | None]]   # (support id, delta vs baseline), best first; None = failed
    best: Scored
    free_slots: int
    evals: int = 0                     # distinct candidate sets submitted to the pool
    cached: int = 0
    failures: int = 0
    no_effect: list[str] = field(default_factory=list)   # eligible supports whose single swap changed nothing
    outliers: list[str] = field(default_factory=list)    # singles worth > OUTLIER_FACTOR x baseline: audit before trusting
    notes: list[str] = field(default_factory=list)

    @property
    def gain(self) -> float:
        b = self.baseline.value or 0.0
        return ((self.best.value or 0.0) - b) / b if b else 0.0


def effective_types(skill: dict, chosen: Sequence[dict]) -> set[str] | None:
    """Skill types after the chosen supports' `add_types`, or None if some chosen support is not applicable
    (order-insensitive fixed point, same permissive rule as the validator)."""
    types = set(skill.get("skill_types") or [])
    pending = list(chosen)
    progress = True
    while pending and progress:
        progress = False
        for e in list(pending):
            if can_support(e, {"skill_types": sorted(types)}):
                types |= set(e.get("add_types") or [])
                pending.remove(e)
                progress = True
    return None if pending else types


def compatible(skill: dict, chosen: Sequence[dict]) -> bool:
    """True if `chosen` supports are mutually allowed: all apply to the skill, no duplicate id, no shared family."""
    ids = [e["id"] for e in chosen]
    if len(set(ids)) != len(ids):
        return False
    seen: set[str] = set()
    for e in chosen:
        fam = set(e.get("family") or [])
        if fam & seen:
            return False
        seen |= fam
    return effective_types(skill, chosen) is not None


def is_triggered(entry: dict) -> bool:
    """True for supports that grant a triggered skill (catalogue tag `Trigger`). PoB adds such a skill to
    `FullDPS` without any trigger-rate or condition scaling (docs/supports.md, Fiery Death audit)."""
    return "Trigger" in [t.strip() for t in (entry.get("tags") or "").split(",")]


def has_unmodelled_cost(entry: dict) -> bool:
    """True for supports whose cost PoB does not model: a Glory requirement (Zerphi's Infamy; PoB-PoE2 at 601768b has
    no Glory). The engine counts their damage and not the cost, so like triggered supports they look free (I13 eval:
    the ablation's best stand-in for 5 key supports)."""
    return "Glory requirement" in (entry.get("description") or "")


def eligible(cat: Catalogue, skill: dict, fixed: Sequence[dict], allow_triggered: Collection[str] | None = None) -> list[dict]:
    """Supports that may join `fixed` on `skill` (fixed ones excluded). Triggered-skill supports are left out
    unless their id is in `allow_triggered` (the config profile sets their trigger condition), and so are supports with
    an unmodelled cost (`has_unmodelled_cost`); `None` = no gate. A spec can still fix either kind explicitly."""
    fixed_ids = {e["id"] for e in fixed}
    return [s for s in cat.entries("support")
            if s["id"] not in fixed_ids and compatible(skill, [*fixed, s])
            and (allow_triggered is None or ((not is_triggered(s) or s["id"] in allow_triggered) and not has_unmodelled_cost(s)))]


def _job(cat: Catalogue, skill: dict, ids: Sequence[str], keys: tuple[str, ...], xml: str) -> Job:
    text = "\n".join(_gem_line(e["name"]) for e in [skill] + [cat.get("support", i) for i in ids])
    return Job(xml, mutations=(("paste_skill", {"text": text}),), stat_keys=keys, tag=tuple(ids))


def search_supports(
    cat: Catalogue,
    pool: EnginePool,
    xml: str,
    skill_id: str,
    fixed: Sequence[str] = (),
    metric: str = "TotalDPS",
    slots: int | None = None,
    beam: int = DEFAULT_BEAM,
    top: int = DEFAULT_TOP,
    extra_keys: Sequence[str] = (),
    allow_triggered: Collection[str] | None = (),
) -> SupportSearch:
    """Best support set for `skill_id` in seed build `xml`, maximising `metric` (a PoB stat key).

    `fixed` supports always stay (spec `fixed.supports`); the search fills the remaining slots
    (`slots` default: `data/rules.yaml` max_supports). Everything is scored by the pool, so results are cached.
    Triggered-skill supports (tag `Trigger`) are excluded unless listed in `allow_triggered` (support ids whose
    trigger condition the config profile sets); pass `None` to disable the gate. Set order is irrelevant to the score (sets are deduplicated as unordered).
    """
    skill = cat.get("skill", skill_id)
    fixed_e = [cat.get("support", i) for i in fixed]
    if not compatible(skill, fixed_e):
        raise ValueError("fixed supports are not mutually compatible for this skill")
    limit = slots if slots is not None else data.rules()["max_supports"]["value"]
    free = max(0, limit - len(fixed_e))
    keys = tuple(dict.fromkeys([metric, *extra_keys]))
    seen: dict[frozenset, Scored] = {}
    stats = {"evals": 0, "cached": 0, "failures": 0}

    def score(sets: list[tuple[str, ...]]) -> list[Scored]:
        todo = list({frozenset(s): s for s in sets if frozenset(s) not in seen}.values())
        results = pool.map([_job(cat, skill, s, keys, xml) for s in todo]) if todo else []
        for s, r in zip(todo, results):
            stats["evals"] += 1
            stats["cached"] += bool(r.cached)
            if not r.ok or r.main_skill != skill["name"]:
                stats["failures"] += 1
                seen[frozenset(s)] = Scored(s, None, {}, r.error or f"main skill {r.main_skill!r}")
            else:
                seen[frozenset(s)] = Scored(s, float(r.stats.get(metric) or 0.0), r.stats)
        return [seen[frozenset(s)] for s in sets]

    fixed_t = tuple(fixed)
    base = score([fixed_t])[0]
    out = SupportSearch(skill["name"], metric, base, [], base, free)
    if base.value is None:
        out.notes.append(f"baseline failed: {base.error}")
        return _finish(out, stats)
    if free == 0:
        return _finish(out, stats)

    cands = eligible(cat, skill, fixed_e, allow_triggered)
    if allow_triggered is not None:
        ids = {c["id"] for c in cands}
        gated = [e["name"] for e in eligible(cat, skill, fixed_e) if e["id"] not in ids]
        if gated:
            out.notes.append(f"{len(gated)} triggered-skill support(s) gated out (profile sets no trigger condition): "
                             + ", ".join(sorted(gated)))
    singles = score([(*fixed_t, c["id"]) for c in cands])
    eps = MIN_GAIN * max(1.0, abs(base.value))
    out.singles = sorted(((s.supports[-1], None if s.value is None else s.value - base.value) for s in singles),
                         key=lambda t: (t[1] is None, -(t[1] or 0.0), t[0]))
    out.no_effect = [i for i, d in out.singles if d is not None and abs(d) <= eps]
    out.outliers = [i for i, d in out.singles if d is not None and d > OUTLIER_FACTOR * abs(base.value)]
    if out.outliers:
        out.notes.append("single supports worth >%gx the baseline (audit against PoB before trusting): %s" % (
            OUTLIER_FACTOR, ", ".join(cat.get("support", i)["name"] for i in out.outliers)))
    pool_ids = [i for i, d in out.singles if d is not None and d > eps][:top]
    if not pool_ids:
        return _finish(out, stats)

    # Beam over the best singles. A level continues only while some set beats its parent set.
    by_id = {s.supports[-1]: s for s in singles}
    level = [by_id[i] for i in pool_ids[:beam]]
    best = max([base, *level], key=lambda s: s.value)
    for _ in range(free - 1):
        nxt: list[tuple[str, ...]] = []
        parent: dict[frozenset, float] = {}
        for st in level:
            for pid in pool_ids:
                if pid in st.supports:
                    continue
                ext = (*st.supports, pid)
                if compatible(skill, [cat.get("support", i) for i in ext]):
                    k = frozenset(ext)
                    if k not in parent:
                        nxt.append(ext)
                    parent[k] = max(parent.get(k, float("-inf")), st.value)
        if not nxt:
            break
        scored = [s for s in score(nxt) if s.value is not None]
        improved = [s for s in scored if s.value > parent[frozenset(s.supports)] + eps]
        if not improved:
            break
        level = sorted(improved, key=lambda s: -s.value)[:beam]
        if level[0].value > best.value:
            best = level[0]
    out.best = best
    left = free - (len(best.supports) - len(fixed_t))
    if left:
        out.notes.append(f"{left} slot(s) left empty: no remaining support improved {metric}")
    return _finish(out, stats)


def _finish(out: SupportSearch, stats: dict[str, int]) -> SupportSearch:
    out.evals, out.cached, out.failures = stats["evals"], stats["cached"], stats["failures"]
    return out
