import json
from concurrent.futures import ProcessPoolExecutor

import pytest

from openworkspace.evidence import append_event, read_events


def test_evidence_chain_verifies(tmp_path):
    journal = tmp_path / "events.jsonl"
    append_event(journal, event_type="test", actor="tester", subject="unit", result="pass")
    append_event(journal, event_type="test", actor="tester", subject="unit", result="pass")
    assert len(read_events(journal)) == 2


def test_modified_event_is_detected(tmp_path):
    journal = tmp_path / "events.jsonl"
    append_event(journal, event_type="test", actor="tester", subject="unit", result="pass")
    event = json.loads(journal.read_text())
    event["result"] = "changed"
    journal.write_text(json.dumps(event) + "\n")
    with pytest.raises(ValueError, match="integrity check failed"):
        read_events(journal)


def test_broken_link_is_detected(tmp_path):
    journal = tmp_path / "events.jsonl"
    append_event(journal, event_type="one", actor="tester", subject="unit", result="pass")
    append_event(journal, event_type="two", actor="tester", subject="unit", result="pass")
    lines = journal.read_text().splitlines()
    second = json.loads(lines[1])
    second["previous_hash"] = "f" * 64
    journal.write_text(lines[0] + "\n" + json.dumps(second) + "\n")
    with pytest.raises(ValueError, match="broken hash link"):
        read_events(journal)


def test_missing_journal_fails_closed(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_events(tmp_path / "missing.jsonl")


def test_empty_journal_fails_closed(tmp_path):
    journal = tmp_path / "empty.jsonl"
    journal.touch()
    with pytest.raises(ValueError, match="empty"):
        read_events(journal)


def test_truncated_journal_record_fails(tmp_path):
    journal = tmp_path / "events.jsonl"
    append_event(journal, event_type="test", actor="tester", subject="unit", result="pass")
    journal.write_text(journal.read_text().rstrip("\n"))
    journal.write_text(journal.read_text() + '{"partial":')
    with pytest.raises(ValueError, match="invalid JSON"):
        read_events(journal)


def _append_from_process(arguments):
    path, process_id, count = arguments
    for index in range(count):
        append_event(
            path,
            event_type="concurrency.test",
            actor=f"process-{process_id}",
            subject=f"event-{index}",
            result="written",
        )


def test_parallel_process_writers_preserve_complete_hash_chain(tmp_path):
    journal = tmp_path / "parallel.jsonl"
    workers = 4
    per_worker = 8
    with ProcessPoolExecutor(max_workers=workers) as executor:
        list(executor.map(
            _append_from_process,
            [(str(journal), worker, per_worker) for worker in range(workers)],
        ))
    events = read_events(journal)
    assert len(events) == workers * per_worker
    assert len({event["event_id"] for event in events}) == workers * per_worker
