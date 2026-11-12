import sqlite3

import pytest

from openworkspace.identity import IdentityError, IdentityRegistry
from openworkspace.tasks import TaskError, TaskStore

IDENTITY = {
    "id": "local.example.user",
    "kind": "user",
    "issuer": "local-workspace",
    "key_reference": None,
    "status": "active",
    "valid_from": "2026-11-12T00:00:00Z",
    "valid_until": None,
    "attributes": {"label": "Example User"},
}

def make_task(task_id, dependencies=None):
    return {
        "id": task_id,
        "owner": "local.example.user",
        "state": "pending",
        "inputs": {"example": True},
        "dependencies": dependencies or [],
        "deadline": None,
        "retry_policy": {"max_attempts": 2, "backoff_seconds": 0},
        "idempotency_key": task_id,
    }


def test_identity_create_read_and_status_lifecycle(tmp_path):
    registry = IdentityRegistry(tmp_path / "runtime.sqlite3")
    assert registry.create(IDENTITY) == IDENTITY
    assert registry.get(IDENTITY["id"]) == IDENTITY
    suspended = registry.set_status(IDENTITY["id"], "suspended", reason="Test suspension")
    assert suspended["status"] == "suspended"
    active = registry.set_status(IDENTITY["id"], "active", reason="Test reactivation")
    assert active["status"] == "active"
    assert [e["event_type"] for e in registry.audit_events()] == [
        "identity.created", "identity.status_changed", "identity.status_changed"
    ]


def test_identity_rejects_duplicate_and_irreversible_reactivation(tmp_path):
    registry = IdentityRegistry(tmp_path / "runtime.sqlite3")
    registry.create(IDENTITY)
    with pytest.raises(IdentityError, match="already exists"):
        registry.create(IDENTITY)
    registry.set_status(IDENTITY["id"], "revoked", reason="Revocation test")
    with pytest.raises(IdentityError, match="not allowed"):
        registry.set_status(IDENTITY["id"], "active", reason="Must not reactivate")


def test_identity_requires_reason_and_valid_record(tmp_path):
    registry = IdentityRegistry(tmp_path / "runtime.sqlite3")
    with pytest.raises(IdentityError, match="active status"):
        registry.create({**IDENTITY, "status": "unknown"})
    with pytest.raises(IdentityError, match="reason"):
        registry.create(IDENTITY)
        registry.set_status(IDENTITY["id"], "suspended", reason=" ")


def test_identity_detects_database_tampering(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    registry = IdentityRegistry(path)
    registry.create(IDENTITY)
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE identities SET record_json=? WHERE identity_id=?",
            ('{"id":"tampered"}', IDENTITY["id"]),
        )
    with pytest.raises(IdentityError, match="integrity"):
        registry.get(IDENTITY["id"])


def test_task_lifecycle_and_audit(tmp_path):
    database = tmp_path / "runtime.sqlite3"
    IdentityRegistry(database).create(IDENTITY)
    store = TaskStore(database)
    task = store.create(make_task("task.one"))
    assert task["state"] == "pending"
    ready = store.transition("task.one", "ready", reason="Dependencies satisfied")
    assert ready["state"] == "ready"
    running = store.transition("task.one", "running", reason="Worker claimed task")
    assert running["state"] == "running"
    succeeded = store.transition("task.one", "succeeded", reason="Work completed")
    assert succeeded["state"] == "succeeded"
    assert [e["event_type"] for e in store.audit_events()] == [
        "task.created", "task.state_changed", "task.state_changed", "task.state_changed"
    ]


def test_task_dependencies_must_succeed_before_ready(tmp_path):
    database = tmp_path / "runtime.sqlite3"
    IdentityRegistry(database).create(IDENTITY)
    store = TaskStore(database)
    store.create(make_task("task.parent"))
    store.create(make_task("task.child", ["task.parent"]))
    with pytest.raises(TaskError, match="not complete"):
        store.transition("task.child", "ready", reason="Premature scheduling")
    store.transition("task.parent", "ready", reason="No dependencies")
    store.transition("task.parent", "running", reason="Claimed")
    store.transition("task.parent", "succeeded", reason="Completed")
    assert store.transition("task.child", "ready", reason="Parent completed")["state"] == "ready"


def test_task_rejects_missing_dependencies_duplicate_and_invalid_transitions(tmp_path):
    database = tmp_path / "runtime.sqlite3"
    IdentityRegistry(database).create(IDENTITY)
    store = TaskStore(database)
    with pytest.raises(TaskError, match="dependency not found"):
        store.create(make_task("task.orphan", ["missing"]))
    store.create(make_task("task.one"))
    with pytest.raises(TaskError, match="already exists"):
        store.create(make_task("task.one"))
    with pytest.raises(TaskError, match="not allowed"):
        store.transition("task.one", "succeeded", reason="Skip lifecycle")


def test_task_retry_limit_and_required_reason(tmp_path):
    database = tmp_path / "runtime.sqlite3"
    IdentityRegistry(database).create(IDENTITY)
    store = TaskStore(database)
    store.create(make_task("task.retry"))
    store.transition("task.retry", "ready", reason="Ready")
    store.transition("task.retry", "running", reason="Attempt one")
    store.transition("task.retry", "failed", reason="Failed attempt")
    store.transition("task.retry", "pending", reason="Retry requested")
    store.transition("task.retry", "ready", reason="Ready again")
    store.transition("task.retry", "running", reason="Attempt two")
    store.transition("task.retry", "failed", reason="Second failure")
    with pytest.raises(TaskError, match="retry limit"):
        store.transition("task.retry", "pending", reason="No third attempt")
    with pytest.raises(TaskError, match="reason"):
        store.transition("task.retry", "blocked", reason=" ")


def test_task_detects_tampered_records(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    IdentityRegistry(path).create(IDENTITY)
    store = TaskStore(path)
    store.create(make_task("task.tamper"))
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE tasks SET task_json=? WHERE task_id=?",
            ('{"id":"tampered"}', "task.tamper"),
        )
    with pytest.raises(TaskError, match="integrity"):
        store.get("task.tamper")



def test_task_requires_active_registered_owner(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    store = TaskStore(path)
    with pytest.raises(TaskError, match="identity registry"):
        store.create(make_task("task.no-identity"))
    identities = IdentityRegistry(path)
    identities.create(IDENTITY)
    identities.set_status(IDENTITY["id"], "suspended", reason="Test")
    with pytest.raises(TaskError, match="not active"):
        store.create(make_task("task.suspended-owner"))


def test_refresh_ready_promotes_only_dependency_satisfied_tasks(tmp_path):
    database = tmp_path / "runtime.sqlite3"
    IdentityRegistry(database).create(IDENTITY)
    store = TaskStore(database)
    store.create(make_task("task.parent"))
    store.create(make_task("task.child", ["task.parent"]))
    assert store.refresh_ready() == ["task.parent"]
    assert store.get("task.child")["state"] == "pending"
    store.transition("task.parent", "running", reason="Parent claimed")
    store.transition("task.parent", "succeeded", reason="Parent done")
    assert store.refresh_ready() == ["task.child"]
    assert store.get("task.child")["state"] == "ready"



def test_identity_and_task_audit_records_reject_ordinary_mutation(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    identities = IdentityRegistry(path)
    identities.create(IDENTITY)
    tasks = TaskStore(path)
    tasks.create(make_task("task.audit"))
    with sqlite3.connect(path) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM identity_audit")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE task_audit SET event_type='changed'")
