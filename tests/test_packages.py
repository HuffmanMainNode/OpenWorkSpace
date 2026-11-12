import hashlib
import sqlite3

import pytest

from openworkspace.packages import (
    DuplicatePackageError,
    PackageCatalog,
    PackageIntakeError,
)


def make_manifest(artifact):
    digest = hashlib.sha256(artifact).hexdigest()
    return {
        "id": "example.external.tool",
        "publisher": "Example Publisher",
        "version": "1.0.0",
        "source": "https://example.invalid/tool",
        "digest": f"sha256:{digest}",
        "license": "Apache-2.0",
        "dependencies": [],
        "permissions": [],
        "supported_environments": ["python>=3.11"],
        "signature_reference": None,
    }


def test_package_manifest_validation_and_artifact_registration(tmp_path):
    artifact = b"synthetic archive bytes; never unpacked or executed"
    artifact_path = tmp_path / "tool.bin"
    artifact_path.write_bytes(artifact)
    catalog = PackageCatalog(tmp_path / "runtime.sqlite3")
    manifest = make_manifest(artifact)
    registered = catalog.register(manifest, artifact_path)
    assert registered["manifest"] == manifest
    assert registered["artifact_sha256"] == manifest["digest"]
    assert registered["execution_enabled"] is False
    assert len(catalog.list()) == 1
    assert catalog.audit_events()[0]["event_type"] == (
        "package.artifact_verified_and_registered"
    )


def test_package_rejects_invalid_manifest_and_digest_mismatch(tmp_path):
    catalog = PackageCatalog(tmp_path / "runtime.sqlite3")
    artifact_path = tmp_path / "tool.bin"
    artifact_path.write_bytes(b"actual bytes")
    with pytest.raises(PackageIntakeError, match="invalid package"):
        catalog.validate({"id": "missing"})
    manifest = make_manifest(b"different bytes")
    with pytest.raises(PackageIntakeError, match="digest mismatch"):
        catalog.register(manifest, artifact_path)


def test_package_duplicate_version_is_rejected_but_new_version_is_allowed(tmp_path):
    artifact = b"package version content"
    path = tmp_path / "tool.bin"
    path.write_bytes(artifact)
    catalog = PackageCatalog(tmp_path / "runtime.sqlite3")
    manifest = make_manifest(artifact)
    catalog.register(manifest, path)
    with pytest.raises(DuplicatePackageError):
        catalog.register(manifest, path)
    newer = {**manifest, "version": "1.1.0"}
    catalog.register(newer, path)
    assert [row["version"] for row in catalog.list()] == ["1.0.0", "1.1.0"]


def test_package_metadata_tampering_is_detected(tmp_path):
    artifact = b"verified"
    path = tmp_path / "tool.bin"
    path.write_bytes(artifact)
    database = tmp_path / "runtime.sqlite3"
    catalog = PackageCatalog(database)
    catalog.register(make_manifest(artifact), path)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE packages SET manifest_json=? WHERE package_id=?",
            ('{"id":"tampered"}', "example.external.tool"),
        )
    with pytest.raises(PackageIntakeError, match="integrity"):
        catalog.get("example.external.tool", "1.0.0")


def test_package_audit_rejects_ordinary_mutation(tmp_path):
    artifact = b"verified"
    path = tmp_path / "tool.bin"
    path.write_bytes(artifact)
    database = tmp_path / "runtime.sqlite3"
    catalog = PackageCatalog(database)
    catalog.register(make_manifest(artifact), path)
    with sqlite3.connect(database) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM package_audit")
