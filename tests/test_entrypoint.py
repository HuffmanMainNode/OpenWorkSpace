import json

from openworkspace.entrypoint import initialize_workspace, main, run_demo


def test_initialize_workspace_creates_stores_and_is_idempotent(tmp_path):
    root = tmp_path / ".openworkspace"
    first = initialize_workspace(root)
    evidence = root / "evidence.jsonl"
    second = initialize_workspace(root)

    assert first == second
    assert (root / "runtime.sqlite3").is_file()
    assert (root / "registry.sqlite3").is_file()
    assert not evidence.exists()


def test_demo_is_non_executing_and_shows_allow_and_deny():
    result = run_demo()
    decisions = {item["permission"]: item["allowed"] for item in result["decisions"]}

    assert decisions == {"filesystem.read": True, "network.connect": False}
    assert result["executed"] is False
    assert result["os_access_enforced"] is False
    assert result["workspace_persisted"] is False


def test_init_and_demo_commands_emit_json(tmp_path, capsys):
    assert main(["init", "--path", str(tmp_path / "workspace")]) == 0
    initialized = json.loads(capsys.readouterr().out)
    assert initialized["initialized"] is True

    assert main(["demo"]) == 0
    demo = json.loads(capsys.readouterr().out)
    assert demo["executed"] is False


def test_main_help_lists_init_and_demo(capsys):
    assert main(["--help"]) == 0
    output = capsys.readouterr().out
    assert "init" in output
    assert "demo" in output
    assert "validate-manifest" in output
