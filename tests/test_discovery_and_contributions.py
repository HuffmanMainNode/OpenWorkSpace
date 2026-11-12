import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_workspace_discovery_descriptor_matches_schema():
    schema = _json(ROOT / "specifications" / "workspace-discovery.schema.json")
    descriptor = _json(ROOT / "openworkspace.json")
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(descriptor)


def test_contribution_template_matches_schema():
    schema = _json(ROOT / "specifications" / "contribution.schema.json")
    template = _json(ROOT / "contributions" / "templates" / "contribution.json")
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(template)


def test_contribution_schema_is_valid_json_schema():
    schema = _json(ROOT / "specifications" / "contribution.schema.json")
    Draft202012Validator.check_schema(schema)


def test_workspace_discovery_schema_is_valid_json_schema():
    schema = _json(ROOT / "specifications" / "workspace-discovery.schema.json")
    Draft202012Validator.check_schema(schema)


def test_discovery_references_resolve_to_repository_files():
    descriptor = _json(ROOT / "openworkspace.json")
    for relative_path in descriptor["discovery"].values():
        assert (ROOT / relative_path).is_file(), relative_path


def test_machine_readable_entrypoints_exist():
    for relative_path in ("AGENTS.md", "llms.txt", "openworkspace.json"):
        assert (ROOT / relative_path).is_file()


def test_contribution_intake_is_metadata_only_and_empty_of_payloads():
    inbox = ROOT / "contributions" / "inbox"
    forbidden_suffixes = {".exe", ".dll", ".so", ".dylib", ".whl", ".zip", ".tar", ".gz"}
    for path in inbox.rglob("*"):
        if path.is_file():
            assert path.suffix.lower() not in forbidden_suffixes
            assert path.name not in {"pyproject.toml", "setup.py", "package.json"}
