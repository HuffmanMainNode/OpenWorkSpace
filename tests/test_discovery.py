import json
import shutil
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = (
    "specifications/first-party-catalog.schema.json",
    "specifications/resource-packs.schema.json",
    "specifications/source-qualification.schema.json",
    "catalog/first-party/repositories.json",
    "catalog/packs/first-party-packs.json",
    "catalog/first-party/source-qualification.json",
)


def _validate(root):
    from openworkspace.discovery import validate_local_catalog

    return validate_local_catalog(root)


def _copy_catalog(tmp_path: Path) -> Path:
    for relative in DOCUMENTS:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE_ROOT / relative, target)
    return tmp_path


def _read(root: Path, relative: str) -> dict:
    path = root / relative
    return json.loads(path.read_text(encoding="utf-8"))


def _write(root: Path, relative: str, document: dict) -> None:
    (root / relative).write_text(
        json.dumps(document, indent=2) + "\n", encoding="utf-8"
    )


def _assert_invalid(root: Path, expected_message: str) -> None:
    from openworkspace.discovery import CatalogValidationError

    try:
        _validate(root)
    except CatalogValidationError as exc:
        assert expected_message in str(exc)
    else:
        raise AssertionError(f"expected catalog validation error containing {expected_message!r}")


def test_local_catalog_validates_and_reports_offline_scope():
    result = _validate(SOURCE_ROOT)
    assert result == {
        "valid": True,
        "repositories": 62,
        "resource_packs": 6,
        "qualification_records": 9,
        "network_accessed": False,
        "source_code_executed": False,
    }


def test_rejects_duplicate_resource_pack_ids(tmp_path):
    root = _copy_catalog(tmp_path)
    path = "catalog/packs/first-party-packs.json"
    packs = _read(root, path)
    packs["packs"].append(dict(packs["packs"][0]))
    _write(root, path, packs)

    _assert_invalid(root, "duplicate pack IDs")


def test_rejects_duplicate_project_reference_within_pack(tmp_path):
    root = _copy_catalog(tmp_path)
    path = "catalog/packs/first-party-packs.json"
    packs = _read(root, path)
    first_pack = packs["packs"][0]
    first_pack["items"].append(dict(first_pack["items"][0]))
    _write(root, path, packs)

    _assert_invalid(root, "duplicate project references")


def test_rejects_license_flag_that_disagrees_with_reviewed_files(tmp_path):
    root = _copy_catalog(tmp_path)
    path = "catalog/first-party/source-qualification.json"
    qualification = _read(root, path)
    record = next(
        item for item in qualification["records"]
        if item["license_file"]["inspected"] is False
    )
    record["license_file"]["inspected"] = True
    _write(root, path, qualification)

    _assert_invalid(root, "license inspection flag")


def test_rejects_license_path_traversal(tmp_path):
    root = _copy_catalog(tmp_path)
    path = "catalog/first-party/source-qualification.json"
    qualification = _read(root, path)
    qualification["records"][0]["license_file"]["path"] = "../LICENSE"
    _write(root, path, qualification)

    _assert_invalid(root, "safe repository-relative path")


def test_rejects_inspected_license_missing_from_reviewed_file_list(tmp_path):
    root = _copy_catalog(tmp_path)
    path = "catalog/first-party/source-qualification.json"
    qualification = _read(root, path)
    record = next(
        item for item in qualification["records"]
        if item["license_file"]["inspected"] is True
    )
    record["files_reviewed"].remove(record["license_file"]["path"])
    _write(root, path, qualification)

    _assert_invalid(root, "license inspection flag")
