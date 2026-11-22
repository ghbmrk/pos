"""SQLite result cache. Only the pool's coordinating thread touches it (single connection, WAL)."""
from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path


class ResultCache:
    def __init__(self, path: str | Path = ":memory:") -> None:
        self._lock = threading.Lock()
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        if str(path) != ":memory:":
            self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS results (key TEXT PRIMARY KEY, stats TEXT NOT NULL, "
            "main_skill TEXT, created REAL DEFAULT (strftime('%s','now')))"
        )
        self._db.commit()

    def get(self, key: str) -> dict | None:
        with self._lock:
            row = self._db.execute("SELECT stats, main_skill FROM results WHERE key=?", (key,)).fetchone()
        return None if row is None else {"stats": json.loads(row[0]), "main_skill": row[1]}

    def put(self, key: str, stats: dict, main_skill: str | None) -> None:
        with self._lock:
            self._db.execute(
                "INSERT OR REPLACE INTO results (key, stats, main_skill) VALUES (?,?,?)",
                (key, json.dumps(stats, sort_keys=True), main_skill),
            )
            self._db.commit()

    def __len__(self) -> int:
        with self._lock:
            return self._db.execute("SELECT COUNT(*) FROM results").fetchone()[0]

    def close(self) -> None:
        with self._lock:
            self._db.close()
