"""Local task lifecycle store. Tasks are records; this module does not execute them."""

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


class TaskError(ValueError):
    """Raised when a task operation is invalid."""


class TaskStore:
    """Transactional local task state store with dependency-aware readiness."""

    _TRANSITIONS = {
        "pending": {"ready", "blocked", "cancelled"},
        "ready": {"running", "blocked", "cancelled"},
        "running": {"succeeded", "failed", "cancelled"},
        "failed": {"pending", "blocked"},
        "blocked": {"pending", "cancelled"},
        "succeeded": set(),
        "cancelled": set(),
    }

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._validator = Draft202012Validator(
            json.loads(Path(__file__).with_name("task.schema.json").read_text(encoding="utf-8")),
            format_checker=FormatChecker(),
        )
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY, task_json TEXT NOT NULL,
                    task_sha256 TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS task_audit (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
                    event_type TEXT NOT NULL, timestamp TEXT NOT NULL, details_json TEXT NOT NULL
                )"""
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10.0)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @staticmethod
    def _encode(task: dict[str, Any]) -> tuple[str, str]:
        encoded = json.dumps(task, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return encoded, hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def create(self, task: dict[str, Any]) -> dict[str, Any]:
        errors = sorted(self._validator.iter_errors(task), key=lambda item: list(item.path))
        if errors:
            raise TaskError(f"invalid task: {errors[0].message}")
        if task["state"] != "pending":
            raise TaskError("new tasks must begin in pending state")
        encoded, digest = self._encode(task)
        now = datetime.now(UTC).isoformat()
        try:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                for dependency in task["dependencies"]:
                    row = connection.execute(
                        "SELECT task_json FROM tasks WHERE task_id = ?", (dependency,)
                    ).fetchone()
                    if row is None:
                        raise TaskError(f"dependency not found: {dependency}")
                    if dependency == task["id"]:
                        raise TaskError("a task cannot depend on itself")
                connection.execute(
                    """INSERT INTO tasks(task_id,task_json,task_sha256,created_at,updated_at)
                    VALUES(?,?,?,?,?)""",
                    (task["id"], encoded, digest, now, now),
                )
                self._audit(connection, task["id"], "task.created", {})
        except sqlite3.IntegrityError as exc:
            raise TaskError(f"task already exists: {task['id']}") from exc
        return task

    def get(self, task_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT task_json,task_sha256 FROM tasks WHERE task_id=?", (task_id,)
            ).fetchone()
        if row is None:
            raise TaskError(f"task not found: {task_id}")
        if hashlib.sha256(row[0].encode("utf-8")).hexdigest() != row[1]:
            raise TaskError(f"task integrity check failed: {task_id}")
        task = json.loads(row[0])
        errors = list(self._validator.iter_errors(task))
        if errors:
            raise TaskError(f"stored task is invalid: {task_id}")
        return task

    def transition(self, task_id: str, target: str, *, reason: str) -> dict[str, Any]:
        if not reason.strip():
            raise TaskError("a non-empty reason is required for task transitions")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT task_json,task_sha256,attempts FROM tasks WHERE task_id=?", (task_id,)
            ).fetchone()
            if row is None:
                raise TaskError(f"task not found: {task_id}")
            if hashlib.sha256(row[0].encode("utf-8")).hexdigest() != row[1]:
                raise TaskError(f"task integrity check failed: {task_id}")
            task = json.loads(row[0])
            current = task["state"]
            if target not in self._TRANSITIONS.get(current, set()):
                raise TaskError(f"task transition not allowed: {current} -> {target}")
            if target == "ready":
                for dependency in task["dependencies"]:
                    dependency_row = connection.execute(
                        "SELECT task_json,task_sha256 FROM tasks WHERE task_id=?", (dependency,)
                    ).fetchone()
                    if dependency_row is None:
                        raise TaskError(f"dependency not found: {dependency}")
                    dependency_digest = hashlib.sha256(
                        dependency_row[0].encode("utf-8")
                    ).hexdigest()
                    if dependency_digest != dependency_row[1]:
                        raise TaskError(f"dependency integrity check failed: {dependency}")
                    if json.loads(dependency_row[0])["state"] != "succeeded":
                        raise TaskError(f"dependency is not complete: {dependency}")
            attempts = row[2]
            if target == "running":
                attempts += 1
            if target == "pending" and attempts >= task["retry_policy"]["max_attempts"]:
                raise TaskError("retry limit reached")
            task["state"] = target
            encoded, digest = self._encode(task)
            now = datetime.now(UTC).isoformat()
            connection.execute(
                """UPDATE tasks SET task_json=?,task_sha256=?,attempts=?,updated_at=?
                WHERE task_id=?""",
                (encoded, digest, attempts, now, task_id),
            )
            self._audit(
                connection, task_id, "task.state_changed",
                {"from": current, "to": target, "reason": reason, "attempts": attempts},
            )
        return task

    def list(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT task_json,task_sha256 FROM tasks ORDER BY task_id"
            ).fetchall()
        result = []
        for encoded, digest in rows:
            if hashlib.sha256(encoded.encode("utf-8")).hexdigest() != digest:
                raise TaskError("task integrity check failed during listing")
            task = json.loads(encoded)
            result.append({"id": task["id"], "owner": task["owner"], "state": task["state"]})
        return result

    def audit_events(self, task_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT task_id,event_type,timestamp,details_json FROM task_audit"
        params: tuple[Any, ...] = ()
        if task_id is not None:
            query += " WHERE task_id=?"
            params = (task_id,)
        query += " ORDER BY sequence"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [
            {"task_id": row[0], "event_type": row[1], "timestamp": row[2],
             "details": json.loads(row[3])}
            for row in rows
        ]

    @staticmethod
    def _audit(connection: sqlite3.Connection, task_id: str, event: str, details: dict) -> None:
        connection.execute(
            "INSERT INTO task_audit(task_id,event_type,timestamp,details_json) VALUES(?,?,?,?)",
            (task_id, event, datetime.now(UTC).isoformat(), json.dumps(details, sort_keys=True)),
        )
