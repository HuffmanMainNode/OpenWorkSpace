"""Append-only JSONL evidence journal with a verifiable hash chain."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

GENESIS = "0" * 64
EVIDENCE_SCHEMA_PATH = Path(__file__).with_name("evidence.schema.json")


class JournalTornTailError(ValueError):
    """Raised when the final journal record is not newline-terminated."""


class JournalRepairError(ValueError):
    """Raised when a journal cannot be repaired safely."""


def _canonical(value: dict[str, Any]) -> bytes:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return encoded.encode("utf-8")


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    """Load and compile the packaged event schema once per process."""
    schema = json.loads(EVIDENCE_SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


@contextmanager
def _journal_lock(journal: Path, *, shared: bool = False) -> Iterator[None]:
    """Coordinate readers and writers across threads and processes."""
    lock_path = journal.with_name(journal.name + ".lock")
    with lock_path.open("a+b") as lock_file:
        if sys.platform == "win32":
            lock_file.seek(0, os.SEEK_END)
            if lock_file.tell() == 0:
                lock_file.write(b"0")
                lock_file.flush()
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            operation = fcntl.LOCK_SH if shared else fcntl.LOCK_EX
            fcntl.flock(lock_file.fileno(), operation)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _fsync_directory(directory: Path) -> None:
    """Persist a newly created directory entry where directory fsync is supported."""
    if sys.platform == "win32":
        return
    descriptor = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _decode_event(line: bytes, line_number: int) -> dict[str, Any]:
    try:
        event = json.loads(line.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON at journal line {line_number}") from exc
    if not isinstance(event, dict) or "hash" not in event:
        raise ValueError(f"invalid event at journal line {line_number}")

    supplied_hash = event.pop("hash")
    try:
        _validator().validate({**event, "hash": supplied_hash})
    except ValidationError as exc:
        raise ValueError(f"invalid event schema at journal line {line_number}") from exc

    expected_hash = hashlib.sha256(_canonical(event)).hexdigest()
    if not isinstance(supplied_hash, str) or supplied_hash != expected_hash:
        raise ValueError(f"integrity check failed at journal line {line_number}")
    event["hash"] = supplied_hash
    return event


def _parse_complete_lines(raw: bytes) -> list[dict[str, Any]]:
    if not raw:
        return []
    if not raw.endswith(b"\n"):
        raise JournalTornTailError("evidence journal has a torn final line")

    events: list[dict[str, Any]] = []
    previous = GENESIS
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            raise ValueError(f"blank journal line at {line_number}")
        event = _decode_event(line, line_number)
        if event.get("previous_hash") != previous:
            raise ValueError(f"broken hash link at journal line {line_number}")
        events.append(event)
        previous = event["hash"]
    return events


def _read_events_unlocked(journal: Path, *, allow_torn_tail: bool) -> list[dict[str, Any]]:
    if not journal.exists():
        raise FileNotFoundError(f"evidence journal does not exist: {journal}")
    raw = journal.read_bytes()
    if not raw:
        raise ValueError(f"evidence journal is empty: {journal}")

    if not raw.endswith(b"\n"):
        if not allow_torn_tail:
            raise JournalTornTailError(f"evidence journal has a torn final line: {journal}")
        complete_end = raw.rfind(b"\n") + 1
        raw = raw[:complete_end]
        if not raw:
            return []
    return _parse_complete_lines(raw)


def _last_event_hash_unlocked(journal: Path) -> str:
    """Validate only the final complete event; full-chain checks belong to read_events."""
    if not journal.exists():
        return GENESIS

    with journal.open("rb") as stream:
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
        if size == 0:
            return GENESIS
        stream.seek(size - 1)
        if stream.read(1) != b"\n":
            raise JournalTornTailError(f"evidence journal has a torn final line: {journal}")

        cursor = size - 1
        line_start = 0
        while cursor > 0:
            chunk_start = max(0, cursor - 4096)
            stream.seek(chunk_start)
            chunk = stream.read(cursor - chunk_start)
            previous_newline = chunk.rfind(b"\\n")
            if previous_newline >= 0:
                line_start = chunk_start + previous_newline + 1
                break
            cursor = chunk_start

        stream.seek(line_start)
        final_line = stream.read(size - line_start - 1)

    if not final_line.strip():
        raise ValueError("blank final event in evidence journal")
    event = _decode_event(final_line, 0)
    return event["hash"]


def _write_event_unlocked(
    journal: Path,
    *,
    event_type: str,
    actor: str,
    subject: str,
    result: str,
    metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    previous = _last_event_hash_unlocked(journal)
    event: dict[str, Any] = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "actor": actor,
        "subject": subject,
        "result": result,
        "source": None,
        "metadata": {} if metadata is None else metadata,
        "previous_hash": previous,
    }
    _validator().validate({**event, "hash": "0" * 64})
    event["hash"] = hashlib.sha256(_canonical(event)).hexdigest()
    encoded = json.dumps(event, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n"

    created = not journal.exists()
    flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    descriptor = os.open(journal, flags, 0o600)
    try:
        if os.name == "posix":
            os.fchmod(descriptor, 0o600)
        written = os.write(descriptor, encoded)
        if written != len(encoded):
            raise OSError(f"short evidence journal write: {written} of {len(encoded)} bytes")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)

    if created:
        _fsync_directory(journal.parent)
    return event


def append_event(
    path: str | Path,
    *,
    event_type: str,
    actor: str,
    subject: str,
    result: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append one event atomically; reject torn tails rather than silently extending them."""
    journal = Path(path)
    journal.parent.mkdir(parents=True, exist_ok=True)
    with _journal_lock(journal):
        return _write_event_unlocked(
            journal,
            event_type=event_type,
            actor=actor,
            subject=subject,
            result=result,
            metadata=metadata,
        )


