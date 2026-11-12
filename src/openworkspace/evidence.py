"""Append-only JSONL evidence journal with a verifiable hash chain."""


"""Append-only JSONL evidence journal with a verifiable hash chain."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

if os.name == "nt":
    import msvcrt
else:
    import fcntl

GENESIS = "0" * 64
EVIDENCE_SCHEMA_PATH = Path(__file__).with_name("evidence.schema.json")


def _canonical(value: dict[str, Any]) -> bytes:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return encoded.encode("utf-8")


def _validator() -> Draft202012Validator:
    schema = json.loads(EVIDENCE_SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


@contextmanager
def _exclusive_journal_lock(journal: Path) -> Iterator[None]:
    """Serialize journal writers across threads and processes on supported OSes."""
    lock_path = journal.with_name(journal.name + ".lock")
    with lock_path.open("a+b") as lock_file:
        if os.name == "nt":
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
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def append_event(
    path: str | Path,
    *,
    event_type: str,
    actor: str,
    subject: str,
    result: str,
) -> dict[str, Any]:
    """Append one event and return it. This is tamper-evident, not tamper-proof."""
    journal = Path(path)
    journal.parent.mkdir(parents=True, exist_ok=True)
    with _exclusive_journal_lock(journal):
        previous = GENESIS
        if journal.exists() and journal.stat().st_size:
            events = read_events(journal)
            previous = events[-1]["hash"]
        event: dict[str, Any] = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "actor": actor,
            "subject": subject,
            "result": result,
            "source": None,
            "metadata": {},
            "previous_hash": previous,
        }
        _validator().validate({**event, "hash": "0" * 64})
        event["hash"] = hashlib.sha256(_canonical(event)).hexdigest()
        with journal.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(event, sort_keys=True, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        return event


def read_events(path: str | Path) -> list[dict[str, Any]]:
    """Read journal entries and reject missing, empty, malformed, or altered journals."""
    journal = Path(path)
    if not journal.exists():
        raise FileNotFoundError(f"evidence journal does not exist: {journal}")
    if not journal.stat().st_size:
        raise ValueError(f"evidence journal is empty: {journal}")
    events: list[dict[str, Any]] = []
    previous = GENESIS
    validator = _validator()
    with journal.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                raise ValueError(f"blank journal line at {line_number}")
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at journal line {line_number}") from exc
            if not isinstance(event, dict) or "hash" not in event:
                raise ValueError(f"invalid event at journal line {line_number}")
            supplied_hash = event.pop("hash")
            try:
                validator.validate({**event, "hash": supplied_hash})
            except Exception as exc:
                raise ValueError(f"invalid event schema at journal line {line_number}") from exc
            if event.get("previous_hash") != previous:
                raise ValueError(f"broken hash link at journal line {line_number}")
            expected_hash = hashlib.sha256(_canonical(event)).hexdigest()
            if not isinstance(supplied_hash, str) or supplied_hash != expected_hash:
                raise ValueError(f"integrity check failed at journal line {line_number}")
            event["hash"] = supplied_hash
            events.append(event)
            previous = supplied_hash
    return events
