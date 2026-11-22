"""Gear search over two gear sets in one tier budget (K3, docs/second-actor.md section 5).

The player and a companion (Squire) each hold a gear set in their own build XML ("lane"). Companion slots are
namespaced (`squire.weapon`); the tier budget stays the build's total. Default split: the player's slots keep their
tier-table shares scaled by `1 - budget_share`, the companion's slots share `budget_share` in proportion to the
tier-table allocation of their slot kinds. Each lane is optimised with the G7 per-slot search (`GearSearcher.best_item`),
then points move between any two slots, across actors included, while the combined objective rises.

Objective: floors (player only) rank ahead of the metric; the metric is player metric + companion metric. The player
build XML is expected to carry the companion's effects already (K2 puts them into its config), so a companion slot
changes only the companion lane's own metric and the lanes are independent given their budgets.

A pending actor fails loudly: `require_available` raises ActorUnavailable (validator code `actor_unavailable`); no
number is produced for it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from . import actors
from .gear import MIN_GAIN, REALLOC_STEP, SLOTS, Chosen, GearSearch, GearSearcher, kind_of
from .gear import DEFAULT_PASSES, DEFAULT_REALLOC_ROUNDS

Obj = tuple[float, float]


@dataclass
class Lane:
    """One gear set: who wears it, the searcher that scores it (own metric, floors), its build and bases."""
    actor: str | None                 # None = the player; else the actor kind (namespace of its slots)
    searcher: GearSearcher
    xml: str
    bases: Mapping[str, str]
    slots: tuple[str, ...]

    def key(self, slot: str) -> str:
        return slot if self.actor is None else f"{self.actor}.{slot}"


@dataclass
class ActorGearSearch:
    tier: str
    budget: float | None
    share: float                           # companion's initial share of the budget
    slot_budgets: dict[str, float | None]  # namespaced slot -> points after reallocation
    items: dict[str, Chosen]               # namespaced slot -> item
    lanes: dict[str, GearSearch]           # "player" and the actor kind -> that lane's result
    baseline: float                        # combined metric with unmodded bases
    value: float                           # combined metric after search
    player_value: float
    companion_value: float
    floors_met: bool
    deficit: float
    points_main: float                   # points spent
    points_companion: float
    price: Any = None
    evals: int = 0
    cached: int = 0
    failures: int = 0
    notes: list[str] = field(default_factory=list)


def split_budgets(tier: str, player_slots: Sequence[str], comp_slots: Sequence[str], share: float,
                  player: GearSearcher, kind: str) -> dict[str, float | None]:
    """Initial namespaced slot budgets. Uncapped tiers give None everywhere."""
    if not 0.0 < share < 1.0:
        raise ValueError(f"budget_share {share} must be in (0, 1)")
    total = player.t.budget(tier)
    if total is None:
        return {**{s: None for s in player_slots}, **{f"{kind}.{s}": None for s in comp_slots}}
    alloc = player.t.raw["default_allocation"]
    weight = {s: alloc[kind_of(s)] / sum(kind_of(t) == kind_of(s) for t in SLOTS) for s in comp_slots}
    wsum = sum(weight.values())
    out: dict[str, float | None] = {s: (player.slot_budget(tier, s) or 0.0) * (1.0 - share) for s in player_slots}
    out.update({f"{kind}.{s}": total * share * weight[s] / wsum for s in comp_slots})
    return out


def _check_lane(lane: Lane) -> None:
    for s in lane.slots:
        if s not in SLOTS:
            raise ValueError(f"slot {lane.key(s)!r} not searchable (supported: {', '.join(SLOTS)})")
        if s not in lane.bases:
            raise ValueError(f"no base given for slot {lane.key(s)!r}")
        if lane.searcher._slot_of_base(lane.bases[s]) != kind_of(s):
            raise ValueError(f"base {lane.bases[s]!r} does not fit slot {lane.key(s)!r}")


def search_two_actors(player: GearSearcher, companion: GearSearcher, main_xml: str, comp_xml: str, tier: str,
                      bases: Mapping[str, str], comp_bases: Mapping[str, str], *, kind: str = "squire",
                      slots: Sequence[str] = tuple(SLOTS), comp_slots: Sequence[str] | None = None,
                      share: float | None = None, passes: int = DEFAULT_PASSES,
                      realloc_rounds: int = DEFAULT_REALLOC_ROUNDS) -> ActorGearSearch:
    """Search player and companion gear together. `player`/`companion` are GearSearchers with their own metric
    (`companion` has no floors). Raises ActorUnavailable while the actor is pending."""
    a = actors.require_available(kind)
    comp_slots = tuple(comp_slots if comp_slots is not None else a.get("gear_slots") or ())
    if not comp_slots:
        raise ValueError(f"actor {kind!r} has no gear slots to search")
    bad = [s for s in comp_slots if a.get("gear_slots") and s not in a["gear_slots"]]
    if bad:
        raise ValueError(f"companion slots {bad} not in actor {kind!r} gear_slots {a['gear_slots']}")
    share = share if share is not None else a.get("budget_share")
    if share is None:
        raise ValueError(f"actor {kind!r} has no budget_share and none was given")
    lanes = [Lane(None, player, main_xml, bases, tuple(slots)), Lane(kind, companion, comp_xml, comp_bases, comp_slots)]
    for ln in lanes:
        _check_lane(ln)
    total = player.t.budget(tier)
    budgets = split_budgets(tier, slots, comp_slots, share, player, kind)
    initial_share = share

    lane_of = {ln.key(s): (ln, s) for ln in lanes for s in ln.slots}
    keys = list(lane_of)
    opts = {k: ln.searcher.affix_options(ln.bases[s]) for k, (ln, s) in lane_of.items()}
    cur = {ln.actor: ln.xml for ln in lanes}
    items: dict[str, Chosen] = {}
    for ln in lanes:
        for s in ln.slots:
            cur[ln.actor] = ln.searcher.equip(cur[ln.actor], s, ln.searcher.raw(ln.bases[s], []))
            items[ln.key(s)] = Chosen(s, ln.bases[s], raw=ln.searcher.raw(ln.bases[s], []))
    base_stats = {ln.actor: ln.searcher.stats(cur[ln.actor]) for ln in lanes}
    baseline = sum(float(base_stats[ln.actor].get(ln.searcher.metric) or 0.0) for ln in lanes)

    def lane_obj(ln: Lane, xml: str) -> Obj:
        st = ln.searcher.stats(xml)
        return -ln.searcher.floors.deficit(st), float(st.get(ln.searcher.metric) or 0.0)

    def combine(objs: Mapping[str | None, Obj]) -> Obj:
        return sum(o[0] for o in objs.values()), sum(o[1] for o in objs.values())

    def others(items: Mapping[str, Chosen], ln: Lane, s: str) -> list[str]:
        return [items[ln.key(t)].unique for t in ln.slots if t != s and items[ln.key(t)].unique]

    def descend(cur: dict, items: dict, budgets: dict) -> tuple[dict, dict, dict]:
        cur, items = dict(cur), dict(items)
        for ln in lanes:
            for _ in range(passes):
                changed = False
                for s in ln.slots:
                    k = ln.key(s)
                    ch, _ = ln.searcher.best_item(cur[ln.actor], s, ln.bases[s], budgets[k], opts[k], others(items, ln, s))
                    if ch.raw != items[k].raw:
                        items[k] = ch
                        cur[ln.actor] = ln.searcher.equip(cur[ln.actor], s, ch.raw)
                        changed = True
                if not changed:
                    break
        return cur, items, {ln.actor: lane_obj(ln, cur[ln.actor]) for ln in lanes}

    cur, items, lobj = descend(cur, items, budgets)
    obj = combine(lobj)
    notes: list[str] = []

    if total is not None and len(keys) > 1:
        step = REALLOC_STEP * sum(b for b in budgets.values() if b is not None)
        for _ in range(realloc_rounds):
            gains: dict[tuple[str, int], Obj] = {}
            for k in keys:
                ln, s = lane_of[k]
                for sign in (+1, -1):
                    b = budgets[k] + sign * step
                    if b < 0:
                        continue
                    _, o = ln.searcher.best_item(cur[ln.actor], s, ln.bases[s], b, opts[k], others(items, ln, s))
                    if o is not None:
                        gains[(k, sign)] = (o[0] - lobj[ln.actor][0], o[1] - lobj[ln.actor][1])   # delta in its lane
            best_move, best_est = None, (0.0, 0.0)
            for give in keys:
                for take in keys:
                    if give == take or (give, 1) not in gains or (take, -1) not in gains:
                        continue
                    up, down = gains[(give, 1)], gains[(take, -1)]
                    est = (up[0] + down[0], up[1] + down[1])
                    if est > (0.0, MIN_GAIN * max(1.0, abs(obj[1]))) and (best_move is None or est > best_est):
                        best_move, best_est = (give, take), est
            if best_move is None:
                break
            give, take = best_move
            nb = {**budgets, give: budgets[give] + step, take: budgets[take] - step}
            ncur, nitems, nl = descend(cur, items, nb)
            nobj = combine(nl)
            if nobj > obj:
                cur, items, lobj, obj, budgets = ncur, nitems, nl, nobj, nb
                notes.append(f"moved {step:g} points {take} -> {give}")
            else:
                break

    results: dict[str, GearSearch] = {}
    for ln in lanes:
        name = ln.actor or "player"
        st = ln.searcher.stats(cur[ln.actor])
        its = {s: items[ln.key(s)] for s in ln.slots}
        bud = {s: budgets[ln.key(s)] for s in ln.slots}
        d = ln.searcher.floors.deficit(st)
        results[name] = GearSearch(
            tier, ln.searcher.metric, None if total is None else sum(bud.values()), bud, its,
            float(base_stats[ln.actor].get(ln.searcher.metric) or 0.0), float(st.get(ln.searcher.metric) or 0.0),
            d == 0, d, st, cur[ln.actor], ln.searcher.price_model.price([c.gear_item() for c in its.values()]))
        notes += ln.searcher.notes
        if d:
            notes.append(f"{name}: floors not met (deficit {d:g})")
    pl, co = results["player"], results[kind]
    price = player.price_model.price([c.gear_item() for c in items.values()])
    n = sum(ln.searcher.counts["evals"] for ln in lanes)
    c = sum(ln.searcher.counts["cached"] for ln in lanes)
    f = sum(ln.searcher.counts["failures"] for ln in lanes)
    return ActorGearSearch(
        tier, total, initial_share, budgets, items, results, baseline, pl.value + co.value, pl.value, co.value,
        pl.floors_met, pl.deficit, sum(i.points for s, i in items.items() if "." not in s),
        sum(i.points for s, i in items.items() if "." in s), price, n, c, f, list(dict.fromkeys(notes)))
