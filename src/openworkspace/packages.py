"""Local external-package intake metadata and artifact digest verification."""

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

class PackageIntakeError(ValueError):
    """Raised when external package metadata or artifact verification fails."""


class DuplicatePackageError(PackageIntakeError):
    """Raised when a package ID and version are already recorded."""


class PackageCatalog:
    """Record package metadata and verify bytes without unpacking or executing them."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        schema = json.loads(
            Path(__file__).with_name("plugin-manifest.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self._validator = Draft202012Validator(schema, format_checker=FormatChecker())
        with self._connect() as connection:
            enable_wal(connection)
            connection.execute(
                """CREATE TABLE IF NOT EXISTS packages (
                    package_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    manifest_json TEXT NOT NULL,
                    manifest_sha256 TEXT NOT NULL,
                    artifact_sha256 TEXT NOT NULL,
                    verified_at TEXT NOT NULL,
                    PRIMARY KEY(package_id,version)
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS package_audit (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    package_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details_json TEXT NOT NULL
                )"""
            )
            connection.executescript(
                """
                CREATE TRIGGER IF NOT EXISTS package_audit_no_update
                BEFORE UPDATE ON package_audit
                BEGIN SELECT RAISE(ABORT, 'package audit records are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS package_audit_no_delete
                BEFORE DELETE ON package_audit
                BEGIN SELECT RAISE(ABORT, 'package audit records are append-only'); END;
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

    def validate(self, manifest: dict[str, Any]) -> dict[str, Any]:
        errors = sorted(
            self._validator.iter_errors(manifest), key=lambda item: list(item.path)
        )
        if errors:
            raise PackageIntakeError(f"invalid package manifest: {errors[0].message}")
        return manifest

    def validate_file(self, path: str | Path) -> dict[str, Any]:
        source = Path(path)
        try:
            manifest = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise PackageIntakeError(f"cannot read package manifest {source}: {exc}") from exc
        if not isinstance(manifest, dict):
            raise PackageIntakeError("package manifest must be a JSON object")
        return self.validate(manifest)

    @staticmethod
    def artifact_digest(path: str | Path) -> str:
        digest = hashlib.sha256()
        try:
            with Path(path).open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
        except OSError as exc:
            raise PackageIntakeError(f"cannot read package artifact: {exc}") from exc
        return f"sha256:{digest.hexdigest()}"

    def verify_artifact(self, manifest: dict[str, Any], artifact_path: str | Path) -> str:
        self.validate(manifest)
        actual = self.artifact_digest(artifact_path)
        if actual != manifest["digest"]:
            raise PackageIntakeError(
                f"artifact digest mismatch: expected {manifest['digest']}, got {actual}"
            )
        return actual

    def register(
        self, manifest: dict[str, Any], artifact_path: str | Path
    ) -> dict[str, Any]:
        self.validate(manifest)
        artifact_digest = self.verify_artifact(manifest, artifact_path)
        encoded = json.dumps(
            manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        manifest_digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        now = datetime.now(UTC).isoformat()
        try:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """INSERT INTO packages
                    (package_id,version,manifest_json,manifest_sha256,artifact_sha256,verified_at)
                    VALUES(?,?,?,?,?,?)""",
                    (
                        manifest["id"], manifest["version"], encoded,
                        manifest_digest, artifact_digest, now,
                    ),
                )
                self._audit(
                    connection, manifest["id"], manifest["version"],
                    "package.artifact_verified_and_registered",
                    {"artifact_sha256": artifact_digest},
                )
        except sqlite3.IntegrityError as exc:
            raise DuplicatePackageError(
                f"package version already registered: {manifest['id']}@{manifest['version']}"
            ) from exc
        return self.get(manifest["id"], manifest["version"])

    def get(self, package_id: str, version: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT manifest_json,manifest_sha256,artifact_sha256,verified_at
                FROM packages WHERE package_id=? AND version=?""",
                (package_id, version),
            ).fetchone()
        if row is None:
            raise PackageIntakeError(f"package version not found: {package_id}@{version}")
        actual = hashlib.sha256(row[0].encode("utf-8")).hexdigest()
        if actual != row[1]:
            raise PackageIntakeError(f"stored package manifest integrity failed: {package_id}")
        try:
            manifest = json.loads(row[0])
            self.validate(manifest)
        except (ValueError, ValidationError) as exc:
            raise PackageIntakeError(f"stored package manifest is invalid: {package_id}") from exc
        if manifest["id"] != package_id or manifest["version"] != version:
            raise PackageIntakeError("package database key does not match its manifest")
        if row[2] != manifest["digest"]:
            raise PackageIntakeError("stored artifact digest does not match package manifest")
        return {
            "manifest": manifest,
            "artifact_sha256": row[2],
            "verified_at": row[3],
            "execution_enabled": False,
        }

    def list(self) -> list[dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT package_id,version,manifest_json,manifest_sha256,artifact_sha256
                FROM packages ORDER BY package_id,version"""
            ).fetchall()
        result = []
        for package_id, version, encoded, manifest_digest, artifact_digest in rows:
            if hashlib.sha256(encoded.encode("utf-8")).hexdigest() != manifest_digest:
                raise PackageIntakeError(f"stored package manifest integrity failed: {package_id}")
            manifest = json.loads(encoded)
            self.validate(manifest)
            if manifest["id"] != package_id or manifest["version"] != version:
                raise PackageIntakeError("package database key does not match its manifest")
            if artifact_digest != manifest["digest"]:
                raise PackageIntakeError("stored artifact digest does not match package manifest")
            result.append(
                {
                    "id": package_id,
                    "version": version,
                    "publisher": manifest["publisher"],
                    "license": manifest["license"],
                    "artifact_sha256": artifact_digest,
                }
            )
        return result

    def audit_events(self, package_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT package_id,version,event_type,timestamp,details_json FROM package_audit"
        params: tuple[Any, ...] = ()
        if package_id is not None:
            query += " WHERE package_id=?"
            params = (package_id,)
        query += " ORDER BY sequence"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [
            {
                "package_id": row[0],
                "version": row[1],
                "event_type": row[2],
                "timestamp": row[3],
                "details": json.loads(row[4]),
            }
            for row in rows
        ]

    @staticmethod
    def _audit(
        connection: sqlite3.Connection,
        package_id: str,
        version: str,
        event_type: str,
        details: dict[str, Any],
    ) -> None:
        connection.execute(
            """INSERT INTO package_audit
            (package_id,version,event_type,timestamp,details_json) VALUES(?,?,?,?,?)""",
            (
                package_id, version, event_type, datetime.now(UTC).isoformat(),
                json.dumps(details, sort_keys=True),
            ),
        )
