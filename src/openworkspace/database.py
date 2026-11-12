"""Shared SQLite connection configuration for local runtime stores."""

from __future__ import annotations

import sqlite3


BUSY_TIMEOUT_MS = 5_000


def configure_connection(connection: sqlite3.Connection, *, foreign_keys: bool = False) -> None:
    """Apply connection-scoped durability and contention settings."""
    connection.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    connection.execute("PRAGMA synchronous = NORMAL")
    if foreign_keys:
        connection.execute("PRAGMA foreign_keys = ON")


def enable_wal(connection: sqlite3.Connection) -> None:
    """Enable persistent WAL journaling and fail if SQLite cannot apply it."""
    mode = connection.execute("PRAGMA journal_mode = WAL").fetchone()
    if mode is None or str(mode[0]).lower() != "wal":
        raise sqlite3.DatabaseError("SQLite WAL mode could not be enabled")
