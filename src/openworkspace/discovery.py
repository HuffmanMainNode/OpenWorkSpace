"""Offline validation for OpenWorkSpace's repository-local discovery catalogs."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, SchemaError, ValidationError


class CatalogValidationError(ValueError):
    """Raised when local discovery or qualification data is invalid."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CatalogValidationError(f"cannot read valid UTF-8 JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CatalogValidationError(f"expected a JSON object in {path}")
    return value


def _validate_document(root: Path, schema_path: str, document_path: str) -> dict[str, Any]:
    schema = _load_json(root / schema_path)
    document = _load_json(root / document_path)
    try:
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(document)
    except (SchemaError, ValidationError) as exc:
        raise CatalogValidationError(
            f"{document_path} does not satisfy {schema_path}: {exc.message}"
        ) from exc
    return document


def _is_safe_relative_path(value: str) -> bool:
    """Reject absolute, traversing, drive-qualified, and control-character paths."""
    path = PurePosixPath(value)
    return (
        bool(value)
        and "\\" not in value
        and ":" not in value
        and not any(ord(character) < 32 for character in value)
        and not path.is_absolute()
        and all(part not in {".", ".."} for part in path.parts)
        and bool(path.parts)
    )


def validate_local_catalog(root: str | Path = ".") -> dict[str, Any]:
    """Validate catalog, packs, and qualification records without network or execution."""

    repository = Path(root).expanduser()
    catalog = _validate_document(
        repository,
        "specifications/first-party-catalog.schema.json",
        "catalog/first-party/repositories.json",
    )
    packs = _validate_document(
        repository,
        "specifications/resource-packs.schema.json",
        "catalog/packs/first-party-packs.json",
    )
    qualification = _validate_document(
        repository,
        "specifications/source-qualification.schema.json",
        "catalog/first-party/source-qualification.json",
    )

    entries = catalog["repositories"]
    by_id = {entry["id"]: entry for entry in entries}
    if len(by_id) != len(entries):
        raise CatalogValidationError("first-party catalog contains duplicate project IDs")
    urls = [entry["repository_url"] for entry in entries]
    if len(set(urls)) != len(urls):
        raise CatalogValidationError("first-party catalog contains duplicate repository URLs")

    for owner in ("PCakes303", "HuffmanRepositories", "HuffmanMainNode"):
        actual = sum(entry["publisher"] == owner for entry in entries)
        if catalog["counts"][owner] != actual:
            raise CatalogValidationError(f"catalog count mismatch for {owner}")
    if catalog["counts"]["total"] != len(entries):
        raise CatalogValidationError("first-party catalog total does not match its entries")

    pack_ids = [pack["id"] for pack in packs["packs"]]
    if len(set(pack_ids)) != len(pack_ids):
        raise CatalogValidationError("resource packs contain duplicate pack IDs")

    for pack in packs["packs"]:
        item_ids = [item["project_id"] for item in pack["items"]]
        if len(set(item_ids)) != len(item_ids):
            raise CatalogValidationError(
                f"resource pack {pack['id']} contains duplicate project references"
            )
        for project_id in item_ids:
            if project_id not in by_id:
                raise CatalogValidationError(
                    f"resource pack {pack['id']} references unknown project {project_id}"
                )
            entry = by_id[project_id]
            if entry["visibility"] != "public" or entry["fork"]:
                raise CatalogValidationError(
                    f"resource pack {pack['id']} references an ineligible project"
                )

    reviewed: set[str] = set()
    for record in qualification["records"]:
        project_id = record["project_id"]
        if project_id in reviewed:
            raise CatalogValidationError(
                f"duplicate source qualification record for {project_id}"
            )
        reviewed.add(project_id)
        entry = by_id.get(project_id)
        if entry is None:
            raise CatalogValidationError(
                f"source qualification references unknown project {project_id}"
            )
        if entry["source_revision"] != record["source_revision"]:
            raise CatalogValidationError(
                f"source revision mismatch for qualified project {project_id}"
            )
        if entry["review_state"] != record["review_state"]:
            raise CatalogValidationError(
                f"review state mismatch for qualified project {project_id}"
            )

        license_path = record["license_file"]["path"]
        if not _is_safe_relative_path(license_path):
            raise CatalogValidationError(
                f"license file path must be a safe repository-relative path for {project_id}"
            )
        for reviewed_path in record["files_reviewed"]:
            if not _is_safe_relative_path(reviewed_path):
                raise CatalogValidationError(
                    f"reviewed file path must be safe and repository-relative for {project_id}"
                )
        license_was_reviewed = license_path in record["files_reviewed"]
        if record["license_file"]["inspected"] != license_was_reviewed:
            raise CatalogValidationError(
                f"license inspection flag and files_reviewed disagree for {project_id}"
            )
        if record["decision"] != "reference-only":
            raise CatalogValidationError(
                f"unsupported integration decision for project {project_id}"
            )

    return {
        "valid": True,
        "repositories": len(entries),
        "resource_packs": len(packs["packs"]),
        "qualification_records": len(qualification["records"]),
        "network_accessed": False,
        "source_code_executed": False,
    }