def read_events(
    path: str | Path, *, allow_torn_tail: bool = False
) -> list[dict[str, Any]]:
    """Read and verify the full chain; optionally return its complete prefix before a torn tail."""
    journal = Path(path)
    if not journal.exists():
        raise FileNotFoundError(f"evidence journal does not exist: {journal}")
    with _journal_lock(journal, shared=True):
        return _read_events_unlocked(journal, allow_torn_tail=allow_torn_tail)


def _write_fragment_exclusive(path: Path, fragment: bytes) -> None:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        written = os.write(descriptor, fragment)
        if written != len(fragment):
            raise OSError(f"short torn-fragment write: {written} of {len(fragment)} bytes")
        os.fsync(descriptor)
    except Exception:
        os.close(descriptor)
        path.unlink(missing_ok=True)
        raise
    else:
        os.close(descriptor)
    _fsync_directory(path.parent)


def repair_evidence(path: str | Path) -> dict[str, Any]:
    """Preserve a torn suffix, verify the preceding chain, truncate, and record recovery."""
    journal = Path(path)
    if not journal.exists():
        raise FileNotFoundError(f"evidence journal does not exist: {journal}")

    with _journal_lock(journal):
        raw = journal.read_bytes()
        if not raw:
            raise JournalRepairError("cannot repair an empty evidence journal")
        if raw.endswith(b"\n"):
            raise JournalRepairError("evidence journal does not have a torn tail")

        complete_end = raw.rfind(b"\n") + 1
        complete_prefix = raw[:complete_end]
        fragment = raw[complete_end:]
        if not fragment:
            raise JournalRepairError("evidence journal does not have a torn tail")

        # Validate the entire preceding chain before preserving or changing any bytes.
        events = _parse_complete_lines(complete_prefix) if complete_prefix else []
        fragment_sha256 = hashlib.sha256(fragment).hexdigest()
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        fragment_path = journal.with_name(f"{journal.name}.torn-{timestamp}")
        try:
            _write_fragment_exclusive(fragment_path, fragment)
        except FileExistsError as exc:
            raise JournalRepairError(
                f"torn-fragment destination already exists: {fragment_path}"
            ) from exc

        try:
            with journal.open("r+b") as stream:
                stream.truncate(complete_end)
                stream.flush()
                os.fsync(stream.fileno())
            _write_event_unlocked(
                journal,
                event_type="journal.recovered",
                actor="openworkspace",
                subject=journal.name,
                result="recovered",
                metadata={
                    "fragment_length": len(fragment),
                    "fragment_sha256": fragment_sha256,
                },
            )
        except Exception as exc:
            try:
                with journal.open("r+b") as stream:
                    stream.truncate(complete_end)
                    stream.seek(complete_end)
                    stream.write(fragment)
                    stream.flush()
                    os.fsync(stream.fileno())
            except Exception as restore_exc:
                raise JournalRepairError(
                    "repair failed and the original torn suffix could not be restored; "
                    f"preserved fragment: {fragment_path}; restore error: {restore_exc}"
                ) from exc
            raise

        return {
            "repaired": True,
            "fragment_path": str(fragment_path),
            "fragment_length": len(fragment),
            "fragment_sha256": fragment_sha256,
            "verified_events_before_repair": len(events),
        }
