"""Two-gear-set search tests (K3). All fakes: no engine, pool or catalogue needed (runs without LuaJIT)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_pipeline import data  # noqa: E402
from pos_pipeline.actors import ActorUnavailable  # noqa: E402
from pos_pipeline.gear import Affix, GearSearcher, _Floors  # noqa: E402
from pos_pipeline.gear_actors import search_two_actors, split_budgets  # noqa: E402
from pos_tiers.price import AnchorSumModel  # noqa: E402
from pos_tiers.tiers import TierTable  # noqa: E402

BASE = {"weapon": "wbase", "amulet": "abase", "body_armour": "bbase"}
KIND_OF_BASE = {"wbase": "weapon", "abase": "amulet", "bbase": "body_armour"}


class FakeSearcher(GearSearcher):
    """Searcher over a toy model: an item is `base;group:value;...`, a build is `slot=item|slot=item`.
    Metric `M` sums `dmg*` values times `scale`; stat `Res` sums `res` values. Cost comes from the real tier table."""

    def __init__(self, scale: float, floors=None, metric="M"):
        self.t = TierTable.load()
        self.metric, self.floors, self.scale = metric, _Floors(floors), scale
        self.keys = (metric, "Res")
        self.uniques, self.counts, self.rejected, self.notes = {}, {"evals": 0, "cached": 0, "failures": 0}, [], []
        self.price_model = AnchorSumModel(self.t)
        self.shortlist, self.beam, self.roll, self.ilvl = 8, 2, 0.5, 82

    def affix_options(self, base):
        o = {}
        for g, v in (("dmgA", 10), ("dmgB", 7), ("dmgC", 4)):
            o[g] = [Affix(g, 1, f"{g}1", "Prefix", (f"{g}:{v}",), self.t.affix_points(g, 1)),
                    Affix(g, 3, f"{g}3", "Prefix", (f"{g}:{v // 2}",), self.t.affix_points(g, 3))]
        o["res"] = [Affix("res", 1, "res1", "Suffix", ("res:40",), self.t.affix_points("res", 1))]
        return o

    def raw(self, base, affixes):
        return ";".join([base, *(l for a in affixes for l in a.lines)])

    def _best_unique(self, *a, **k):
        return None, None

    def _slot_of_base(self, base):
        return KIND_OF_BASE.get(base)

    @staticmethod
    def _items(xml):
        return dict(p.split("=", 1) for p in xml.split("|") if p)

    def _stat(self, xml):
        m = r = 0.0
        for raw in self._items(xml).values():
            for tok in raw.split(";")[1:]:
                g, v = tok.split(":")
                m += float(v) if g.startswith("dmg") else 0.0
                r += float(v) if g == "res" else 0.0
        return {self.metric: m * self.scale, "Res": r}

    def score(self, xml, slot, raws):
        out = []
        for r in raws:
            self.counts["evals"] += 1
            st = self._stat(self.equip(xml, slot, r))
            out.append((-self.floors.deficit(st), st[self.metric]))
        return out

    def equip(self, xml, slot, raw):
        d = self._items(xml)
        d[slot] = raw
        return "|".join(f"{k}={v}" for k, v in d.items())

    def stats(self, xml):
        return self._stat(xml)


@pytest.fixture
def squire(monkeypatch):
    reg = {"squire": {"status": "available", "gear_slots": ["weapon", "body_armour"], "budget_share": 0.3,
                      "max_skills": 1, "model": "separate_build", "skill_effects": {}}}
    monkeypatch.setattr(data, "actors", lambda: reg)
    return reg


def run(player, comp, tier="mid", **kw):
    return search_two_actors(player, comp, "", "", tier, BASE, {"weapon": "wbase", "body_armour": "bbase"},
                             slots=("weapon", "amulet"), **kw)


def test_pending_actor_fails_loudly():
    with pytest.raises(ActorUnavailable) as e:
        run(FakeSearcher(1.0), FakeSearcher(1.0))        # real registry: squire is pending
    assert "squire" in str(e.value) and e.value.unknowns


def test_budget_split_conserves_total_and_namespaces(squire):
    p = FakeSearcher(1.0)
    b = split_budgets("mid", ("weapon", "amulet"), ("weapon", "body_armour"), 0.3, p, "squire")
    assert set(b) == {"weapon", "amulet", "squire.weapon", "squire.body_armour"}
    comp = b["squire.weapon"] + b["squire.body_armour"]
    assert comp == pytest.approx(0.3 * 160)
    assert b["squire.weapon"] / b["squire.body_armour"] == pytest.approx(0.28 / 0.16)     # tier-table proportions
    assert b["weapon"] == pytest.approx(0.7 * 160 * 0.28) and b["amulet"] == pytest.approx(0.7 * 160 * 0.12)


def test_uncapped_tier_has_no_budgets(squire):
    b = split_budgets("mirror", ("weapon",), ("weapon",), 0.3, FakeSearcher(1.0), "squire")
    assert b == {"weapon": None, "squire.weapon": None}


@pytest.mark.parametrize("share", [0.0, 1.0, -0.1, 1.5])
def test_bad_share(squire, share):
    with pytest.raises(ValueError, match="budget_share"):
        run(FakeSearcher(1.0), FakeSearcher(1.0), share=share)


def test_share_required(squire):
    squire["squire"]["budget_share"] = None
    with pytest.raises(ValueError, match="budget_share"):
        run(FakeSearcher(1.0), FakeSearcher(1.0))


def test_slot_validation(squire):
    with pytest.raises(ValueError, match="not in actor"):
        run(FakeSearcher(1.0), FakeSearcher(1.0), comp_slots=("amulet",))
    with pytest.raises(ValueError, match="does not fit"):
        search_two_actors(FakeSearcher(1.0), FakeSearcher(1.0), "", "", "mid", BASE, {"weapon": "abase", "body_armour": "bbase"},
                          slots=("weapon",))
    with pytest.raises(ValueError, match="no base"):
        search_two_actors(FakeSearcher(1.0), FakeSearcher(1.0), "", "", "mid", BASE, {"weapon": "wbase"}, slots=("weapon",))


def test_search_moves_points_to_the_actor_that_earns_more(squire):
    p, c = FakeSearcher(1.0), FakeSearcher(50.0)      # a companion point is worth 50x a player point
    r = run(p, c, tier="budget", realloc_rounds=6)
    init = split_budgets("budget", ("weapon", "amulet"), ("weapon", "body_armour"), 0.3, p, "squire")
    assert sum(r.slot_budgets.values()) == pytest.approx(sum(init.values()))  # reallocation conserves points
    comp = lambda b: sum(v for k, v in b.items() if "." in k)                 # noqa: E731
    assert comp(r.slot_budgets) > comp(init) + 1e-9                           # budget flowed to the companion
    assert any(n.startswith("moved") for n in r.notes)
    assert r.value > r.baseline and r.value == pytest.approx(r.player_value + r.companion_value)
    for k, it in r.items.items():
        assert it.points <= r.slot_budgets[k] + 1e-9
    assert set(r.items) == {"weapon", "amulet", "squire.weapon", "squire.body_armour"}
    assert r.points_main == pytest.approx(sum(it.points for k, it in r.items.items() if "." not in k))
    assert set(r.lanes) == {"player", "squire"}
    assert r.lanes["squire"].items["weapon"] is r.items["squire.weapon"]


def test_points_flow_to_player_when_companion_is_worthless(squire):
    r = run(FakeSearcher(1.0), FakeSearcher(0.0), tier="budget", realloc_rounds=6)
    comp_budget = sum(v for k, v in r.slot_budgets.items() if "." in k)
    assert comp_budget < 0.3 * 60 - 1e-9
    assert r.companion_value == 0.0 and r.player_value > 0


def test_floors_apply_to_player_only(squire):
    p = FakeSearcher(1.0, floors={"Res": 40})
    c = FakeSearcher(1.0)                               # no floor on the companion
    r = run(p, c, realloc_rounds=0)
    assert r.floors_met and r.lanes["player"].stats["Res"] >= 40
    assert r.lanes["squire"].stats["Res"] == 0 or r.lanes["squire"].floors_met


def test_floors_rank_ahead_of_metric(squire):
    p = FakeSearcher(1.0, floors={"Res": 40})
    r = run(p, FakeSearcher(1.0), realloc_rounds=0)
    assert any(a.group == "res" for k, it in r.items.items() if "." not in k for a in it.affixes)


def test_uncapped_runs_without_reallocation(squire):
    r = run(FakeSearcher(1.0), FakeSearcher(1.0), tier="mirror")
    assert r.budget is None and all(v is None for v in r.slot_budgets.values()) and r.value > r.baseline
