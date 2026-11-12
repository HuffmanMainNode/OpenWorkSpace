"""Local identity record registry. This module does not authenticate principals."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


class IdentityError(ValueError):
    """Raised when an identity operation is invalid."""


class IdentityRegistry:
    """Stores local identity metadata; key references are opaque labels, not credentials."""

    _TRANSITIONS = {
        "active": {"suspended", "revoked"},
        "suspended": {"active", "revoked"},
        "revoked": set(),
        "unknown": {"active", "suspended", "revoked"},
    }

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._schema = json.loads(
            Path(__file__).with_name("identity.schema.json").read_text(encoding="utf-8")
        )
        self._validator = Draft202012Validator(self._schema, format_checker=FormatChecker())
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS identities (
                    identity_id TEXT PRIMARY KEY,
                    record_json TEXT NOT NULL,
                    record_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS identity_audit (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    identity_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details_json TEXT NOT NULL
                )"""
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10.0)
        connection.execute("PRAGMA busy_timeout = 10000")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @staticmethod
    def _encode(record: dict[str, Any]) -> tuple[str, str]:
        encoded = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return encoded, hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def create(self, record: dict[str, Any]) -> dict[str, Any]:
        errors = sorted(self._validator.iter_errors(record), key=lambda item: list(item.path))
        if errors:
            raise IdentityError(f"invalid identity record: {errors[0].message}")
        if record["status"] != "active":
            raise IdentityError("new identities must begin in active status")
        encoded, digest = self._encode(record)
        now = datetime.now(UTC).isoformat()
        try:
            with self._connect() as connection:
                connection.execute(
                    """INSERT INTO identities
                    (identity_id, record_json, record_sha256, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)""",
                    (record["id"], encoded, digest, now, now),
                )
                connection.execute(
                    "INSERT INTO identity_audit(identity_id,event_type,timestamp,details_json) VALUES(?,?,?,?)",
                    (record["id"], "identity.created", now, json.dumps({"sha256": digest})),
                )
        except sqlite3.IntegrityError as exc:
            raise IdentityError(f"identity already exists: {record['id']}") from exc
        return record

    def get(self, identity_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_json, record_sha256 FROM identities WHERE identity_id = ?",
                (identity_id,),
            ).fetchone()
        if row is None:
            raise IdentityError(f"identity not found: {identity_id}")
        actual = hashlib.sha256(row[0].encode("utf-8")).hexdigest()
        if actual != row[1]:
            raise IdentityError(f"identity integrity check failed: {identity_id}")
        record = json.loads(row[0])
        errors = list(self._validator.iter_errors(record))
        if errors:
            raise IdentityError(f"stored identity is invalid: {identity_id}")
        return record

    def set_status(self, identity_id: str, status: str, *, reason: str) -> dict[str, Any]:
        if not reason.strip():
            raise IdentityError("a non-empty reason is required for status changes")
        if status not in self._TRANSITIONS:
            raise IdentityError(f"unknown identity status: {status}")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT record_json, record_sha256 FROM identities WHERE identity_id = ?",
                (identity_id,),
            ).fetchone()
            if row is None:
                raise IdentityError(f"identity not found: {identity_id}")
            if hashlib.sha256(row[0].encode("utf-8")).hexdigest() != row[1]:
                raise IdentityError(f"identity integrity check failed: {identity_id}")
            record = json.loads(row[0])
            current = record["status"]
            if status not in self._TRANSITIONS[current]:
                raise IdentityError(f"identity status transition not allowed: {current} -> {status}")
            record["status"] = status
            encoded, digest = self._encode(record)
            now = datetime.now(UTC).isoformat()
            connection.execute(
                "UPDATE identities SET record_json=?, record_sha256=?, updated_at=? WHERE identity_id=?",
                (encoded, digest, now, identity_id),
            )
            connection.execute(
                "INSERT INTO identity_audit(identity_id,event_type,timestamp,details_json) VALUES(?,?,?,?)",
                (identity_id, "identity.status_changed", now,
                 json.dumps({"from": current, "to": status, "reason": reason}, sort_keys=True)),
            )
        return record

    def list(self) -> list[dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT identity_id, updated_at FROM identities ORDER BY identity_id"
            ).fetchall()
        return [{"id": row[0], "updated_at": row[1]} for row in rows]

    def audit_events(self, identity_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT identity_id,event_type,timestamp,details_json FROM identity_audit"
        params: tuple[Any, ...] = ()
        if identity_id is not None:
            query += " WHERE identity_id = ?"
            params = (identity_id,)
        query += " ORDER BY sequence"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [
            {"identity_id": row[0], "event_type": row[1], "timestamp": row[2],
             "details": json.loads(row[3])}
            for row in rows
        ]
