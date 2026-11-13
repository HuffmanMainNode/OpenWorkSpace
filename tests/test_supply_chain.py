from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_supply_chain_controls_are_declared():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    runtime = project["project"]["dependencies"]
    development = project["project"]["optional-dependencies"]["dev"]

    assert "cryptography>=50.0.0,<51" in runtime
    assert "pytest>=9.0.3,<10" in development

    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "permissions:\n  contents: read" in ci
    assert "pip-audit --path" in ci
    assert "runtime-audit:" in ci

    weekly = (ROOT / ".github/workflows/weekly-dependencies.yml").read_text(
        encoding="utf-8"
    )
    assert "schedule:" in weekly
    assert "pytest" in weekly
    assert "ruff check ." in weekly
    assert "python -m pip wheel --no-deps ." in weekly
    assert "permissions:\n  contents: read" in weekly

    dependabot = (ROOT / ".github/dependabot.yml").read_text(encoding="utf-8")
    assert 'package-ecosystem: "pip"' in dependabot
    assert 'package-ecosystem: "github-actions"' in dependabot
