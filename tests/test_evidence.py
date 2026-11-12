import json

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
