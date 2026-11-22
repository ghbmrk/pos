import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_engine.engine import PobEngine  # noqa: E402
from pos_pool import EnginePool, Job, ResultCache  # noqa: E402

XML = (Path(__file__).parent / "fixtures" / "large_tree.xml").read_text()
KEYS = ("TotalDPS", "TotalEHP")


def weapon(n: int) -> tuple:
    raw = f"Rarity: Rare\nW{n}\nDueling Wand\n{n}% increased Spell Damage"
    return (("add_item", {"raw": raw, "slot": "Weapon 1"}),)


@pytest.fixture(scope="module")
def pool():
    with EnginePool(workers=2, timeout=60) as p:
        yield p


def test_matches_direct_engine(pool):
    with PobEngine() as e:
        e.load_build_xml(XML)
        direct = e.get_stats(list(KEYS))["stats"]
    r = pool.evaluate(Job(XML, (), KEYS))
    assert r.ok and r.stats == pytest.approx(direct)


def test_order_and_cache():
    with EnginePool(workers=2) as p:
        jobs = [Job(XML, weapon(n), KEYS, tag=n) for n in (10, 50, 100, 150)]
        first = p.map(jobs)
        assert [r.tag for r in first] == [10, 50, 100, 150]
        assert all(r.ok and not r.cached for r in first)
        assert len({r.stats["TotalDPS"] for r in first}) > 1  # mutations actually applied
        second = p.map(jobs)
        assert all(r.cached for r in second)
        assert [r.stats for r in second] == [r.stats for r in first]
        assert p.stats["evals"] == 4 and p.stats["hits"] == 4


def test_duplicates_in_batch_evaluated_once():
    with EnginePool(workers=2) as p:
        rs = p.map([Job(XML, (), KEYS)] * 3)
        assert p.stats["evals"] == 1
        assert [r.cached for r in rs] == [False, True, True]


def test_cache_key_ignores_xml_whitespace_but_not_keys_or_mutations():
    sha = "x"
    a = Job(XML, (), KEYS).key(sha)
    assert a == Job(XML.replace("><", ">\n  <"), (), KEYS).key(sha)
    assert a == Job(XML, (), tuple(reversed(KEYS))).key(sha)
    assert a != Job(XML, (), ("TotalDPS",)).key(sha)
    assert a != Job(XML, weapon(5), KEYS).key(sha)
    assert a != Job(XML, (), KEYS).key("y")


def test_sqlite_cache_persists(tmp_path):
    db = tmp_path / "c.sqlite"
    with EnginePool(workers=1, cache=db) as p:
        p.evaluate(Job(XML, (), KEYS))
    with EnginePool(workers=1, cache=ResultCache(db)) as p:
        r = p.evaluate(Job(XML, (), KEYS))
        assert r.cached and p.stats["evals"] == 0


def test_crashed_worker_restarts():
    with EnginePool(workers=1) as p:
        assert p.evaluate(Job(XML, (), KEYS)).ok
        p._pool[0].engine.proc.kill()  # simulate crash between jobs
        r = p.evaluate(Job(XML, weapon(7), KEYS))
        assert r.ok and p._pool[0].starts == 2


class FlakyEngine(PobEngine):
    fail_next = True

    def get_stats(self, keys=None):
        if FlakyEngine.fail_next:
            FlakyEngine.fail_next = False
            self.proc.kill()
        return super().get_stats(keys)


def test_failure_retried_once_then_succeeds():
    FlakyEngine.fail_next = True
    with EnginePool(workers=1, engine_factory=FlakyEngine) as p:
        r = p.evaluate(Job(XML, (), KEYS))
        assert r.ok and r.attempts == 2 and p.stats["retries"] == 1


def test_job_failing_twice_is_reported():
    with EnginePool(workers=1) as p:
        r = p.evaluate(Job(XML, (("add_item", {"raw": "x", "slot": "NoSuchSlot", "bogus": 1}),), KEYS))
        assert not r.ok and r.attempts == 2 and r.error and p.stats["failures"] == 1
        assert p.evaluate(Job(XML, (), KEYS)).ok  # pool still healthy
        assert len(p.cache) == 1  # failures are not cached


class SlowEngine(PobEngine):
    """Simulates a hung engine: stalls past the watchdog, then talks to the (killed) process."""
    stall = 1.0

    def get_stats(self, keys=None):
        import time
        time.sleep(SlowEngine.stall)
        return super().get_stats(keys)


def test_hung_worker_killed_by_timeout_and_recovers():
    SlowEngine.stall = 1.0
    with EnginePool(workers=1, timeout=0.3, engine_factory=SlowEngine) as p:
        r = p.evaluate(Job(XML, (), KEYS))
        assert not r.ok and r.attempts == 2 and p.stats["failures"] == 1
        assert p._pool[0].starts == 2  # killed and restarted for the retry
        SlowEngine.stall = 0.0
        p.timeout = 60
        assert p.evaluate(Job(XML, weapon(11), KEYS)).ok


def item(n: int) -> str:
    return f"Rarity: Rare\nW{n}\nDueling Wand\n{n}% increased Spell Damage"


class CountingEngine(PobEngine):
    loads = 0

    def load_build_xml(self, xml, name="imported"):
        CountingEngine.loads += 1
        return super().load_build_xml(xml, name)


def test_slot_item_matches_mutation_job_and_skips_reload():
    CountingEngine.loads = 0
    with EnginePool(workers=1, engine_factory=CountingEngine) as p:
        fast = p.map([Job(XML, (), KEYS, slot_item=("Weapon 1", item(n))) for n in (20, 60, 120)])
        assert CountingEngine.loads == 1  # base build loaded once, restored by eval_items
        slow = p.map([Job(XML, weapon(n), KEYS) for n in (20, 60, 120)])
        for f, s in zip(fast, slow):
            assert f.ok and s.ok
            assert f.stats["TotalDPS"] == pytest.approx(s.stats["TotalDPS"])
        # base build is still clean after the fast path
        base = p.evaluate(Job(XML, (), KEYS))
        assert base.stats["TotalDPS"] != fast[0].stats["TotalDPS"]


def test_slot_item_validation():
    with pytest.raises(ValueError):
        Job(XML, weapon(1), KEYS, slot_item=("Weapon 1", item(1)))
    with pytest.raises(ValueError):
        Job(XML, (), None, slot_item=("Weapon 1", item(1)))


def test_worker_recycled_above_rss_cap():
    with EnginePool(workers=1, max_rss_mb=1.0) as p:  # any engine exceeds 1 MB
        for n in (1, 2, 3):
            assert p.evaluate(Job(XML, weapon(n), KEYS)).ok
        assert p._pool[0].starts == 3
