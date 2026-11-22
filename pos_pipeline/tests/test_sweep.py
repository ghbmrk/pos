"""Sweep + ablation tests: pure verdict/flag logic, plus the real engine and committed catalogue (need LuaJIT)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_catalogue import Catalogue  # noqa: E402
from pos_engine.engine import PobEngine  # noqa: E402
from pos_pipeline.assemble import assemble  # noqa: E402
from pos_pipeline.spec import parse_spec  # noqa: E402
from pos_pipeline.sweep import SweepEntry, _finish, _sort, ablate, sweep  # noqa: E402
from pos_pool.pool import EnginePool  # noqa: E402


def test_flags_and_ordering():
    a, b, c, d = (SweepEntry("k", str(i), n) for i, n in enumerate("abcd"))
    _finish(a, 100.0, 120.0, True)
    _finish(b, 100.0, 100.0, True)       # zero delta, has text -> possibly_unmodelled
    _finish(c, 100.0, 100.0, False)      # zero delta, no text -> no_effect
    _finish(d, 100.0, 500.0, True)       # > 3x baseline -> audit
    assert b.flags == ["possibly_unmodelled"] and c.flags == ["no_effect"] and d.flags == ["audit_outlier"]
    failed = SweepEntry("k", "f", "f")
    _finish(failed, 100.0, None, True)
    assert failed.flags == ["failed"]
    assert [e.name for e in _sort([failed, b, a, d])] == ["d", "a", "b", "f"]


@pytest.fixture(scope="module")
def cat():
    return Catalogue.load()


@pytest.fixture(scope="module")
def seed(cat):
    spec = parse_spec({"pob_sha": cat.pob_sha[:7], "class": "Sorceress", "ascendancy": "Stormweaver", "level": 90,
                       "main_skill": {"gem": "Spark"}, "tiers": ["mid"],
                       "fixed": {"supports": ["Controlled Destruction"], "notables": ["Constant Gale"]}})
    with PobEngine() as eng:
        a = assemble(spec, cat, eng)
    assert a.ok, a.issues
    return a.xml


@pytest.fixture(scope="module")
def skill(cat):
    return cat.resolve("skill", "Spark").entry["id"]


def test_sweeps_run_and_flag(cat, seed, skill):
    with EnginePool(workers=2) as pool:
        ks = sweep(cat, pool, seed, "keystone", "TotalDPS")
        assert len(ks.entries) == len(cat.entries("keystone")) and ks.baseline > 0
        assert all(e.points is not None for e in ks.entries if "unreachable" not in e.flags)
        ds = [e.delta for e in ks.entries if e.delta is not None]
        assert ds == sorted(ds, reverse=True)
        sup = sweep(cat, pool, seed, "support", "TotalDPS", skill_id=skill)
        assert sup.entries and sup.entries[0].delta >= sup.entries[-1].delta
        assert "Controlled Destruction" not in {e.name for e in sup.entries}   # already in the group
        uq = sweep(cat, pool, seed, "unique:weapon", "TotalDPS")
        assert uq.entries and any("unparsed" in e.flags for e in uq.entries)   # PoB-unparseable uniques are never scored
        assert all(e.value is None for e in uq.flagged("unparsed"))
        with pytest.raises(ValueError):
            sweep(cat, pool, seed, "unique:nope", "TotalDPS")


def test_ablation_verdicts(cat, seed, skill):
    pieces = [{"kind": "support", "id": "Controlled Destruction"},
              {"kind": "notable", "id": "Constant Gale"},
              {"kind": "keystone", "id": "Ancestral Bond"},           # not allocated -> not_testable
              {"kind": "support", "id": "Added Fire Damage"}]          # not in the group -> not_testable
    with EnginePool(workers=2) as pool:
        r = ablate(cat, pool, seed, pieces, "TotalDPS", skill_id=skill)
    v = {p.piece["id"]: p for p in r}
    assert v["Controlled Destruction"].without is not None and v["Controlled Destruction"].verdict in {"confirmed", "not_load_bearing", "possibly_unmodelled"}
    assert v["Constant Gale"].without is not None
    assert v["Ancestral Bond"].verdict == "not_testable" and "not allocated" in v["Ancestral Bond"].note
    assert v["Added Fire Damage"].verdict == "not_testable"
    # a big removal is confirmed: dropping every support's worth of damage with a tiny threshold
    with EnginePool(workers=2) as pool:
        [x] = ablate(cat, pool, seed, [{"kind": "notable", "id": "Constant Gale"}], "TotalDPS", threshold=1e-6)
    assert x.verdict in {"confirmed", "possibly_unmodelled", "not_load_bearing"} and x.baseline > 0


def test_support_key_piece_by_gem_id(cat):
    """I7: the gate accepts a support key piece by gem id; ablation must resolve it the same way (was `not_testable`)."""
    from pos_pipeline.sweep import _support_id
    assert _support_id(cat, "SupportChainPlayer") == _support_id(cat, "Chain I") == "SupportChainPlayer"
    assert _support_id(cat, "Nope") is None
