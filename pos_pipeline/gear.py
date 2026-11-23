"""Gear search (G7, docs/gear.md): rare items for weapon, body armour and amulet inside a tier's point budget.

Per slot: screen every affix group spawnable on the chosen base with a single-affix item, keep the best few,
then build the item greedily (beam) from (group, rank) options whose points fit the slot budget, scoring each
round of candidates in one batched `eval_items` call (pool `slot_item` fast path). Slots are optimised in turn
with the others fixed (coordinate descent), then budget points move between slots while that raises the
metric. Optional floors (e.g. resistances, attributes) rank ahead of the metric.

Every affix is checked with PoB's `check_item` before use: a mod line PoB cannot parse contributes nothing,
so a candidate carrying one would score as a silent zero (docs/pipeline.md stage 2). Such mods are excluded.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from pos_catalogue import Catalogue
from pos_engine.engine import PobEngine
from pos_pool.pool import EnginePool, Job
from pos_tiers.price import AnchorSumModel, Estimate, GearItem
from pos_tiers.resolver import ModIndex, default_index
from pos_tiers.tiers import TierTable

# Search slot name -> PoB slot name, in search order. The two rings are separate search slots that share the tier
# table's `ring` allocation (half each); everything else maps one to one.
SLOTS = {"weapon": "Weapon 1", "body_armour": "Body Armour", "amulet": "Amulet", "ring_1": "Ring 1",
         "ring_2": "Ring 2", "helmet": "Helmet", "gloves": "Gloves", "boots": "Boots", "belt": "Belt"}
SLOT_KIND = {"ring_1": "ring", "ring_2": "ring"}          # search slot -> tier-table slot / base kind
# Catalogue base `type` -> tier-table slot kind (weapons are recognised separately).
BASE_TYPE_KIND = {"Body Armour": "body_armour", "Amulet": "amulet", "Ring": "ring", "Helmet": "helmet",
                  "Gloves": "gloves", "Boots": "boots", "Belt": "belt"}
# Floors for a build with every slot searched: resistance caps and attribute requirements.
STANDARD_FLOORS: dict[str, float | str] = {"FireResist": 75, "ColdResist": 75, "LightningResist": 75,
                                           "Str": "ReqStr", "Dex": "ReqDex", "Int": "ReqInt"}
MAX_PREFIX = MAX_SUFFIX = 3     # PoE2 rare explicit limits
ITEM_LEVEL = 82                 # assumed max drop item level (unverified); mods above it are excluded
ROLL = 0.5                      # where in a mod's (min-max) range the value is taken; PoB's own default is 0.5
DEFAULT_SHORTLIST = 8
DEFAULT_BEAM = 2
DEFAULT_PASSES = 2
DEFAULT_REALLOC_ROUNDS = 4
REALLOC_STEP = 0.1              # share of the searched slots' total budget moved per reallocation step
MIN_GAIN = 1e-9                 # relative improvement needed to keep a change
UNIQUE_PRICES = Path(__file__).resolve().parents[1] / "data" / "unique_prices.yaml"

_RANGE = re.compile(r"\((-?\d+(?:\.\d+)?)-(-?\d+(?:\.\d+)?)\)")


def roll_line(line: str, roll: float = ROLL) -> str:
    """Replace each `(min-max)` range with the value at `roll` (integers stay integers, as in PoB)."""
    def sub(m: re.Match) -> str:
        lo, hi = m.group(1), m.group(2)
        v = float(lo) + (float(hi) - float(lo)) * roll
        if "." in lo or "." in hi:
            return f"{v:.2f}".rstrip("0").rstrip(".")
        return str(int(v + 0.5) if v >= 0 else -int(-v + 0.5))
    return _RANGE.sub(sub, line)


def spawnable(mod: dict, tags: Sequence[str]) -> bool:
    """Game rule: the first weightKey present on the base decides the weight."""
    have = set(tags)
    for k, v in zip(mod["keys"], mod["vals"]):
        if k in have:
            return v > 0
    return False


@dataclass(frozen=True)
class Affix:
    group: str
    rank: int          # 1 = highest-level tier of the group spawnable on this base (pricing rank)
    mod_id: str
    type: str          # Prefix | Suffix
    lines: tuple[str, ...]
    points: float


@dataclass
class Chosen:
    slot: str
    base: str
    affixes: tuple[Affix, ...] = ()
    unique: str | None = None
    unique_band: str | None = None
    points: float = 0.0
    raw: str = ""

    def gear_item(self) -> GearItem:
        if self.unique:
            return GearItem(kind_of(self.slot), unique_band=self.unique_band)
        return GearItem(kind_of(self.slot), [(a.group, a.rank) for a in self.affixes])


@dataclass
class GearSearch:
    tier: str
    metric: str
    budget: float | None                  # points for the searched slots together (None = uncapped)
    slot_budgets: dict[str, float | None]
    items: dict[str, Chosen]
    baseline: float | None                # metric with the bases unmodded
    value: float | None
    floors_met: bool
    deficit: float
    stats: dict[str, Any]
    xml: str
    price: Estimate | None = None
    evals: int = 0
    cached: int = 0
    failures: int = 0
    rejected_unparsed: list[str] = field(default_factory=list)   # mod ids PoB cannot parse
    notes: list[str] = field(default_factory=list)


class _Floors:
    """Floors as `{stat: number | other stat key}`, e.g. {"FireResist": 75, "Int": "ReqInt"}."""

    def __init__(self, floors: Mapping[str, float | str] | None):
        self.f = dict(floors or {})

    @property
    def keys(self) -> list[str]:
        return [*self.f, *(v for v in self.f.values() if isinstance(v, str))]

    def deficit(self, stats: Mapping[str, Any]) -> float:
        d = 0.0
        for k, v in self.f.items():
            need = float(stats.get(v) or 0.0) if isinstance(v, str) else float(v)
            d += max(0.0, need - float(stats.get(k) or 0.0))
        return d


def kind_of(slot: str) -> str:
    return SLOT_KIND.get(slot, slot)


def load_unique_prices(path: Path = UNIQUE_PRICES) -> dict[str, str]:
    """Unique name -> price band (key of tiers.yaml unique_bands). Hand-set until poe.ninja is reachable."""
    if not path.exists():
        return {}
    return dict((yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("uniques") or {})


class GearSearcher:
    def __init__(self, cat: Catalogue, pool: EnginePool, engine: PobEngine, table: TierTable | None = None,
                 index: ModIndex | None = None, metric: str = "TotalDPS",
                 floors: Mapping[str, float | str] | None = None, extra_keys: Sequence[str] = (),
                 shortlist: int = DEFAULT_SHORTLIST, beam: int = DEFAULT_BEAM, roll: float = ROLL,
                 item_level: int = ITEM_LEVEL, unique_prices: Mapping[str, str] | None = None, objective: Any = None):
        self.cat, self.pool, self.eng = cat, pool, engine
        self.objective = objective or None     # pos_pipeline.objective.Objective: scores every candidate on the benchmarks (L1)
        self._fight_xmls: dict[tuple[str, str], str] = {}
        self.t = table or TierTable.load()
        self.idx = index or default_index()
        self.metric = metric
        self.floors = _Floors(floors)
        if self.objective:
            self.floors = _Floors(self.objective.floors)
        self.keys = tuple(dict.fromkeys([metric, *self.floors.keys, *extra_keys, *(self.objective.keys if self.objective else ())]))
        self.shortlist, self.beam, self.roll, self.ilvl = shortlist, beam, roll, item_level
        self.uniques = dict(unique_prices if unique_prices is not None else load_unique_prices())
        self.price_model = AnchorSumModel(self.t)
        self.counts = {"evals": 0, "cached": 0, "failures": 0}
        self._parse_ok: dict[str, bool] = {}
        self._implicit: dict[str, list[str]] = {}
        self.rejected: list[str] = []
        self.notes: list[str] = []

    # ---- items -------------------------------------------------------------------------------------------
    def _entry(self, kind: str, name: str) -> dict:
        e = self.cat.resolve(kind, name).entry
        if e is None:
            raise ValueError(f"{kind} {name!r} not found (or ambiguous) in catalogue {self.cat.pob_sha[:7]}")
        return e

    def _base(self, name: str) -> dict:
        return self._entry("base", name)

    def implicit(self, base: str) -> list[str]:
        if base not in self._implicit:
            r = self.eng.call("check_item", raw=f"Rarity: NORMAL\n{base}")
            if not r.get("ok"):
                raise ValueError(f"PoB does not recognise base {base!r}: {r.get('error')}")
            imp = r.get("implicit") or ""
            self._implicit[base] = [roll_line(x, self.roll) for x in imp.split("\n") if x.strip()]
        return self._implicit[base]

    def raw(self, base: str, affixes: Sequence[Affix]) -> str:
        imp = self.implicit(base)
        lines = ["Rarity: RARE", "pos candidate", base, f"Item Level: {self.ilvl}", f"Implicits: {len(imp)}", *imp]
        for a in affixes:
            lines += [roll_line(x, self.roll) for x in a.lines]
        return "\n".join(lines)

    def affix_options(self, base: str) -> dict[str, list[Affix]]:
        """group -> one Affix per distinct point cost (the best rank at that cost), best rank first.
        Only mods spawnable on the base, at or below the item level, and fully parsed by PoB."""
        tags = self._base(base)["tags"]
        groups: dict[str, list[tuple[str, dict]]] = {}
        for mid, m in self.idx.mods.items():
            if m["group"] and spawnable(m, tags):
                groups.setdefault(m["group"], []).append((mid, m))
        out: dict[str, list[Affix]] = {}
        for g, lst in groups.items():
            lst.sort(key=lambda x: (-x[1]["level"], x[0]))
            seen_cost: set[float] = set()
            opts = []
            for rank, (mid, m) in enumerate(lst, 1):
                if m["level"] > self.ilvl:
                    continue
                pts = self.t.affix_points(g, rank)
                if pts in seen_cost:
                    continue
                a = Affix(g, rank, mid, m["type"], tuple(m["text"]), pts)
                if not self._parses(base, a):
                    continue
                seen_cost.add(pts)
                opts.append(a)
            if opts:
                out[g] = opts
        return out

    def _parses(self, base: str, a: Affix) -> bool:
        if a.mod_id not in self._parse_ok:
            r = self.eng.call("check_item", raw=self.raw(base, [a]))
            ok = bool(r.get("ok")) and not r.get("unparsed")
            self._parse_ok[a.mod_id] = ok
            if not ok:
                self.rejected.append(a.mod_id)
        return self._parse_ok[a.mod_id]

    # ---- scoring -----------------------------------------------------------------------------------------
    def _fight_xml(self, xml: str, fight) -> str:
        """`xml` with the fight's PoB options baked into its config, so the slot_item fast path scores under them."""
        k = (hashlib.sha256(xml.encode()).hexdigest(), fight.bid)
        if k not in self._fight_xmls:
            self.eng.load_build_xml(xml)
            self.eng.set_config(options=fight.opts() or None)
            self._fight_xmls[k] = self.eng.get_xml()
        return self._fight_xmls[k]

    def key_of(self, xml: str) -> tuple[float, float]:
        """Objective key of a whole build: (-floor deficit, metric), or the benchmark objective's (-deficit, goal)."""
        if not self.objective:
            st = self.stats(xml)
            return (-self.floors.deficit(st), float(st.get(self.metric) or 0.0))
        # through the pool, not self.eng: every load_build_xml leaks engine memory (~30-50 MB) and this engine is long-lived
        rs = self.pool.map([Job(xml, mutations=self.objective.mutations(f), stat_keys=self.keys) for f in self.objective.fights])
        if any(not r.ok for r in rs):
            raise RuntimeError("objective evaluation failed: " + "; ".join(str(r.error) for r in rs if not r.ok))
        sts = [r.stats for r in rs]
        return self.objective.score(sts).key

    def score(self, xml: str, slot: str, raws: list[str]) -> list[tuple[float, float] | None]:
        """Objective per raw item in `slot` of `xml`: (-deficit, metric or goal); None = engine rejected it."""
        fx = [self._fight_xml(xml, f) for f in self.objective.fights] if self.objective else [xml]
        n_raw = len(raws)
        # fight-major order: consecutive jobs share one XML, so a worker keeps its loaded build (the slot_item fast path)
        res = self.pool.map([Job(x, stat_keys=self.keys, slot_item=(SLOTS[slot], r)) for x in fx for r in raws])
        out = []
        for n in range(n_raw):
            rs = [res[i * n_raw + n] for i in range(len(fx))]
            self.counts["evals"] += 1
            self.counts["cached"] += all(r.cached for r in rs)
            if any(not r.ok or not r.stats for r in rs):
                self.counts["failures"] += 1
                out.append(None)
            elif self.objective:
                out.append(self.objective.score([r.stats for r in rs]).key)
            else:
                out.append((-self.floors.deficit(rs[0].stats), float(rs[0].stats.get(self.metric) or 0.0)))
        return out

    def stats(self, xml: str) -> dict[str, Any]:
        self.eng.load_build_xml(xml)
        return self.eng.get_stats(list(self.keys))["stats"]

    def equip(self, xml: str, slot: str, raw: str) -> str:
        self.eng.load_build_xml(xml)
        r = self.eng.add_item(raw, slot=SLOTS[slot])
        if not r.get("ok"):
            raise ValueError(f"could not equip item in {slot}: {r.get('error')}")
        return self.eng.get_xml()

    # ---- one slot ----------------------------------------------------------------------------------------
    def best_item(self, xml: str, slot: str, base: str, budget: float | None,
                  options: dict[str, list[Affix]] | None = None, exclude_uniques: Sequence[str] = ()) -> tuple[Chosen, tuple[float, float] | None]:
        """Best rare (or priced unique) for `slot` within `budget` points, others fixed as in `xml`."""
        opts = options if options is not None else self.affix_options(base)
        empty = Chosen(slot, base, raw=self.raw(base, []))
        # Screen: each group alone at its best affordable rank.
        single = {g: next((a for a in o if budget is None or a.points <= budget), None) for g, o in opts.items()}
        single = {g: a for g, a in single.items() if a is not None}
        groups = sorted(single)
        scored = self.score(xml, slot, [empty.raw] + [self.raw(base, [single[g]]) for g in groups])
        base_obj = scored[0]
        if base_obj is None:
            raise ValueError(f"engine rejected the unmodded {base} in {slot}")
        ranked = sorted(((s, g) for s, g in zip(scored[1:], groups) if s is not None and s > base_obj),
                        key=lambda t: (t[0], t[1]), reverse=True)
        short = [g for _, g in ranked[: self.shortlist]]

        best, best_obj = empty, base_obj
        level: list[tuple[tuple[Affix, ...], tuple[float, float]]] = [((), base_obj)]
        seen: set[frozenset] = {frozenset()}
        while level:
            cands: list[tuple[Affix, ...]] = []
            parent: dict[frozenset, tuple[float, float]] = {}
            for state, obj in level:
                used = {a.group for a in state}
                spent = sum(a.points for a in state)
                npre = sum(a.type == "Prefix" for a in state)
                nsuf = len(state) - npre
                for g in short:
                    if g in used:
                        continue
                    for a in opts[g]:
                        if (a.type == "Prefix" and npre >= MAX_PREFIX) or (a.type == "Suffix" and nsuf >= MAX_SUFFIX):
                            continue
                        if budget is not None and spent + a.points > budget + 1e-9:
                            continue
                        ext = (*state, a)
                        k = frozenset(ext)
                        if k not in seen:
                            seen.add(k)
                            cands.append(ext)
                        parent[k] = max(parent.get(k, obj), obj)
            if not cands:
                break
            objs = self.score(xml, slot, [self.raw(base, c) for c in cands])
            improved = []
            for c, o in zip(cands, objs):
                if o is None:
                    continue
                p = parent[frozenset(c)]
                if o[0] > p[0] or (o[0] == p[0] and o[1] > p[1] + MIN_GAIN * max(1.0, abs(p[1]))):
                    improved.append((c, o))
            improved.sort(key=lambda t: (t[1], -sum(a.points for a in t[0])), reverse=True)
            level = improved[: self.beam]
            if level and level[0][1] > best_obj:
                st = level[0][0]
                best_obj = level[0][1]
                best = Chosen(slot, base, tuple(sorted(st, key=lambda a: (a.type, a.group))),
                              points=sum(a.points for a in st), raw=self.raw(base, st))
        u, u_obj = self._best_unique(xml, slot, budget, exclude_uniques)
        if u is not None and u_obj is not None and u_obj > best_obj:
            return u, u_obj
        return best, best_obj

    def _best_unique(self, xml: str, slot: str, budget: float | None, exclude: Sequence[str] = ()) -> tuple[Chosen | None, tuple[float, float] | None]:
        bands = self.t.raw["unique_bands"]
        cands: list[Chosen] = []
        for name, band in sorted(self.uniques.items()):
            pts = float(bands[band]["points"])
            if budget is not None and pts > budget:
                continue
            try:
                e = self._entry("unique", name)
            except ValueError:
                self.notes.append(f"unique_prices: {name!r} not in catalogue")
                continue
            if self._slot_of_base(e.get("base")) != kind_of(slot) or e["name"] in exclude:
                continue
            t = self.eng.call("unique_text", name=e["name"], base=e.get("base"))
            if not t.get("ok"):
                continue
            raw = t["raw"] if t["raw"].lstrip().lower().startswith("rarity:") else "Rarity: UNIQUE\n" + t["raw"]
            chk = self.eng.call("check_item", raw=raw)
            if not chk.get("ok") or chk.get("unparsed"):
                self.notes.append(f"unique {name} skipped: PoB cannot parse "
                                  f"{[u['line'] for u in chk.get('unparsed') or []] or 'the item'}")
                continue
            cands.append(Chosen(slot, e.get("base") or "", unique=e["name"], unique_band=band, points=pts, raw=raw))
        if not cands:
            return None, None
        objs = self.score(xml, slot, [c.raw for c in cands])
        best = max(((o, c) for o, c in zip(objs, cands) if o is not None), default=(None, None), key=lambda t: t[0])
        return best[1], best[0]

    def _slot_of_base(self, base: str | None) -> str | None:
        if not base:
            return None
        try:
            typ = self._base(base)["type"]
        except ValueError:
            return None
        if typ in BASE_TYPE_KIND:
            return BASE_TYPE_KIND[typ]
        b = self._base(base)
        weapon_tags = {"weapon", *self.t.slot_tags("weapon")}
        return "weapon" if b.get("weapon") or weapon_tags & set(b.get("tags", [])) else None

    def slot_budget(self, tier: str, slot: str) -> float | None:
        b = self.t.slot_budget(tier, kind_of(slot))
        if b is None or kind_of(slot) == slot:
            return b
        return b / sum(kind_of(s) == kind_of(slot) for s in SLOTS)   # rings: the `ring` share split over both

    # ---- whole search ------------------------------------------------------------------------------------
    def search(self, xml: str, tier: str, bases: Mapping[str, str], slots: Sequence[str] = tuple(SLOTS),
               passes: int = DEFAULT_PASSES, realloc_rounds: int = DEFAULT_REALLOC_ROUNDS) -> GearSearch:
        for s in slots:
            if s not in SLOTS:
                raise ValueError(f"slot {s!r} not searchable (supported: {', '.join(SLOTS)})")
            if s not in bases:
                raise ValueError(f"no base given for slot {s!r}")
            if self._slot_of_base(bases[s]) != kind_of(s):
                raise ValueError(f"base {bases[s]!r} does not fit slot {s!r}")
        total = self.t.budget(tier)
        budgets: dict[str, float | None] = {s: self.slot_budget(tier, s) for s in slots}
        opts = {s: self.affix_options(bases[s]) for s in slots}

        # Baseline: all searched slots hold the unmodded base.
        cur = xml
        for s in slots:
            cur = self.equip(cur, s, self.raw(bases[s], []))
        base_stats = self.stats(cur)
        baseline = float(base_stats.get(self.metric) or 0.0)
        items = {s: Chosen(s, bases[s], raw=self.raw(bases[s], [])) for s in slots}

        def others(items: dict[str, Chosen], s: str) -> list[str]:   # uniques are one per name
            return [c.unique for t, c in items.items() if t != s and c.unique]

        def descend(cur: str, items: dict[str, Chosen], budgets: dict[str, float | None]) -> tuple[str, dict[str, Chosen], tuple[float, float]]:
            for _ in range(passes):
                changed = False
                for s in slots:
                    ch, _ = self.best_item(cur, s, bases[s], budgets[s], opts[s], others(items, s))
                    if ch.raw != items[s].raw:
                        items = {**items, s: ch}
                        cur = self.equip(cur, s, ch.raw)
                        changed = True
                if not changed:
                    break
            return cur, items, self.key_of(cur)

        cur, items, obj = descend(cur, items, budgets)

        # Budget reallocation between the searched slots (capped tiers only).
        if total is not None and len(slots) > 1:
            step = REALLOC_STEP * sum(b for b in budgets.values() if b is not None)
            for _ in range(realloc_rounds):
                gains: dict[tuple[str, int], tuple[float, float]] = {}
                for s in slots:
                    for sign in (+1, -1):
                        b = budgets[s] + sign * step
                        if b < 0:
                            continue
                        _, o = self.best_item(cur, s, bases[s], b, opts[s], others(items, s))
                        if o is not None:
                            gains[(s, sign)] = o
                best_move, best_est = None, 0.0
                for give in slots:
                    for take in slots:
                        if give == take or (give, 1) not in gains or (take, -1) not in gains:
                            continue
                        up, down = gains[(give, 1)], gains[(take, -1)]
                        est = (up[0] - obj[0]) + (down[0] - obj[0]), (up[1] - obj[1]) + (down[1] - obj[1])
                        if est > (0.0, MIN_GAIN * max(1.0, abs(obj[1]))) and (best_move is None or est > best_est):
                            best_move, best_est = (give, take), est
                if best_move is None:
                    break
                give, take = best_move
                nb = {**budgets, give: budgets[give] + step, take: budgets[take] - step}
                ncur, nitems, nobj = descend(cur, items, nb)
                if nobj > obj:
                    cur, items, obj, budgets = ncur, nitems, nobj, nb
                    self.notes.append(f"moved {step:g} points {take} -> {give}")
                else:
                    break

        final = self.stats(cur)
        for s, ch in items.items():
            if not ch.unique:
                chk = self.eng.call("check_item", raw=ch.raw)
                if chk.get("unparsed"):
                    self.notes.append(f"{s}: final item has unparsed lines {chk['unparsed']}")
        price = self.price_model.price([c.gear_item() for c in items.values()])
        searched_total = None if total is None else sum(budgets.values())
        out = GearSearch(tier, self.metric, searched_total, budgets, items, baseline,
                         float(final.get(self.metric) or 0.0), self.floors.deficit(final) == 0,
                         self.floors.deficit(final), final, cur, price)
        out.evals, out.cached, out.failures = self.counts["evals"], self.counts["cached"], self.counts["failures"]
        out.rejected_unparsed = sorted(set(self.rejected))
        out.notes = list(dict.fromkeys(self.notes))
        if not out.floors_met:
            out.notes.append(f"floors not met (deficit {out.deficit:g}); other slots (G7b) must cover the rest")
        return out


def search_gear(cat: Catalogue, pool: EnginePool, engine: PobEngine, xml: str, tier: str,
                bases: Mapping[str, str], metric: str = "TotalDPS", **kw: Any) -> GearSearch:
    """Convenience wrapper: see GearSearcher. `kw` splits into searcher options and search() options."""
    search_kw = {k: kw.pop(k) for k in ("slots", "passes", "realloc_rounds") if k in kw}
    return GearSearcher(cat, pool, engine, metric=metric, **kw).search(xml, tier, bases, **search_kw)
