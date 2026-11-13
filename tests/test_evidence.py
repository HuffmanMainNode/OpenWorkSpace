import hashlib
import json
import os
import statistics
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path
from threading import Event

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
    from openworkspace.evidence import JournalTornTailError

    with pytest.raises(JournalTornTailError, match="torn tail"):
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
    per_worker = 50
    with ProcessPoolExecutor(max_workers=workers) as executor:
        list(executor.map(
            _append_from_process,
            [(str(journal), worker, per_worker) for worker in range(workers)],
        ))
    events = read_events(journal)
    assert len(events) == workers * per_worker
    assert len({event["event_id"] for event in events}) == workers * per_worker


def test_append_rejects_torn_tail_without_modifying_journal(tmp_path):
    from openworkspace.evidence import JournalTornTailError

    journal = tmp_path / "torn.jsonl"
    append_event(journal, event_type="test", actor="tester", subject="one", result="ok")
    with journal.open("ab") as stream:
        stream.write(b'{"partial":')
    before = journal.read_bytes()
    with pytest.raises(JournalTornTailError, match="torn tail"):
        append_event(journal, event_type="test", actor="tester", subject="two", result="ok")
    assert journal.read_bytes() == before


def test_read_events_can_return_verified_prefix_of_torn_journal(tmp_path):
    from openworkspace.evidence import JournalTornTailError

    journal = tmp_path / "torn-prefix.jsonl"
    append_event(journal, event_type="test", actor="tester", subject="one", result="ok")
    with journal.open("ab") as stream:
        stream.write(b'{"partial":')
    with pytest.raises(JournalTornTailError, match="torn tail"):
        read_events(journal)
    assert len(read_events(journal, allow_torn_tail=True)) == 1


def test_repair_moves_torn_fragment_and_appends_recovery_event(tmp_path):
    from openworkspace.evidence import repair_evidence

    journal = tmp_path / "repair.jsonl"
    append_event(journal, event_type="test", actor="tester", subject="one", result="ok")
    fragment = b'{"partial":"preserve me"'
    with journal.open("ab") as stream:
        stream.write(fragment)

    result = repair_evidence(journal)
    saved = Path(result["fragment_path"])
    assert saved.read_bytes() == fragment
    if os.name == "posix":
        assert saved.stat().st_mode & 0o777 == 0o600
    events = read_events(journal)
    assert events[-1]["event_type"] == "journal.recovered"
    assert events[-1]["metadata"] == {
        "fragment_length": len(fragment),
        "fragment_sha256": hashlib.sha256(fragment).hexdigest(),
    }


def test_repair_refuses_clean_journal_without_modification(tmp_path):
    from openworkspace.evidence import repair_evidence

    journal = tmp_path / "clean.jsonl"
    append_event(journal, event_type="test", actor="tester", subject="one", result="ok")
    before = journal.read_bytes()
    with pytest.raises(ValueError, match="torn tail"):
        repair_evidence(journal)
    assert journal.read_bytes() == before


def test_repair_refuses_corrupt_complete_line_without_modification(tmp_path):
    from openworkspace.evidence import repair_evidence

    journal = tmp_path / "corrupt.jsonl"
    append_event(journal, event_type="test", actor="tester", subject="one", result="ok")
    event = json.loads(journal.read_text(encoding="utf-8"))
    event["result"] = "tampered"
    journal.write_text(json.dumps(event) + "\n" + '{"partial":', encoding="utf-8")
    before = journal.read_bytes()
    with pytest.raises(ValueError, match="integrity"):
        repair_evidence(journal)
    assert journal.read_bytes() == before


def test_append_accepts_schema_validated_metadata(tmp_path):
    journal = tmp_path / "metadata.jsonl"
    event = append_event(
        journal, event_type="test", actor="tester", subject="one", result="ok",
        metadata={"ticket": "WSP-032", "attempt": 2},
    )
    assert event["metadata"] == {"ticket": "WSP-032", "attempt": 2}
    assert read_events(journal)[0]["metadata"] == event["metadata"]


def test_evidence_validator_is_cached(tmp_path):
    from openworkspace.evidence import _validator

    _validator.cache_clear()
    journal = tmp_path / "cached.jsonl"
    append_event(journal, event_type="test", actor="tester", subject="one", result="ok")
    append_event(journal, event_type="test", actor="tester", subject="two", result="ok")
    assert _validator.cache_info().misses == 1
    _validator.cache_clear()


def test_readers_during_writes_never_observe_false_integrity_failure(tmp_path):
    ready = Event()
    finished = Event()
    errors = []
    journal = tmp_path / "concurrent-read.jsonl"

    def writer():
        for index in range(120):
            append_event(
                journal, event_type="reader-writer", actor="writer",
                subject=str(index), result="written",
            )
            if index == 0:
                ready.set()
        finished.set()

    def reader():
        ready.wait(timeout=10)
        while not finished.is_set():
            try:
                read_events(journal)
            except Exception as exc:
                errors.append(exc)
                return

    with ThreadPoolExecutor(max_workers=2) as executor:
        write_future = executor.submit(writer)
        read_future = executor.submit(reader)
        write_future.result(timeout=30)
        read_future.result(timeout=30)
    assert errors == []
    assert len(read_events(journal)) == 120


