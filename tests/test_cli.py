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
