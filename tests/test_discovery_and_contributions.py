import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _contribution_validator():
    schema = _json(ROOT / "specifications" / "contribution.schema.json")
    return Draft202012Validator(schema, format_checker=FormatChecker())


def test_workspace_discovery_descriptor_matches_schema():
    schema = _json(ROOT / "specifications" / "workspace-discovery.schema.json")
    descriptor = _json(ROOT / "openworkspace.json")
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(descriptor)


def test_contribution_template_matches_schema():
    template = _json(ROOT / "contributions" / "templates" / "contribution.json")
    _contribution_validator().validate(template)


def test_contribution_schema_is_valid_json_schema():
    Draft202012Validator.check_schema(
        _json(ROOT / "specifications" / "contribution.schema.json")
    )


def test_workspace_discovery_schema_is_valid_json_schema():
    Draft202012Validator.check_schema(
        _json(ROOT / "specifications" / "workspace-discovery.schema.json")
    )


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


def test_contribution_rejects_unrecognized_fields():
    manifest = _json(ROOT / "contributions" / "templates" / "contribution.json")
    manifest["unexpected_execution_hook"] = "run-me"
    assert list(_contribution_validator().iter_errors(manifest))


def test_archive_distribution_requires_license_and_maintainer_approval():
    manifest = _json(ROOT / "contributions" / "templates" / "contribution.json")
    manifest["distribution"] = {
        "mode": "approved-archive",
        "source_included": True,
        "archive_allowed": True,
    }
    manifest["review"]["status"] = "approved-archive"
    assert list(_contribution_validator().iter_errors(manifest))


def test_unqualified_execution_cannot_claim_isolated_qualification():
    manifest = _json(ROOT / "contributions" / "templates" / "contribution.json")
    manifest["execution"] = "isolated-qualified"
    assert list(_contribution_validator().iter_errors(manifest))


def test_network_destinations_require_declared_network_access():
    manifest = _json(ROOT / "contributions" / "templates" / "contribution.json")
    manifest["network"] = {"required": False, "destinations": ["https://example.org"]}
    assert list(_contribution_validator().iter_errors(manifest))


def test_reference_only_template_does_not_claim_execution_or_redistribution():
    manifest = _json(ROOT / "contributions" / "templates" / "contribution.json")
    _contribution_validator().validate(manifest)
    assert manifest["execution"] == "none"
    assert manifest["distribution"]["mode"] == "reference-only"
    assert manifest["distribution"]["source_included"] is False
    assert manifest["distribution"]["archive_allowed"] is False
