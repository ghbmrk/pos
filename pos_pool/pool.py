"""Multi-process PoB evaluation pool (pipeline task G4).

N persistent `PobEngine` LuaJIT processes, one owned by each worker thread. A job is
`(build XML, mutations, stat keys)`; the result is the stats dict. Results are cached in SQLite
keyed by `(pob_sha, canonical XML hash, mutations, stat keys)`.

Failure handling: a worker whose engine errors, dies, or exceeds `timeout` seconds is killed and
restarted, and the job retried once. A job failing twice yields `Result(ok=False, error=...)`.
Hung engines are detected by a watchdog that kills the process, which unblocks the pending read.
"""
from __future__ import annotations

import functools
import hashlib
import json
import os
import queue
import subprocess
import threading
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from pos_engine.engine import PobEngine
from pos_engine import paths

from .cache import ResultCache

Mutation = tuple[str, dict[str, Any]]  # (PobEngine method name, kwargs), applied in order


def pob_sha() -> str:
    """Commit of the pinned PoB submodule (cache-key component); env POS_POB_SHA overrides."""
    env = os.environ.get("POS_POB_SHA")
    if env:
        return env
    try:
        out = subprocess.run(
            ["git", "-C", str(paths.pob_src_dir()), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10, check=True,
        )
        return out.stdout.strip()
    except Exception:
        return "unknown"


@functools.lru_cache(maxsize=256)
def canonical_xml_hash(xml: str) -> str:
    try:
        canon = ET.canonicalize(xml, strip_text=True)
    except ET.ParseError:
        canon = xml
    return hashlib.sha256(canon.encode()).hexdigest()


@dataclass(frozen=True)
class Job:
    xml: str
    mutations: tuple[Mutation, ...] = ()
    stat_keys: tuple[str, ...] | None = None
    # Fast path for gear search: evaluate one candidate item in a slot via the engine's
    # `eval_items` (which restores the build), so a worker already holding this XML skips the
    # ~0.25 s XML reload. Requires empty `mutations` and explicit `stat_keys`.
    slot_item: tuple[str, str] | None = None  # (slot, raw item text)
    tag: Any = field(default=None, compare=False)  # caller's label, passed through to Result

    def __post_init__(self) -> None:
        if self.slot_item is not None and (self.mutations or not self.stat_keys):
            raise ValueError("slot_item jobs need empty mutations and explicit stat_keys")

    def key(self, sha: str) -> str:
        payload = json.dumps(
            [sha, canonical_xml_hash(self.xml), [[m, p] for m, p in self.mutations],
             sorted(self.stat_keys) if self.stat_keys is not None else None, self.slot_item],
            sort_keys=True, default=str,
        )
        return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class Result:
    ok: bool
    stats: dict[str, Any] = field(default_factory=dict)
    main_skill: str | None = None
    error: str | None = None
    cached: bool = False
    attempts: int = 0
    tag: Any = None


class _Worker:
    """Owns one PobEngine; restarts it on demand."""

    def __init__(self, factory: Callable[[], PobEngine]) -> None:
        self._factory = factory
        self.engine: PobEngine | None = None
        self.starts = 0
        self.loaded: str | None = None  # canonical hash of the XML currently loaded and clean

    def ensure(self) -> PobEngine:
        if self.engine is None or self.engine.proc.poll() is not None:
            self.kill()
            self.engine = self._factory()
            self.starts += 1
        return self.engine

    def rss_mb(self) -> float:
        try:
            pid = self.engine.proc.pid  # type: ignore[union-attr]
            return int(Path(f"/proc/{pid}/status").read_text().split("VmRSS:")[1].split()[0]) / 1024
        except Exception:
            return 0.0

    def kill(self) -> None:
        eng, self.engine = self.engine, None
        self.loaded = None
        if eng is not None:
            try:
                eng.proc.kill()
                eng.proc.wait(timeout=5)
            except Exception:
                pass


class EnginePool:
    def __init__(
        self,
        workers: int | None = None,
        cache: ResultCache | str | Path | None = None,
        timeout: float = 60.0,
        engine_factory: Callable[[], PobEngine] | None = None,
        sha: str | None = None,
        max_rss_mb: float = 1500.0,
        max_batch: int = 16,
        hard_rss_mb: float = 3500.0,
    ) -> None:
        self.max_batch = max_batch
        # load_build_xml leaks engine memory (~30-50 MB/load, measured); a worker above max_rss_mb
        # is recycled between jobs so N workers cannot exhaust RAM.
        self.max_rss_mb = max_rss_mb
        # A job that balloons past hard_rss_mb is killed mid-run (and retried once on a fresh engine) instead of taking
        # the container's OOM killer with it; seen as an intermittent multi-GB runaway in one worker (a 14 GB peak).
        self.hard_rss_mb = hard_rss_mb
        self.workers = workers or os.cpu_count() or 1
        self.timeout = timeout
        self.sha = sha or pob_sha()
        self.cache = cache if isinstance(cache, ResultCache) else ResultCache(cache or ":memory:")
        self._factory = engine_factory or PobEngine
        self._pool = [_Worker(self._factory) for _ in range(self.workers)]
        self.stats = {"hits": 0, "evals": 0, "retries": 0, "failures": 0}
        self._slock = threading.Lock()

    def _bump(self, k: str, n: int = 1) -> None:
        with self._slock:
            self.stats[k] += n

    # -- single attempt -----------------------------------------------------
    def _run(self, w: _Worker, batch: list[Job]) -> list[tuple[dict | None, str | None]]:
        """One attempt at a work unit: a single general job, or a batch of slot_item jobs that
        share (XML, slot, stat keys) and go to the engine as one `eval_items` call."""
        eng = w.ensure()
        h = canonical_xml_hash(batch[0].xml)
        timer = threading.Timer(self.timeout, eng.proc.kill)  # watchdog: kill unblocks readline
        timer.start()
        stop = threading.Event()

        def guard() -> None:   # memory watchdog: poll the worker's RSS while the job runs
            while not stop.wait(0.25):
                if w.rss_mb() > self.hard_rss_mb:
                    eng.proc.kill()
                    return

        threading.Thread(target=guard, daemon=True).start()
        try:
            if batch[0].slot_item is not None:
                if w.loaded != h:
                    w.loaded = None
                    eng.load_build_xml(batch[0].xml)
                    w.loaded = h
                slot = batch[0].slot_item[0]
                res = eng.eval_items(slot, [j.slot_item[1] for j in batch], keys=list(batch[0].stat_keys))
                return [(r or None, None) for r in res["results"]]  # None = engine rejected that item
            job = batch[0]
            w.loaded = None  # mutations dirty the build
            eng.load_build_xml(job.xml)
            for method, params in job.mutations:
                getattr(eng, method)(**params)
            r = eng.get_stats(list(job.stat_keys) if job.stat_keys is not None else None)
            return [(r.get("stats", {}), r.get("mainSkill"))]
        finally:
            timer.cancel()
            stop.set()
            rss = w.rss_mb()
            # A job shorter than one guard poll (0.25 s) is never sampled mid-run, so check the cap once more here:
            # without this the hard cap was timing-dependent (CI runs #156, #159).
            if rss > self.hard_rss_mb:
                w.kill()
                raise MemoryError(f"worker RSS {rss:.0f} MB over hard cap {self.hard_rss_mb:.0f} MB")
            if rss > self.max_rss_mb:
                w.kill()

    def _evaluate(self, w: _Worker, batch: list[Job]) -> list[Result]:
        last = None
        for attempt in (1, 2):
            try:
                out = self._run(w, batch)
                return [
                    Result(True, st, sk, attempts=attempt, tag=j.tag) if st is not None
                    else Result(False, error="engine rejected item", attempts=attempt, tag=j.tag)
                    for j, (st, sk) in zip(batch, out)
                ]
            except Exception as ex:  # engine error, crash, or watchdog kill
                last = f"{type(ex).__name__}: {ex}"
                w.kill()  # engine state is unknown after any failure
                if attempt == 1:
                    self._bump("retries")
        self._bump("failures", len(batch))
        return [Result(False, error=last, attempts=2, tag=j.tag) for j in batch]

    # -- public API -----------------------------------------------------------
    def map(self, jobs: Iterable[Job]) -> list[Result]:
        """Evaluate jobs in parallel; results returned in input order. Cache hits skip the engines."""
        jobs = list(jobs)
        results: list[Result | None] = [None] * len(jobs)
        keys = [j.key(self.sha) for j in jobs]
        seen: dict[str, int] = {}  # dedupe identical jobs within the batch
        dups: list[tuple[int, int]] = []
        for i, (j, k) in enumerate(zip(jobs, keys)):
            hit = self.cache.get(k)
            if hit is not None:
                results[i] = Result(True, hit["stats"], hit["main_skill"], cached=True, tag=j.tag)
                self._bump("hits")
            elif k in seen:
                dups.append((i, seen[k]))
            else:
                seen[k] = i
        # Work units: general jobs alone; slot_item jobs grouped by (XML, slot, keys) into chunks
        # sized so every worker gets work. Same-XML units adjacent: workers keep their loaded build.
        units: list[list[int]] = []
        groups: dict[tuple, list[int]] = {}
        for i in sorted(seen.values()):
            j = jobs[i]
            if j.slot_item is None:
                units.append([i])
            else:
                groups.setdefault((canonical_xml_hash(j.xml), j.slot_item[0], j.stat_keys), []).append(i)
        for idxs in groups.values():
            size = max(1, min(self.max_batch, -(-len(idxs) // self.workers)))
            units += [idxs[o:o + size] for o in range(0, len(idxs), size)]
        units.sort(key=lambda u: canonical_xml_hash(jobs[u[0]].xml))
        todo: "queue.Queue[list[int]]" = queue.Queue()
        for u in units:
            todo.put(u)

        def loop(w: _Worker) -> None:
            while True:
                try:
                    u = todo.get_nowait()
                except queue.Empty:
                    return
                for i, res in zip(u, self._evaluate(w, [jobs[i] for i in u])):
                    results[i] = res
                    if res.ok:
                        self._bump("evals")
                        self.cache.put(keys[i], res.stats, res.main_skill)

        n = min(self.workers, max(todo.qsize(), 1))
        threads = [threading.Thread(target=loop, args=(self._pool[t],), daemon=True) for t in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        for i, src in dups:
            r = results[src]
            results[i] = Result(r.ok, r.stats, r.main_skill, r.error, True, r.attempts, jobs[i].tag)
        return results  # type: ignore[return-value]

    def evaluate(self, job: Job) -> Result:
        return self.map([job])[0]

    def close(self) -> None:
        for w in self._pool:
            w.kill()

    def __enter__(self) -> "EnginePool":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
