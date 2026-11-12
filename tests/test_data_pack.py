import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "specifications"
FIXTURE_DIR = ROOT / "examples" / "contracts"


def test_all_contract_fixtures_validate_against_their_schemas():
    pairs = {
        "identity.json": "identity.schema.json",
        "task.json": "task.schema.json",
        "message.json": "message.schema.json",
        "permission.json": "permission.schema.json",
        "resource.json": "resource.schema.json",
        "plugin-manifest.json": "plugin-manifest.schema.json",
        "registry-record.json": "registry.schema.json",
        "evidence-event.json": "evidence.schema.json",
    }
    for fixture_name, schema_name in pairs.items():
        fixture = json.loads((FIXTURE_DIR / fixture_name).read_text(encoding="utf-8"))
        schema = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(fixture)


def test_permission_catalog_matches_capability_manifest_enum():
    catalog = json.loads(
        (ROOT / "data" / "catalogs" / "permissions.json").read_text(encoding="utf-8")
    )
    schema = json.loads(
        (SCHEMA_DIR / "capability.schema.json").read_text(encoding="utf-8")
    )
    catalog_ids = {entry["id"] for entry in catalog["permissions"]}
    schema_ids = set(schema["properties"]["permissions"]["items"]["enum"])
    assert catalog["default_decision"] == "deny"
    assert catalog_ids == schema_ids


def test_data_catalogs_are_valid_json_and_have_schema_version():
    catalog_paths = sorted((ROOT / "data" / "catalogs").glob("*.json"))
    assert len(catalog_paths) >= 6
    for path in catalog_paths:
        catalog = json.loads(path.read_text(encoding="utf-8"))
        assert catalog["schema_version"] == "1.0"


def test_local_markdown_links_resolve():
    import re

    for markdown in ROOT.rglob("*.md"):
        source = markdown.read_text(encoding="utf-8")
        for target in re.findall(r"\\[[^]]+\\]\\(([^)]+)\\)", source):
            if target.startswith(("https://", "http://", "mailto:", "#")):
                continue
            relative_path = target.split("#", 1)[0]
            if relative_path:
                assert (markdown.parent / relative_path).exists(), (
                    f"Broken local link in {markdown.relative_to(ROOT)}: {target}"
                )
