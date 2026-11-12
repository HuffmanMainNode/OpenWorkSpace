"""Append-only JSONL evidence journal with a verifiable hash chain."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

GENESIS = "0" * 64


def _canonical(value: dict[str, Any]) -> bytes:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return encoded.encode("utf-8")


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
    previous = GENESIS
    if journal.exists() and journal.stat().st_size:
        events = read_events(journal)
        previous = events[-1]["hash"]
    event: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "actor": actor,
        "subject": subject,
        "result": result,
        "previous_hash": previous,
    }
    event["hash"] = hashlib.sha256(_canonical(event)).hexdigest()
    with journal.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(event, sort_keys=True, ensure_ascii=False) + "\n")
        stream.flush()
    return event


def read_events(path: str | Path) -> list[dict[str, Any]]:
    """Read journal entries and reject malformed JSON or broken hash links."""
    journal = Path(path)
    events: list[dict[str, Any]] = []
    previous = GENESIS
    if not journal.exists():
        return events
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
            if event.get("previous_hash") != previous:
                raise ValueError(f"broken hash link at journal line {line_number}")
            expected_hash = hashlib.sha256(_canonical(event)).hexdigest()
            if supplied_hash != expected_hash:
                raise ValueError(f"integrity check failed at journal line {line_number}")
            event["hash"] = supplied_hash
            events.append(event)
            previous = supplied_hash
    return events
