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
