"""Transactional local SQLite registry for declarative capability manifests."""

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

from openworkspace.contracts import validate_capability
from openworkspace.policy import PolicyDecision, authorize


class RegistryError(ValueError):
    """Raised when a registry operation cannot be completed."""


class DuplicateCapabilityError(RegistryError):
    """Raised when a capability ID is already registered."""


def _canonical(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class CapabilityRegistry:
    """A local SQLite registry. It stores metadata and never executes capabilities."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10.0)
        connection.row_factory = sqlite3.Row
        configure_connection(connection, foreign_keys=True)
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            enable_wal(connection)
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS capabilities (
                    capability_id TEXT PRIMARY KEY,
                    version TEXT NOT NULL,
                    manifest_json TEXT NOT NULL,
                    manifest_sha256 TEXT NOT NULL,
                    registered_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS registry_audit (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    capability_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details_json TEXT NOT NULL
                );
                CREATE TRIGGER IF NOT EXISTS registry_audit_no_update
                BEFORE UPDATE ON registry_audit
                BEGIN SELECT RAISE(ABORT, 'registry audit records are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS registry_audit_no_delete
                BEFORE DELETE ON registry_audit
                BEGIN SELECT RAISE(ABORT, 'registry audit records are append-only'); END;
                """
            )

    def register(self, manifest: dict[str, Any]) -> dict[str, Any]:
        """Validate and register a manifest. Duplicate IDs are rejected, never overwritten."""
        validate_capability(manifest)
        encoded = _canonical(manifest)
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        now = datetime.now(UTC).isoformat()
        try:
            with self._connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """INSERT INTO capabilities
                    (capability_id, version, manifest_json, manifest_sha256, registered_at)
                    VALUES (?, ?, ?, ?, ?)""",
                    (manifest["id"], manifest["version"], encoded, digest, now),
                )
                self._audit(connection, "capability.registered", manifest["id"], {"sha256": digest})
        except sqlite3.IntegrityError as exc:
            if "UNIQUE" in str(exc).upper() or "PRIMARY KEY" in str(exc).upper():
                raise DuplicateCapabilityError(
                    f"capability already registered: {manifest['id']}"
                ) from exc
            raise RegistryError(f"registry integrity error: {exc}") from exc
        return self.get(manifest["id"])

    def get(self, capability_id: str) -> dict[str, Any]:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT manifest_json, manifest_sha256 FROM capabilities WHERE capability_id = ?",
                (capability_id,),
            ).fetchone()
        if row is None:
            raise RegistryError(f"capability not found: {capability_id}")
        return self._decode_manifest(capability_id, row["manifest_json"], row["manifest_sha256"])

    def list(self) -> list[dict[str, str]]:
        with self._connection() as connection:
            rows = connection.execute(
                """SELECT capability_id, version, manifest_sha256, registered_at
                FROM capabilities ORDER BY capability_id"""
            ).fetchall()
        return [dict(row) for row in rows]

    def remove(self, capability_id: str) -> None:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                "DELETE FROM capabilities WHERE capability_id = ?", (capability_id,)
            )
            if cursor.rowcount == 0:
                raise RegistryError(f"capability not found: {capability_id}")
            self._audit(connection, "capability.removed", capability_id, {})

    def evaluate(
        self, capability_id: str, granted: set[str] | frozenset[str]
    ) -> list[PolicyDecision]:
        """Evaluate permissions and atomically record the decision in registry audit."""
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT manifest_json, manifest_sha256 FROM capabilities WHERE capability_id = ?",
                (capability_id,),
            ).fetchone()
            if row is None:
                raise RegistryError(f"capability not found: {capability_id}")
            manifest = self._decode_manifest(
                capability_id, row["manifest_json"], row["manifest_sha256"]
            )
            decisions = authorize(manifest["permissions"], granted)
            details = {
                "decisions": [
                    {
                        "permission": item.permission,
                        "allowed": item.allowed,
                        "reason": item.reason,
                    }
                    for item in decisions
                ]
            }
            self._audit(
                connection, "capability.permissions_evaluated", capability_id, details
            )
        return decisions

    def audit_events(self) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                """SELECT sequence, event_type, capability_id, timestamp, details_json
                FROM registry_audit ORDER BY sequence"""
            ).fetchall()
        return [
            {
                "sequence": row["sequence"],
                "event_type": row["event_type"],
                "capability_id": row["capability_id"],
                "timestamp": row["timestamp"],
                "details": json.loads(row["details_json"]),
            }
            for row in rows
        ]

    @staticmethod
    def _decode_manifest(
        capability_id: str, encoded: str, expected_digest: str
    ) -> dict[str, Any]:
        actual = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        if actual != expected_digest:
            raise RegistryError(f"stored manifest integrity check failed: {capability_id}")
        try:
            manifest = json.loads(encoded)
            validate_capability(manifest)
        except (json.JSONDecodeError, ValueError) as exc:
            raise RegistryError(f"stored manifest is invalid: {capability_id}") from exc
        return manifest

    @staticmethod
    def _audit(
        connection: sqlite3.Connection,
        event_type: str,
        capability_id: str,
        details: dict[str, Any],
    ) -> None:
        connection.execute(
            """INSERT INTO registry_audit
            (event_type, capability_id, timestamp, details_json) VALUES (?, ?, ?, ?)""",
            (
                event_type,
                capability_id,
                datetime.now(UTC).isoformat(),
                _canonical(details),
            ),
        )
