import json
from pathlib import Path

from jsonschema import Draft202012Validator

from openworkspace.contracts import validate_capability_file

ROOT = Path(__file__).resolve().parents[1]


def test_all_published_schemas_are_valid_json_schema():
    schema_files = sorted((ROOT / "specifications").glob("*.schema.json"))
    assert len(schema_files) >= 9
    for path in schema_files:
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)


def test_example_manifest_passes_runtime_validator():
    manifest = validate_capability_file(ROOT / "examples" / "hello-capability.json")
    assert manifest["id"] == "example.hello"


def test_bundled_capability_schema_matches_published_contract():
    published = json.loads((ROOT / "specifications" / "capability.schema.json").read_text())
    bundled = json.loads((ROOT / "src" / "openworkspace" / "capability.schema.json").read_text())
    assert bundled == published


def test_evidence_schema_matches_bundled_runtime_schema():
    published = json.loads((ROOT / "specifications" / "evidence.schema.json").read_text())
    bundled = json.loads((ROOT / "src" / "openworkspace" / "evidence.schema.json").read_text())
    assert bundled == published


def test_identity_task_and_message_schemas_match_bundled_runtime_resources():
    for name in ("identity", "task", "message"):
        published = json.loads(
            (ROOT / "specifications" / f"{name}.schema.json").read_text(encoding="utf-8")
        )
        bundled = json.loads(
            (ROOT / "src" / "openworkspace" / f"{name}.schema.json").read_text(
                encoding="utf-8"
            )
        )
        assert bundled == published


def test_registry_schema_matches_bundled_runtime_schema():
    published = json.loads((ROOT / "specifications" / "registry.schema.json").read_text())
    bundled = json.loads((ROOT / "src" / "openworkspace" / "registry.schema.json").read_text())
    assert bundled == published
