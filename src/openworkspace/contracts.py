"""Validation for versioned OpenWorkSpace capability manifests."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class ContractError(ValueError):
    """Raised when an input does not satisfy its published contract."""


def load_capability_schema() -> dict[str, Any]:
    schema_path = files("openworkspace").joinpath("capability.schema.json")
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_capability(data: Any) -> None:
    """Validate a capability manifest; raise ContractError on the first error."""
    validator = Draft202012Validator(load_capability_schema())
    errors = sorted(validator.iter_errors(data), key=lambda error: list(map(str, error.path)))
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.path) or "$"
        raise ContractError(f"{location}: {error.message}")


def validate_capability_file(path: str | Path) -> dict[str, Any]:
    """Read and validate a UTF-8 JSON capability manifest."""
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read valid UTF-8 JSON from {source}: {exc}") from exc
    validate_capability(data)
    return data
