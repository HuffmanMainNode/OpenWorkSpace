import json
from pathlib import Path

from jsonschema import Draft202012Validator

from openworkspace.contracts import validate_capability_file

ROOT = Path(__file__).resolve().parents[1]


def test_all_published_schemas_are_valid_json_schema():
    schema_files = sorted((ROOT / "specifications").glob("*.schema.json"))
    assert len(schema_files) >= 8
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
