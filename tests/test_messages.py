import sqlite3

import pytest

from openworkspace.identity import IdentityRegistry
from openworkspace.messages import DuplicateMessageError, MessageError, MessageStore

SENDER = {
    "id": "local.sender", "kind": "agent", "issuer": "local", "key_reference": None,
    "status": "active", "valid_from": None, "valid_until": None, "attributes": {}
}
RECIPIENT = {
    "id": "local.recipient", "kind": "service", "issuer": "local", "key_reference": None,
    "status": "active", "valid_from": None, "valid_until": None, "attributes": {}
}


def envelope(message_id="message.one"):
    return {
        "message_id": message_id, "sender": SENDER["id"], "recipient": RECIPIENT["id"],
        "message_type": "example.test", "schema_version": "1.0",
        "timestamp": "2026-11-12T12:00:00Z", "correlation_id": None,
        "payload": {"hello": "world"}
    }


def setup_store(path):
    identities = IdentityRegistry(path)
    identities.create(SENDER)
    identities.create(RECIPIENT)
    return MessageStore(path)


def test_message_enqueue_inbox_and_acknowledgement(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    store = setup_store(path)
    store.enqueue(envelope())
    inbox = store.inbox(RECIPIENT["id"])
    assert len(inbox) == 1
    assert inbox[0]["envelope"]["payload"] == {"hello": "world"}
    store.acknowledge("message.one", RECIPIENT["id"])
    assert store.inbox(RECIPIENT["id"]) == []
    assert store.get("message.one")["state"] == "acknowledged"
    assert [item["event_type"] for item in store.audit_events()] == [
        "message.queued", "message.acknowledged"
    ]


def test_message_requires_active_registered_sender_and_recipient(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    store = setup_store(path)
    identities = IdentityRegistry(path)
    identities.set_status(SENDER["id"], "suspended", reason="Test suspension")
    with pytest.raises(MessageError, match="not active"):
        store.enqueue(envelope())


def test_message_rejects_duplicate_id_and_wrong_recipient_ack(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    store = setup_store(path)
    store.enqueue(envelope())
    with pytest.raises(DuplicateMessageError):
        store.enqueue(envelope())
    with pytest.raises(MessageError, match="only the declared recipient"):
        store.acknowledge("message.one", SENDER["id"])


def test_message_rejects_invalid_or_oversized_envelopes(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    store = setup_store(path)
    with pytest.raises(MessageError, match="invalid message"):
        store.enqueue({**envelope(), "extra": True})
    huge = {**envelope("message.huge"), "payload": {"data": "x" * 1_100_000}}
    with pytest.raises(MessageError, match="1 MiB"):
        store.enqueue(huge)


def test_message_detects_database_tampering(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    store = setup_store(path)
    store.enqueue(envelope())
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE messages SET envelope_json=? WHERE message_id=?",
            ('{"message_id":"changed"}', "message.one"),
        )
    with pytest.raises(MessageError, match="integrity"):
        store.get("message.one")
