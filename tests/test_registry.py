import pytest

from openworkspace.registry import (
    CapabilityRegistry,
    DuplicateCapabilityError,
    RegistryError,
)

MANIFEST = {
    "id": "example.registry",
    "version": "0.1.0",
    "interface_version": "1",
    "description": "A registry fixture. It is not executable.",
    "inputs": {},
    "outputs": {},
    "permissions": ["filesystem.read", "network.connect"],
}


def test_register_get_and_list_capability(tmp_path):
    registry = CapabilityRegistry(tmp_path / "registry.sqlite3")
    registered = registry.register(MANIFEST)
    assert registered == MANIFEST
    assert registry.get("example.registry") == MANIFEST
    rows = registry.list()
    assert len(rows) == 1
    assert rows[0]["capability_id"] == "example.registry"


def test_duplicate_id_is_rejected_without_overwrite(tmp_path):
    registry = CapabilityRegistry(tmp_path / "registry.sqlite3")
    registry.register(MANIFEST)
    changed = {**MANIFEST, "description": "Changed"}
    with pytest.raises(DuplicateCapabilityError):
        registry.register(changed)
    assert registry.get("example.registry")["description"] == MANIFEST["description"]


def test_invalid_manifest_is_not_registered(tmp_path):
    registry = CapabilityRegistry(tmp_path / "registry.sqlite3")
    with pytest.raises(ValueError):
        registry.register({**MANIFEST, "permissions": ["root.access"]})
    assert registry.list() == []


def test_permission_evaluation_defaults_to_deny_and_is_audited(tmp_path):
    registry = CapabilityRegistry(tmp_path / "registry.sqlite3")
    registry.register(MANIFEST)
    decisions = registry.evaluate("example.registry", {"filesystem.read"})
    assert [item.allowed for item in decisions] == [True, False]
    events = registry.audit_events()
    assert [item["event_type"] for item in events] == [
        "capability.registered",
        "capability.permissions_evaluated",
    ]
    assert events[-1]["details"]["decisions"][1]["reason"] == "no matching explicit grant"


def test_remove_is_audited_and_missing_id_fails(tmp_path):
    registry = CapabilityRegistry(tmp_path / "registry.sqlite3")
    registry.register(MANIFEST)
    registry.remove("example.registry")
    assert registry.list() == []
    assert registry.audit_events()[-1]["event_type"] == "capability.removed"
    with pytest.raises(RegistryError, match="not found"):
        registry.remove("example.registry")


def test_stored_manifest_digest_is_checked(tmp_path):
    registry_path = tmp_path / "registry.sqlite3"
    registry = CapabilityRegistry(registry_path)
    registry.register(MANIFEST)
    import sqlite3

    with sqlite3.connect(registry_path) as connection:
        connection.execute(
            "UPDATE capabilities SET manifest_json = ? WHERE capability_id = ?",
            ('{"id":"tampered"}', "example.registry"),
        )
    with pytest.raises(RegistryError, match="integrity"):
        registry.get("example.registry")
