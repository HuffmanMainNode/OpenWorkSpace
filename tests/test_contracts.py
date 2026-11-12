import pytest

from openworkspace.contracts import ContractError, validate_capability

VALID = {
    "id": "example.echo", "version": "0.1.0", "interface_version": "1",
    "description": "A harmless example capability.", "inputs": {}, "outputs": {}, "permissions": [],
}


def test_valid_manifest_is_accepted():
    validate_capability(VALID)


def test_missing_required_field_is_rejected():
    manifest = {key: value for key, value in VALID.items() if key != "permissions"}
    with pytest.raises(ContractError):
        validate_capability(manifest)


def test_unknown_permission_is_rejected():
    manifest = {**VALID, "permissions": ["filesystem.root_access"]}
    with pytest.raises(ContractError):
        validate_capability(manifest)


def test_unknown_property_is_rejected():
    manifest = {**VALID, "execute": "true"}
    with pytest.raises(ContractError):
        validate_capability(manifest)


def test_invalid_version_is_rejected():
    manifest = {**VALID, "version": "latest"}
    with pytest.raises(ContractError):
        validate_capability(manifest)
