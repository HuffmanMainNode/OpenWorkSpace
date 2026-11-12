import json

from openworkspace.cli import main


def test_cli_validates_manifest(tmp_path, capsys):
    manifest = {
        "id": "example.echo", "version": "0.1.0", "interface_version": "1",
        "description": "Example", "inputs": {}, "outputs": {}, "permissions": []
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    assert main(["validate-manifest", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True


def test_cli_reports_invalid_manifest(tmp_path, capsys):
    path = tmp_path / "manifest.json"
    path.write_text("{}")
    assert main(["validate-manifest", str(path)]) == 2
    assert "error:" in capsys.readouterr().err


def test_cli_register_list_show_and_remove(tmp_path, capsys):
    manifest = {
        "id": "example.cli", "version": "0.1.0", "interface_version": "1",
        "description": "CLI fixture", "inputs": {}, "outputs": {}, "permissions": []
    }
    source = tmp_path / "manifest.json"
    database = tmp_path / "registry.sqlite3"
    source.write_text(json.dumps(manifest))
    db_args = ["--database", str(database)]

    assert main(["register", str(source), *db_args]) == 0
    assert json.loads(capsys.readouterr().out)["registered"] is True
    assert main(["list", *db_args]) == 0
    assert len(json.loads(capsys.readouterr().out)["capabilities"]) == 1
    assert main(["show", "example.cli", *db_args]) == 0
    assert json.loads(capsys.readouterr().out)["id"] == "example.cli"
    assert main(["remove", "example.cli", *db_args]) == 0
    assert json.loads(capsys.readouterr().out)["removed"] is True


def test_cli_permission_evaluation_returns_nonzero_on_denial(tmp_path, capsys):
    manifest = {
        "id": "example.deny", "version": "0.1.0", "interface_version": "1",
        "description": "Permission fixture", "inputs": {}, "outputs": {},
        "permissions": ["network.connect"]
    }
    source = tmp_path / "manifest.json"
    database = tmp_path / "registry.sqlite3"
    source.write_text(json.dumps(manifest))
    db_args = ["--database", str(database)]
    assert main(["register", str(source), *db_args]) == 0
    capsys.readouterr()
    assert main(["evaluate", "example.deny", *db_args]) == 3
    output = json.loads(capsys.readouterr().out)
    assert output["executed"] is False
    assert output["decisions"][0]["allowed"] is False


def test_cli_missing_evidence_file_fails(tmp_path, capsys):
    assert main(["verify-evidence", str(tmp_path / "missing.jsonl")]) == 2
    assert "does not exist" in capsys.readouterr().err


def test_cli_identity_and_task_lifecycle(tmp_path, capsys):
    identity = {
        "id": "cli.example.user", "kind": "user", "issuer": "local",
        "key_reference": None, "status": "active", "valid_from": None,
        "valid_until": None, "attributes": {}
    }
    task = {
        "id": "cli.example.task", "owner": "cli.example.user", "state": "pending",
        "inputs": {}, "dependencies": [], "deadline": None,
        "retry_policy": {"max_attempts": 1, "backoff_seconds": 0},
        "idempotency_key": None
    }
    identity_path = tmp_path / "identity.json"
    task_path = tmp_path / "task.json"
    database = tmp_path / "runtime.sqlite3"
    identity_path.write_text(json.dumps(identity))
    task_path.write_text(json.dumps(task))
    db = ["--database", str(database)]

    assert main(["identity-create", str(identity_path), *db]) == 0
    assert json.loads(capsys.readouterr().out)["created"] is True
    assert main(["identity-show", "cli.example.user", *db]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "active"
    status_args = [
        "identity-status", "cli.example.user", "suspended", "--reason", "CLI test", *db
    ]
    assert main(status_args) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "suspended"
    assert main([
        "identity-status", "cli.example.user", "active", "--reason", "Restore for task test", *db
    ]) == 0
    capsys.readouterr()

    assert main(["task-create", str(task_path), *db]) == 0
    assert json.loads(capsys.readouterr().out)["created"] is True
    assert main(["task-refresh-ready", *db]) == 0
    assert json.loads(capsys.readouterr().out)["promoted"] == ["cli.example.task"]
    assert main(["task-list", *db]) == 0
    assert json.loads(capsys.readouterr().out)["tasks"][0]["state"] == "ready"
    assert main(["task-show", "cli.example.task", *db]) == 0
    assert json.loads(capsys.readouterr().out)["state"] == "ready"


def test_cli_local_message_queue(tmp_path, capsys):
    from openworkspace.identity import IdentityRegistry

    database = tmp_path / "runtime.sqlite3"
    identities = IdentityRegistry(database)
    for identity_id, kind in (("cli.sender", "user"), ("cli.recipient", "service")):
        identities.create({
            "id": identity_id, "kind": kind, "issuer": "local",
            "key_reference": None, "status": "active", "valid_from": None,
            "valid_until": None, "attributes": {}
        })
    envelope = {
        "message_id": "cli.message", "sender": "cli.sender",
        "recipient": "cli.recipient", "message_type": "test.cli",
        "schema_version": "1.0", "timestamp": "2026-11-12T12:00:00Z",
        "correlation_id": None, "payload": {"test": True}
    }
    source = tmp_path / "message.json"
    source.write_text(json.dumps(envelope))
    db = ["--database", str(database)]

    assert main(["message-send", str(source), *db]) == 0
    assert json.loads(capsys.readouterr().out)["queued"] is True
    assert main(["message-inbox", "cli.recipient", *db]) == 0
    assert len(json.loads(capsys.readouterr().out)["messages"]) == 1
    assert main(["message-ack", "cli.message", "cli.recipient", *db]) == 0
    assert json.loads(capsys.readouterr().out)["acknowledged"] is True
    assert main(["message-inbox", "cli.recipient", *db]) == 0
    assert json.loads(capsys.readouterr().out)["messages"] == []


def test_cli_identity_keygen_sign_and_verify(tmp_path, capsys, monkeypatch):
    identity = {
        "id": "cli.key-owner", "kind": "user", "issuer": "local",
        "key_reference": None, "status": "active", "valid_from": None,
        "valid_until": None, "attributes": {}
    }
    identity_path = tmp_path / "identity.json"
    payload_path = tmp_path / "payload.bin"
    database = tmp_path / "runtime.sqlite3"
    key_directory = tmp_path / "keys"
    identity_path.write_text(json.dumps(identity))
    payload_path.write_bytes(b"OpenWorkSpace CLI signature test")
    db = ["--database", str(database)]
    keys = ["--key-directory", str(key_directory)]

    assert main(["identity-create", str(identity_path), *db]) == 0
    capsys.readouterr()
    prompts = iter(["cli passphrase for tests", "cli passphrase for tests"])
    monkeypatch.setattr("openworkspace.cli.getpass.getpass", lambda _: next(prompts))
    assert main(["identity-keygen", "cli.key-owner", *keys, *db]) == 0
    assert json.loads(capsys.readouterr().out)["key_generated"] is True

    monkeypatch.setattr(
        "openworkspace.cli.getpass.getpass", lambda _: "cli passphrase for tests"
    )
    assert main(["identity-sign", "cli.key-owner", str(payload_path), *keys, *db]) == 0
    signature = json.loads(capsys.readouterr().out)["signature"]
    assert main([
        "identity-verify", "cli.key-owner", str(payload_path), signature, *db
    ]) == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True


def test_cli_resource_catalog_lifecycle(tmp_path, capsys):
    resource = {
        "id": "cli.resource", "name": "CLI Reference", "resource_type": "reference",
        "source": "https://example.invalid/cli", "version": "1.0",
        "license_status": "reference-only", "license_expression": None,
        "trust_state": "uninspected", "permissions": [], "maintainer": None,
        "notes": "CLI fixture"
    }
    source = tmp_path / "resource.json"
    database = tmp_path / "runtime.sqlite3"
    source.write_text(json.dumps(resource))
    db = ["--database", str(database)]
    assert main(["resource-register", str(source), *db]) == 0
    assert json.loads(capsys.readouterr().out)["registered"] is True
    assert main(["resource-list", "--search", "reference", *db]) == 0
    assert len(json.loads(capsys.readouterr().out)["resources"]) == 1
    assert main(["resource-trust", "cli.resource", "inspected", "--reason", "CLI review", *db]) == 0
    assert json.loads(capsys.readouterr().out)["trust_state"] == "inspected"
    assert main(["resource-show", "cli.resource", *db]) == 0
    assert json.loads(capsys.readouterr().out)["trust_state"] == "inspected"


def test_cli_package_validate_verify_register_and_show(tmp_path, capsys):
    import hashlib

    artifact = b"synthetic cli package bytes"
    artifact_path = tmp_path / "package.bin"
    artifact_path.write_bytes(artifact)
    manifest = {
        "id": "cli.package", "publisher": "Example", "version": "1.0.0",
        "source": "https://example.invalid/package",
        "digest": "sha256:" + hashlib.sha256(artifact).hexdigest(),
        "license": "Apache-2.0", "dependencies": [], "permissions": [],
        "supported_environments": ["python>=3.11"], "signature_reference": None
    }
    manifest_path = tmp_path / "package.json"
    manifest_path.write_text(json.dumps(manifest))
    database = tmp_path / "runtime.sqlite3"
    db = ["--database", str(database)]

    assert main(["package-validate", str(manifest_path), *db]) == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True
    assert main(["package-verify", str(manifest_path), str(artifact_path), *db]) == 0
    assert json.loads(capsys.readouterr().out)["verified"] is True
    assert main(["package-register", str(manifest_path), str(artifact_path), *db]) == 0
    assert json.loads(capsys.readouterr().out)["execution_enabled"] is False
    assert main(["package-list", *db]) == 0
    assert len(json.loads(capsys.readouterr().out)["packages"]) == 1
    assert main(["package-show", "cli.package", "1.0.0", *db]) == 0
    assert json.loads(capsys.readouterr().out)["manifest"]["id"] == "cli.package"