def test_tail_truncation_is_not_detected_documented_limit(tmp_path):
    journal = tmp_path / "tail-truncation.jsonl"
    append_event(journal, event_type="test", actor="tester", subject="one", result="ok")
    append_event(journal, event_type="test", actor="tester", subject="two", result="ok")
    lines = journal.read_bytes().splitlines(keepends=True)
    journal.write_bytes(lines[0])
    assert len(read_events(journal)) == 1


def test_rechained_forgery_is_not_detected_documented_limit(tmp_path):
    journal = tmp_path / "rechained-forgery.jsonl"
    append_event(journal, event_type="test", actor="tester", subject="one", result="ok")
    append_event(journal, event_type="test", actor="tester", subject="two", result="ok")
    events = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()]
    for index, event in enumerate(events):
        event.pop("hash")
        if index == 0:
            event["result"] = "forged but rechained"
        else:
            event["previous_hash"] = events[index - 1]["hash"]
        canonical = json.dumps(
            event, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        event["hash"] = hashlib.sha256(canonical).hexdigest()
    journal.write_text(
        "".join(json.dumps(event, sort_keys=True, ensure_ascii=False) + "\n" for event in events),
        encoding="utf-8",
    )
    assert len(read_events(journal)) == 2


def test_append_latency_does_not_scale_with_journal_length(tmp_path):
    journal = tmp_path / "latency.jsonl"
    timings = []
    for index in range(3000):
        started = time.perf_counter()
        append_event(
            journal, event_type="latency.test", actor="tester",
            subject=str(index), result="written",
        )
        timings.append(time.perf_counter() - started)
    first = statistics.median(timings[:200])
    last = statistics.median(timings[-200:])
    assert last <= first * 3, f"append latency grew from {first:.6f}s to {last:.6f}s"


def test_append_uses_one_append_write_and_restrictive_file_mode(tmp_path, monkeypatch):
    import openworkspace.evidence as evidence

    writes = []
    original_write = evidence.os.write

    def tracked_write(descriptor, data):
        writes.append(data)
        return original_write(descriptor, data)

    monkeypatch.setattr(evidence.os, "write", tracked_write)
    journal = tmp_path / "single-write.jsonl"
    append_event(journal, event_type="test", actor="tester", subject="one", result="ok")
    event_writes = [payload for payload in writes if payload.endswith(b"\\n")]
    assert len(event_writes) == 1
    if os.name == "posix":
        assert journal.stat().st_mode & 0o777 == 0o600


def test_append_refuses_corrupt_complete_final_event(tmp_path):
    journal = tmp_path / "corrupt-final.jsonl"
    append_event(journal, event_type="test", actor="tester", subject="one", result="ok")
    event = json.loads(journal.read_text(encoding="utf-8"))
    event["result"] = "tampered"
    journal.write_text(json.dumps(event) + "\\n", encoding="utf-8")
    before = journal.read_bytes()
    with pytest.raises(ValueError, match="integrity check failed"):
        append_event(journal, event_type="test", actor="tester", subject="two", result="ok")
    assert journal.read_bytes() == before


def test_first_append_fsyncs_parent_directory(tmp_path, monkeypatch):
    import openworkspace.evidence as evidence

    synced = []
    original_fsync_directory = evidence._fsync_directory

    def tracked_fsync_directory(directory):
        synced.append(directory)
        original_fsync_directory(directory)

    monkeypatch.setattr(evidence, "_fsync_directory", tracked_fsync_directory)
    journal = tmp_path / "first-event.jsonl"
    append_event(journal, event_type="test", actor="tester", subject="one", result="ok")
    assert synced == [tmp_path]


def test_append_rejects_non_object_metadata_before_writing(tmp_path):
    from jsonschema import ValidationError

    journal = tmp_path / "invalid-metadata.jsonl"
    with pytest.raises(ValidationError):
        append_event(
            journal, event_type="test", actor="tester", subject="one",
            result="ok", metadata=["not", "an", "object"],
        )
    assert not journal.exists()


def test_short_append_write_leaves_detectable_torn_tail(tmp_path, monkeypatch):
    import openworkspace.evidence as evidence
    from openworkspace.evidence import JournalTornTailError

    original_write = evidence.os.write
    journal = tmp_path / "short-write.jsonl"

    def short_write(descriptor, data):
        return original_write(descriptor, data[:12])

    monkeypatch.setattr(evidence.os, "write", short_write)
    with pytest.raises(OSError, match="short evidence journal write"):
        append_event(journal, event_type="test", actor="tester", subject="one", result="ok")
    monkeypatch.setattr(evidence.os, "write", original_write)
    assert not journal.read_bytes().endswith(b"\\n")
    with pytest.raises(JournalTornTailError):
        append_event(journal, event_type="test", actor="tester", subject="two", result="ok")


def test_repair_restores_original_torn_bytes_if_recovery_append_fails(tmp_path, monkeypatch):
    import openworkspace.evidence as evidence

    journal = tmp_path / "repair-rollback.jsonl"
    append_event(journal, event_type="test", actor="tester", subject="one", result="ok")
    fragment = b'{"partial":"rollback"'
    with journal.open("ab") as stream:
        stream.write(fragment)
    before = journal.read_bytes()
    original_write = evidence.os.write
    calls = 0

    def fail_recovery_write(descriptor, data):
        nonlocal calls
        calls += 1
        if calls == 2:
            return original_write(descriptor, data[:12])
        return original_write(descriptor, data)

    monkeypatch.setattr(evidence.os, "write", fail_recovery_write)
    with pytest.raises(OSError, match="short evidence journal write"):
        evidence.repair_evidence(journal)
    assert journal.read_bytes() == before
