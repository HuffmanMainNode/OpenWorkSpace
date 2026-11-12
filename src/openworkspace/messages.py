"""Local SQLite message queue. It provides no network transport or sender authentication."""

from __future__ import annotations

import hashlib
import json
import sqlite3

from openworkspace.database import configure_connection, enable_wal
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, ValidationError


class MessageError(ValueError):
    """Raised when a local message operation is invalid."""


class DuplicateMessageError(MessageError):
    """Raised when a message identifier is reused."""


class MessageStore:
    """Durable local message envelopes with recipient inboxes and acknowledgements."""

    MAX_MESSAGE_BYTES = 1_048_576

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        schema = json.loads(
            Path(__file__).with_name("message.schema.json").read_text(encoding="utf-8")
        )
        self._validator = Draft202012Validator(schema, format_checker=FormatChecker())
        with self._connect() as connection:
            enable_wal(connection)
            with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    envelope_json TEXT NOT NULL,
                    envelope_sha256 TEXT NOT NULL,
                    state TEXT NOT NULL CHECK(state IN ('queued','acknowledged')),
                    created_at TEXT NOT NULL,
                    acknowledged_at TEXT
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS message_audit (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details_json TEXT NOT NULL
                )"""
            )
            connection.executescript(
                """
                CREATE TRIGGER IF NOT EXISTS message_audit_no_update
                BEFORE UPDATE ON message_audit
                BEGIN SELECT RAISE(ABORT, 'message audit records are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS message_audit_no_delete
                BEFORE DELETE ON message_audit
                BEGIN SELECT RAISE(ABORT, 'message audit records are append-only'); END;
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10.0)
        configure_connection(connection)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @staticmethod
    def _encode(envelope: dict[str, Any]) -> tuple[str, str]:
        encoded = json.dumps(
            envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        return encoded, digest

    def _require_active_identity(self, connection: sqlite3.Connection, identity_id: str) -> None:
        table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='identities'"
        ).fetchone()
        if table is None:
            raise MessageError("identity registry is not initialized in this database")
        row = connection.execute(
            "SELECT record_json,record_sha256 FROM identities WHERE identity_id=?",
            (identity_id,),
        ).fetchone()
        if row is None:
            raise MessageError(f"identity not found: {identity_id}")
        actual = hashlib.sha256(row[0].encode("utf-8")).hexdigest()
        if actual != row[1]:
            raise MessageError(f"identity integrity check failed: {identity_id}")
        record = json.loads(row[0])
        if record.get("status") != "active":
            raise MessageError(f"identity is not active: {identity_id}")

    def enqueue(self, envelope: dict[str, Any]) -> dict[str, Any]:
        errors = sorted(
            self._validator.iter_errors(envelope), key=lambda item: list(item.path)
        )
        if errors:
            raise MessageError(f"invalid message envelope: {errors[0].message}")
        encoded, digest = self._encode(envelope)
        if len(encoded.encode("utf-8")) > self.MAX_MESSAGE_BYTES:
            raise MessageError("message exceeds the 1 MiB local queue limit")
        now = datetime.now(UTC).isoformat()
        try:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                self._require_active_identity(connection, envelope["sender"])
                self._require_active_identity(connection, envelope["recipient"])
                connection.execute(
                    """INSERT INTO messages
                    (message_id,sender,recipient,envelope_json,envelope_sha256,state,created_at)
                    VALUES(?,?,?,?,?,'queued',?)""",
                    (
                        envelope["message_id"], envelope["sender"], envelope["recipient"],
                        encoded, digest, now,
                    ),
                )
                self._audit(connection, envelope["message_id"], "message.queued", {})
        except sqlite3.IntegrityError as exc:
            raise DuplicateMessageError(
                f"message identifier already exists: {envelope['message_id']}"
            ) from exc
        return envelope

    def get(self, message_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT sender,recipient,envelope_json,envelope_sha256,state,acknowledged_at
                FROM messages WHERE message_id=?""",
                (message_id,),
            ).fetchone()
        if row is None:
            raise MessageError(f"message not found: {message_id}")
        self._verify(row[2], row[3], message_id, row[0], row[1])
        return {
            "envelope": json.loads(row[2]),
            "state": row[4],
            "acknowledged_at": row[5],
        }

    def inbox(self, recipient: str, *, include_acknowledged: bool = False) -> list[dict[str, Any]]:
        with self._connect() as connection:
            self._require_active_identity(connection, recipient)
            query = (
                "SELECT message_id,sender,recipient,envelope_json,envelope_sha256,state "
                "FROM messages WHERE recipient=?"
            )
            if not include_acknowledged:
                query += " AND state='queued'"
            query += " ORDER BY created_at,message_id"
            rows = connection.execute(query, (recipient,)).fetchall()
        result = []
        for message_id, sender, target, encoded, digest, state in rows:
            self._verify(encoded, digest, message_id, sender, target)
            result.append({"envelope": json.loads(encoded), "state": state})
        return result

    def acknowledge(self, message_id: str, recipient: str) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """SELECT sender,recipient,envelope_json,envelope_sha256,state
                FROM messages WHERE message_id=?""",
                (message_id,),
            ).fetchone()
            if row is None:
                raise MessageError(f"message not found: {message_id}")
            self._require_active_identity(connection, recipient)
            self._verify(row[2], row[3], message_id, row[0], row[1])
            if row[1] != recipient:
                raise MessageError("only the declared recipient may acknowledge this message")
            if row[4] != "queued":
                raise MessageError(f"message is not queued: {message_id}")
            now = datetime.now(UTC).isoformat()
            connection.execute(
                "UPDATE messages SET state='acknowledged',acknowledged_at=? WHERE message_id=?",
                (now, message_id),
            )
            self._audit(connection, message_id, "message.acknowledged", {"recipient": recipient})

    def audit_events(self, message_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT message_id,event_type,timestamp,details_json FROM message_audit"
        params: tuple[Any, ...] = ()
        if message_id is not None:
            query += " WHERE message_id=?"
            params = (message_id,)
        query += " ORDER BY sequence"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [
            {
                "message_id": row[0],
                "event_type": row[1],
                "timestamp": row[2],
                "details": json.loads(row[3]),
            }
            for row in rows
        ]

    def _verify(
        self,
        encoded: str,
        digest: str,
        message_id: str,
        sender: str | None = None,
        recipient: str | None = None,
    ) -> None:
        actual = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        if actual != digest:
            raise MessageError(f"message integrity check failed: {message_id}")
        try:
            envelope = json.loads(encoded)
            self._validator.validate(envelope)
        except (ValueError, ValidationError) as exc:
            raise MessageError(f"stored message is invalid: {message_id}") from exc
        if envelope.get("message_id") != message_id:
            raise MessageError(f"message key does not match envelope: {message_id}")
        if sender is not None and envelope.get("sender") != sender:
            raise MessageError(f"message sender index mismatch: {message_id}")
        if recipient is not None and envelope.get("recipient") != recipient:
            raise MessageError(f"message recipient index mismatch: {message_id}")

    @staticmethod
    def _audit(
        connection: sqlite3.Connection,
        message_id: str,
        event_type: str,
        details: dict[str, Any],
    ) -> None:
        connection.execute(
            """INSERT INTO message_audit
            (message_id,event_type,timestamp,details_json) VALUES(?,?,?,?)""",
            (
                message_id,
                event_type,
                datetime.now(UTC).isoformat(),
                json.dumps(details, sort_keys=True),
            ),
        )
