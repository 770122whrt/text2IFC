"""Shared SQLite session store for Phase 6.2 interactive CLI runs."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1


@dataclass(frozen=True)
class StoredSession:
    session_id: str
    session_hash: str
    original_input: str
    status: str
    run_dir: Path
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class StoredTurn:
    turn_index: int
    role: str
    text: str
    created_at: str


@dataclass(frozen=True)
class StoredEvent:
    event_index: int
    event_type: str
    payload: dict[str, Any]
    created_at: str


class SessionStore:
    """SQLite-backed source of truth for Phase 6.2 CLI sessions."""

    def __init__(self, db_path: Path, artifact_root: Path):
        self.db_path = db_path
        self.artifact_root = artifact_root
        self._connection = sqlite3.connect(str(db_path))
        self._connection.row_factory = sqlite3.Row
        self._closed = False
        self._migrate()

    @classmethod
    def open(
        cls,
        db_path: Path | str,
        *,
        artifact_root: Path | str | None = None,
    ) -> "SessionStore":
        active_db_path = Path(db_path)
        active_db_path.parent.mkdir(parents=True, exist_ok=True)
        active_artifact_root = Path(artifact_root) if artifact_root is not None else active_db_path.parent
        active_artifact_root.mkdir(parents=True, exist_ok=True)
        return cls(active_db_path, active_artifact_root)

    def create_session(self, *, original_input: str) -> StoredSession:
        now = _utc_now()
        session_id = f"phase6.2-{uuid.uuid4().hex}"
        session_hash = _hash_session_id(session_id)
        run_dir = self.artifact_root / "runs" / session_hash
        run_dir.mkdir(parents=True, exist_ok=False)
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO sessions (
                    session_id, session_hash, original_input, status,
                    run_dir, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    session_hash,
                    original_input,
                    "open",
                    str(run_dir),
                    now,
                    now,
                ),
            )
        self.append_turn(session_id, role="user", text=original_input)
        return self.get_session(session_id)

    def close(self) -> None:
        if not self._closed:
            self._connection.close()
            self._closed = True

    def __enter__(self) -> "SessionStore":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def get_session(self, identifier: str) -> StoredSession:
        row = self._session_row(identifier)
        if row is None:
            raise KeyError(f"unknown Phase 6.2 session: {identifier}")
        return _session_from_row(row)

    def list_sessions(self) -> list[StoredSession]:
        rows = self._connection.execute(
            "SELECT * FROM sessions ORDER BY created_at, session_id"
        ).fetchall()
        return [_session_from_row(row) for row in rows]

    def append_turn(self, session_id: str, *, role: str, text: str) -> StoredTurn:
        session = self.get_session(session_id)
        now = _utc_now()
        turn_index = self._next_index("turns", session.session_id, "turn_index")
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO turns (session_id, turn_index, role, text, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session.session_id, turn_index, role, text, now),
            )
            self._touch(session.session_id, now)
        return StoredTurn(turn_index=turn_index, role=role, text=text, created_at=now)

    def list_turns(self, identifier: str) -> list[StoredTurn]:
        session = self.get_session(identifier)
        rows = self._connection.execute(
            "SELECT * FROM turns WHERE session_id = ? ORDER BY turn_index",
            (session.session_id,),
        ).fetchall()
        return [
            StoredTurn(
                turn_index=int(row["turn_index"]),
                role=str(row["role"]),
                text=str(row["text"]),
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]

    def append_event(
        self,
        session_id: str,
        *,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> StoredEvent:
        session = self.get_session(session_id)
        now = _utc_now()
        event_index = self._next_index("events", session.session_id, "event_index")
        active_payload = {} if payload is None else payload
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO events (session_id, event_index, event_type, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session.session_id,
                    event_index,
                    event_type,
                    json.dumps(active_payload, ensure_ascii=False, sort_keys=True),
                    now,
                ),
            )
            self._touch(session.session_id, now)
        return StoredEvent(
            event_index=event_index,
            event_type=event_type,
            payload=active_payload,
            created_at=now,
        )

    def list_events(self, identifier: str) -> list[StoredEvent]:
        session = self.get_session(identifier)
        rows = self._connection.execute(
            "SELECT * FROM events WHERE session_id = ? ORDER BY event_index",
            (session.session_id,),
        ).fetchall()
        return [
            StoredEvent(
                event_index=int(row["event_index"]),
                event_type=str(row["event_type"]),
                payload=json.loads(str(row["payload_json"])),
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]

    def record_artifact(self, session_id: str, *, kind: str, path: Path | str) -> None:
        session = self.get_session(session_id)
        now = _utc_now()
        path_text = path.as_posix() if isinstance(path, Path) else str(path).replace("\\", "/")
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO artifacts (session_id, kind, path, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (session.session_id, kind, path_text, now),
            )
            self._touch(session.session_id, now)

    def record_agent_call(self, session_id: str, payload: dict[str, Any]) -> None:
        self.record_payload(session_id, table="agent_calls", payload=payload)

    def record_payload(
        self,
        session_id: str,
        *,
        table: str,
        payload: dict[str, Any],
    ) -> None:
        if table not in {"agent_calls", "prompts", "responses", "gates", "metrics"}:
            raise ValueError(f"unsupported session payload table: {table}")
        session = self.get_session(session_id)
        now = _utc_now()
        with self._connection:
            self._connection.execute(
                f"""
                INSERT INTO {table} (session_id, payload_json, created_at)
                VALUES (?, ?, ?)
                """,
                (
                    session.session_id,
                    json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    now,
                ),
            )
            self._touch(session.session_id, now)

    def list_artifacts(self, identifier: str) -> list[dict[str, Any]]:
        session = self.get_session(identifier)
        rows = self._connection.execute(
            "SELECT kind, path, created_at FROM artifacts WHERE session_id = ? ORDER BY id",
            (session.session_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def mark_session_status(self, identifier: str, status: str) -> StoredSession:
        session = self.get_session(identifier)
        now = _utc_now()
        with self._connection:
            self._connection.execute(
                "UPDATE sessions SET status = ?, updated_at = ? WHERE session_id = ?",
                (status, now, session.session_id),
            )
        return self.get_session(session.session_id)

    def export_session(self, identifier: str) -> Path:
        session = self.get_session(identifier)
        export_path = session.run_dir / "session-export.json"
        relative_path = Path("runs") / session.session_hash / "session-export.json"
        if not self._artifact_exists(
            session.session_id,
            kind="session_export",
            path=relative_path,
        ):
            self.record_artifact(
                session.session_id,
                kind="session_export",
                path=relative_path,
            )
        payload = self.session_export_payload(session.session_id)
        _write_json(export_path, payload)
        return export_path

    def session_export_payload(self, identifier: str) -> dict[str, Any]:
        session = self.get_session(identifier)
        return {
            "schema_version": "text2ifc/phase6.2-session-export-v1",
            "session": _session_to_dict(session),
            "turns": [_turn_to_dict(turn) for turn in self.list_turns(session.session_id)],
            "events": [_event_to_dict(event) for event in self.list_events(session.session_id)],
            "agent_calls": self._list_table(session.session_id, "agent_calls"),
            "prompts": self._list_table(session.session_id, "prompts"),
            "responses": self._list_table(session.session_id, "responses"),
            "gates": self._list_table(session.session_id, "gates"),
            "artifacts": self.list_artifacts(session.session_id),
            "metrics": self._list_table(session.session_id, "metrics"),
        }

    def _migrate(self) -> None:
        with self._connection:
            self._connection.execute(
                "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    session_hash TEXT NOT NULL UNIQUE,
                    original_input TEXT NOT NULL,
                    status TEXT NOT NULL,
                    run_dir TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    turn_index INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
                """
            )
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    event_index INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
                """
            )
            for table in ("agent_calls", "prompts", "responses", "gates", "metrics"):
                self._connection.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                    )
                    """
                )
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
                """
            )
            self._connection.execute(
                "INSERT OR IGNORE INTO meta (key, value) VALUES ('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )

    def _session_row(self, identifier: str) -> sqlite3.Row | None:
        return self._connection.execute(
            """
            SELECT * FROM sessions
            WHERE session_id = ? OR session_hash = ?
            """,
            (identifier, identifier),
        ).fetchone()

    def _next_index(self, table: str, session_id: str, column: str) -> int:
        row = self._connection.execute(
            f"SELECT COALESCE(MAX({column}), -1) + 1 AS next_index FROM {table} WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        return int(row["next_index"])

    def _touch(self, session_id: str, updated_at: str) -> None:
        self._connection.execute(
            "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
            (updated_at, session_id),
        )

    def _list_table(self, session_id: str, table: str) -> list[dict[str, Any]]:
        rows = self._connection.execute(
            f"SELECT payload_json, created_at FROM {table} WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
        return [
            {
                "payload": json.loads(str(row["payload_json"])),
                "created_at": str(row["created_at"]),
            }
            for row in rows
        ]

    def _artifact_exists(self, session_id: str, *, kind: str, path: Path) -> bool:
        row = self._connection.execute(
            """
            SELECT 1 FROM artifacts
            WHERE session_id = ? AND kind = ? AND path = ?
            LIMIT 1
            """,
            (session_id, kind, str(path)),
        ).fetchone()
        return row is not None


def _hash_session_id(session_id: str) -> str:
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:16]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _session_from_row(row: sqlite3.Row) -> StoredSession:
    return StoredSession(
        session_id=str(row["session_id"]),
        session_hash=str(row["session_hash"]),
        original_input=str(row["original_input"]),
        status=str(row["status"]),
        run_dir=Path(str(row["run_dir"])),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _session_to_dict(session: StoredSession) -> dict[str, Any]:
    return {
        "session_id": session.session_id,
        "session_hash": session.session_hash,
        "original_input": session.original_input,
        "status": session.status,
        "run_dir": str(session.run_dir),
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


def _turn_to_dict(turn: StoredTurn) -> dict[str, Any]:
    return {
        "turn_index": turn.turn_index,
        "role": turn.role,
        "text": turn.text,
        "created_at": turn.created_at,
    }


def _event_to_dict(event: StoredEvent) -> dict[str, Any]:
    return {
        "event_index": event.event_index,
        "event_type": event.event_type,
        "payload": event.payload,
        "created_at": event.created_at,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
