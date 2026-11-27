"""SQLite cho dữ liệu IDE, có migration theo PRAGMA user_version. Không lưu secret."""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from app_builder.core.schemas import utcnow_iso

MIGRATIONS: list[str] = [
    # v1
    """
    CREATE TABLE projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT NOT NULL,
        path TEXT NOT NULL UNIQUE,
        description TEXT NOT NULL DEFAULT '',
        template TEXT NOT NULL DEFAULT '',
        categories TEXT NOT NULL DEFAULT '[]',
        platforms TEXT NOT NULL DEFAULT '[]',
        trusted INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        last_opened_at TEXT,
        last_build_status TEXT,
        last_build_at TEXT
    );
    CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
        title TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL
    );
    CREATE TABLE messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE change_sets (
        id TEXT PRIMARY KEY,
        project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
        summary TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL,
        payload TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE checkpoints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
        label TEXT NOT NULL,
        location TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE jobs (
        id TEXT PRIMARY KEY,
        project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
        kind TEXT NOT NULL,
        status TEXT NOT NULL,
        detail TEXT NOT NULL DEFAULT '',
        log_path TEXT,
        created_at TEXT NOT NULL,
        started_at TEXT,
        finished_at TEXT
    );
    CREATE TABLE build_artifacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT REFERENCES jobs(id) ON DELETE CASCADE,
        path TEXT NOT NULL,
        sha256 TEXT,
        size INTEGER,
        created_at TEXT NOT NULL
    );
    CREATE TABLE usage_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        provider TEXT NOT NULL,
        model TEXT NOT NULL,
        request_id TEXT NOT NULL,
        input_tokens INTEGER,
        output_tokens INTEGER,
        cached_tokens INTEGER,
        reasoning_tokens INTEGER,
        cost_usd REAL,
        cost_known INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE model_cache (
        provider TEXT NOT NULL,
        model_id TEXT NOT NULL,
        metadata TEXT NOT NULL,
        fetched_at TEXT NOT NULL,
        PRIMARY KEY (provider, model_id)
    );
    CREATE TABLE audit_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        kind TEXT NOT NULL,
        detail TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL
    );
    CREATE INDEX idx_usage_created ON usage_records(created_at);
    CREATE INDEX idx_audit_project ON audit_events(project_id);
    """,
    # v2 (M2): ledger chi tiết hơn cho ngân sách AI
    """
    ALTER TABLE usage_records ADD COLUMN session_id TEXT;
    ALTER TABLE usage_records ADD COLUMN estimated_cost_usd REAL;
    ALTER TABLE usage_records ADD COLUMN served_model TEXT;
    ALTER TABLE usage_records ADD COLUMN note TEXT NOT NULL DEFAULT '';
    CREATE INDEX idx_usage_project ON usage_records(project_id);
    """,
]


class Database:
    def __init__(self, path: Path | str) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        if self.path != ":memory:":
            self.conn.execute("PRAGMA journal_mode = WAL")
        self.migrate()

    @property
    def version(self) -> int:
        return int(self.conn.execute("PRAGMA user_version").fetchone()[0])

    def migrate(self) -> None:
        with self._lock:
            current = self.version
            if current > len(MIGRATIONS):
                raise RuntimeError(
                    f"Cơ sở dữ liệu phiên bản {current} mới hơn ứng dụng ({len(MIGRATIONS)}). Hãy cập nhật App Builder AI."
                )
            for idx in range(current, len(MIGRATIONS)):
                with self.transaction() as cur:
                    cur.executescript_safe(MIGRATIONS[idx])
                    cur.execute(f"PRAGMA user_version = {idx + 1}")

    @contextmanager
    def transaction(self) -> Iterator["_Cursor"]:
        with self._lock:
            self.conn.execute("BEGIN")
            try:
                yield _Cursor(self.conn)
                self.conn.execute("COMMIT")
            except BaseException:
                self.conn.execute("ROLLBACK")
                raise

    def query(self, sql: str, params: tuple | dict = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self.conn.execute(sql, params).fetchall()

    def query_one(self, sql: str, params: tuple | dict = ()) -> sqlite3.Row | None:
        with self._lock:
            return self.conn.execute(sql, params).fetchone()

    def execute(self, sql: str, params: tuple | dict = ()) -> int:
        with self.transaction() as cur:
            c = cur.execute(sql, params)
            return int(c.lastrowid or 0)

    def audit(self, kind: str, project_id: int | None = None, **detail: Any) -> None:
        self.execute(
            "INSERT INTO audit_events(project_id, kind, detail, created_at) VALUES (?,?,?,?)",
            (project_id, kind, json.dumps(detail, ensure_ascii=False), utcnow_iso()),
        )

    def close(self) -> None:
        with self._lock:
            self.conn.close()


class _Cursor:
    """Bọc connection trong transaction; executescript tự COMMIT nên tách từng câu."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def executescript_safe(self, script: str) -> None:
        for stmt in _split_sql(script):
            self._conn.execute(stmt)


def _split_sql(script: str) -> list[str]:
    stmts, buf = [], []
    for line in script.splitlines():
        buf.append(line)
        candidate = "\n".join(buf).strip()
        if candidate.endswith(";") and sqlite3.complete_statement(candidate):
            stmts.append(candidate)
            buf = []
    rest = "\n".join(buf).strip()
    if rest:
        stmts.append(rest)
    return stmts
