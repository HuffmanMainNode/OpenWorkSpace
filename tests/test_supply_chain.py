import pathlib
import tomllib


ROOT = pathlib.Path(__file__).resolve().parents[1]


def _assert_actions_are_pinned(workflow):
    for action in ("actions/checkout@", "actions/setup-python@"):
        lines = [line for line in workflow.splitlines() if f"uses: {action}" in line]
        assert lines, f"missing {action} action reference"
        for line in lines:
            reference = line.split("@", 1)[1].split()[0]
            assert len(reference) == 40
            assert all(character in "0123456789abcdef" for character in reference)
            assert "# v" in line


def test_supply_chain_controls_are_declared():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    runtime = project["project"]["dependencies"]
    development = project["project"]["optional-dependencies"]["dev"]

    assert "cryptography>=50.0.0,<51" in runtime
    assert "pytest>=9.0.3,<10" in development

    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "permissions:\n  contents: read" in ci
    assert "pip-audit --strict -r runtime-requirements.txt" in ci
    assert "runtime-audit:" in ci
    audit_job = ci.split("  runtime-audit:", 1)[1]
    assert "pip install ." not in audit_job
    _assert_actions_are_pinned(ci)

    weekly = (ROOT / ".github/workflows/weekly-dependencies.yml").read_text(
        encoding="utf-8"
    )
    assert "schedule:" in weekly
    assert "pytest" in weekly
    assert "ruff check ." in weekly
    assert "python -m pip wheel --no-deps ." in weekly
    assert "permissions:\n  contents: read" in weekly
    _assert_actions_are_pinned(weekly)

    dependabot = (ROOT / ".github/dependabot.yml").read_text(encoding="utf-8")
    assert 'package-ecosystem: "pip"' in dependabot
    assert 'package-ecosystem: "github-actions"' in dependabot
