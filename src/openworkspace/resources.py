"""Local resource catalog for provenance and trust metadata.

The catalog never fetches or executes resources.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from openworkspace.database import configure_connection, enable_wal

class ResourceCatalogError(ValueError):
    """Raised when a resource catalog operation is invalid."""


class DuplicateResourceError(ResourceCatalogError):
    """Raised when a resource identifier already exists."""


class ResourceCatalog:
    """Store resource metadata and explicit trust-state changes in local SQLite."""

    _TRANSITIONS = {
        "uninspected": {"inspected", "quarantined", "revoked"},
        "inspected": {"qualified", "restricted", "quarantined", "revoked"},
        "qualified": {"authorized", "restricted", "quarantined", "revoked"},
        "authorized": {"restricted", "quarantined", "revoked"},
        "restricted": {"inspected", "qualified", "quarantined", "revoked"},
        "quarantined": {"inspected", "revoked"},
        "revoked": set(),
    }

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        schema = json.loads(
            Path(__file__).with_name("resource.schema.json").read_text(encoding="utf-8")
        )
        self._validator = Draft202012Validator(schema, format_checker=FormatChecker())
        with self._connect() as connection:
            enable_wal(connection)
            connection.execute(
                """CREATE TABLE IF NOT EXISTS resources (
                    resource_id TEXT PRIMARY KEY,
                    resource_json TEXT NOT NULL,
                    resource_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS resource_audit (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details_json TEXT NOT NULL
                )"""
            )
            connection.executescript(
                """
                CREATE TRIGGER IF NOT EXISTS resource_audit_no_update
                BEFORE UPDATE ON resource_audit
                BEGIN SELECT RAISE(ABORT, 'resource audit records are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS resource_audit_no_delete
                BEFORE DELETE ON resource_audit
                BEGIN SELECT RAISE(ABORT, 'resource audit records are append-only'); END;
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
    def _encode(record: dict[str, Any]) -> tuple[str, str]:
        encoded = json.dumps(
            record, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        return encoded, digest

    def register(self, record: dict[str, Any]) -> dict[str, Any]:
        errors = sorted(
            self._validator.iter_errors(record), key=lambda item: list(item.path)
        )
        if errors:
            raise ResourceCatalogError(f"invalid resource record: {errors[0].message}")
        if record["trust_state"] != "uninspected":
            raise ResourceCatalogError("new resources must begin in uninspected trust state")
        encoded, digest = self._encode(record)
        now = datetime.now(UTC).isoformat()
        try:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """INSERT INTO resources
                    (resource_id,resource_json,resource_sha256,created_at,updated_at)
                    VALUES(?,?,?,?,?)""",
                    (record["id"], encoded, digest, now, now),
                )
                self._audit(
                    connection, record["id"], "resource.registered", {"sha256": digest}
                )
        except sqlite3.IntegrityError as exc:
            raise DuplicateResourceError(
                f"resource already registered: {record['id']}"
            ) from exc
        return record

    def get(self, resource_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT resource_json,resource_sha256 FROM resources WHERE resource_id=?",
                (resource_id,),
            ).fetchone()
        if row is None:
            raise ResourceCatalogError(f"resource not found: {resource_id}")
        return self._decode(resource_id, row[0], row[1])

    def list(
        self,
        *,
        search: str | None = None,
        resource_type: str | None = None,
        trust_state: str | None = None,
    ) -> list[dict[str, str]]:
        query = "SELECT resource_id,resource_json,resource_sha256 FROM resources"
        clauses = []
        params: list[str] = []
        if resource_type is not None:
            clauses.append("json_extract(resource_json,'$.resource_type')=?")
            params.append(resource_type)
        if trust_state is not None:
            clauses.append("json_extract(resource_json,'$.trust_state')=?")
            params.append(trust_state)
        if search:
            clauses.append(
                "(instr(lower(resource_json),lower(?))>0)"
            )
            params.append(search)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY resource_id"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        result = []
        for resource_id, encoded, digest in rows:
            record = self._decode(resource_id, encoded, digest)
            result.append(
                {
                    "id": record["id"],
                    "name": record["name"],
                    "resource_type": record["resource_type"],
                    "license_status": record["license_status"],
                    "trust_state": record["trust_state"],
                }
            )
        return result

    def update_trust_state(
        self, resource_id: str, target: str, *, reason: str
    ) -> dict[str, Any]:
        if not reason.strip():
            raise ResourceCatalogError("a non-empty reason is required")
        if target not in self._TRANSITIONS:
            raise ResourceCatalogError(f"unknown trust state: {target}")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT resource_json,resource_sha256 FROM resources WHERE resource_id=?",
                (resource_id,),
            ).fetchone()
            if row is None:
                raise ResourceCatalogError(f"resource not found: {resource_id}")
            record = self._decode(resource_id, row[0], row[1])
            current = record["trust_state"]
            if target not in self._TRANSITIONS[current]:
                raise ResourceCatalogError(
                    f"trust transition not allowed: {current} -> {target}"
                )
            record["trust_state"] = target
            encoded, digest = self._encode(record)
            now = datetime.now(UTC).isoformat()
            connection.execute(
                """UPDATE resources SET resource_json=?,resource_sha256=?,updated_at=?
                WHERE resource_id=?""",
                (encoded, digest, now, resource_id),
            )
            self._audit(
                connection, resource_id, "resource.trust_changed",
                {"from": current, "to": target, "reason": reason},
            )
        return record

    def audit_events(self, resource_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT resource_id,event_type,timestamp,details_json FROM resource_audit"
        params: tuple[Any, ...] = ()
        if resource_id is not None:
            query += " WHERE resource_id=?"
            params = (resource_id,)
        query += " ORDER BY sequence"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [
            {
                "resource_id": row[0],
                "event_type": row[1],
                "timestamp": row[2],
                "details": json.loads(row[3]),
            }
            for row in rows
        ]

    def _decode(self, resource_id: str, encoded: str, digest: str) -> dict[str, Any]:
        actual = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        if actual != digest:
            raise ResourceCatalogError(f"resource integrity check failed: {resource_id}")
        try:
            record = json.loads(encoded)
            self._validator.validate(record)
        except (ValueError, ValidationError) as exc:
            raise ResourceCatalogError(f"stored resource is invalid: {resource_id}") from exc
        if record.get("id") != resource_id:
            raise ResourceCatalogError(f"resource key does not match record: {resource_id}")
        return record

    @staticmethod
    def _audit(
        connection: sqlite3.Connection,
        resource_id: str,
        event_type: str,
        details: dict[str, Any],
    ) -> None:
        connection.execute(
            """INSERT INTO resource_audit
            (resource_id,event_type,timestamp,details_json) VALUES(?,?,?,?)""",
            (
                resource_id,
                event_type,
                datetime.now(UTC).isoformat(),
                json.dumps(details, sort_keys=True),
            ),
        )
