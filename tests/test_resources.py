import sqlite3

import pytest

from openworkspace.resources import (
    DuplicateResourceError,
    ResourceCatalog,
    ResourceCatalogError,
)

RESOURCE = {
    "id": "resource.example.guide",
    "name": "Example Technical Guide",
    "resource_type": "reference",
    "source": "https://example.invalid/guide",
    "version": "1.0",
    "license_status": "reference-only",
    "license_expression": None,
    "trust_state": "uninspected",
    "permissions": [],
    "maintainer": "Example",
    "notes": "Synthetic test fixture only.",
}


def test_resource_register_get_and_search(tmp_path):
    catalog = ResourceCatalog(tmp_path / "runtime.sqlite3")
    assert catalog.register(RESOURCE) == RESOURCE
    assert catalog.get(RESOURCE["id"]) == RESOURCE
    assert catalog.list(search="technical") == [
        {
            "id": RESOURCE["id"],
            "name": RESOURCE["name"],
            "resource_type": "reference",
            "license_status": "reference-only",
            "trust_state": "uninspected",
        }
    ]
    assert catalog.list(resource_type="reference") != []


def test_resource_rejects_duplicate_and_non_initial_trust(tmp_path):
    catalog = ResourceCatalog(tmp_path / "runtime.sqlite3")
    catalog.register(RESOURCE)
    with pytest.raises(DuplicateResourceError):
        catalog.register(RESOURCE)
    with pytest.raises(ResourceCatalogError, match="uninspected"):
        catalog.register({**RESOURCE, "id": "resource.other", "trust_state": "qualified"})


def test_resource_trust_transitions_are_explicit_and_audited(tmp_path):
    catalog = ResourceCatalog(tmp_path / "runtime.sqlite3")
    catalog.register(RESOURCE)
    inspected = catalog.update_trust_state(
        RESOURCE["id"], "inspected", reason="Metadata reviewed"
    )
    assert inspected["trust_state"] == "inspected"
    qualified = catalog.update_trust_state(
        RESOURCE["id"], "qualified", reason="Qualification checks passed"
    )
    assert qualified["trust_state"] == "qualified"
    assert [event["event_type"] for event in catalog.audit_events()] == [
        "resource.registered", "resource.trust_changed", "resource.trust_changed"
    ]


def test_resource_trust_cannot_skip_inspection_or_reverse_revocation(tmp_path):
    catalog = ResourceCatalog(tmp_path / "runtime.sqlite3")
    catalog.register(RESOURCE)
    with pytest.raises(ResourceCatalogError, match="not allowed"):
        catalog.update_trust_state(
            RESOURCE["id"], "authorized", reason="Skip required stages"
        )
    catalog.update_trust_state(RESOURCE["id"], "revoked", reason="Stop use")
    with pytest.raises(ResourceCatalogError, match="not allowed"):
        catalog.update_trust_state(
            RESOURCE["id"], "inspected", reason="Cannot restore revoked item"
        )


def test_resource_rejects_empty_reason_and_detects_tampering(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    catalog = ResourceCatalog(path)
    catalog.register(RESOURCE)
    with pytest.raises(ResourceCatalogError, match="reason"):
        catalog.update_trust_state(RESOURCE["id"], "inspected", reason=" ")
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE resources SET resource_json=? WHERE resource_id=?",
            ('{"id":"changed"}', RESOURCE["id"]),
        )
    with pytest.raises(ResourceCatalogError, match="integrity"):
        catalog.get(RESOURCE["id"])


def test_resource_audit_rejects_ordinary_mutation(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    catalog = ResourceCatalog(path)
    catalog.register(RESOURCE)
    with sqlite3.connect(path) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM resource_audit")
