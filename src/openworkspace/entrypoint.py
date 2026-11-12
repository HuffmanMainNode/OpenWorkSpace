"""First-run setup and safe demonstration commands for OpenWorkSpace."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from openworkspace.cli import main as existing_cli
from openworkspace.identity import IdentityRegistry
from openworkspace.messages import MessageStore
from openworkspace.packages import PackageCatalog
from openworkspace.registry import CapabilityRegistry
from openworkspace.resources import ResourceCatalog
from openworkspace.tasks import TaskStore


def initialize_workspace(root: str | Path) -> dict[str, str]:
    """Create the local workspace stores without replacing existing user data."""
    workspace = Path(root).expanduser()
    workspace.mkdir(parents=True, exist_ok=True)
    database = workspace / "runtime.sqlite3"
    registry_database = workspace / "registry.sqlite3"
    evidence_path = workspace / "evidence.jsonl"

    IdentityRegistry(database)
    TaskStore(database)
    MessageStore(database)
    ResourceCatalog(database)
    PackageCatalog(database)
    CapabilityRegistry(registry_database)

    return {
        "workspace": str(workspace.resolve()),
        "runtime_database": str(database.resolve()),
        "registry_database": str(registry_database.resolve()),
        "evidence_journal": str(evidence_path.resolve()),
    }


def run_demo() -> dict[str, object]:
    """Run a deterministic permission-decision demo in a disposable directory."""
    manifest = {
        "id": "demo.local-review",
        "version": "1.0.0",
        "interface_version": "1",
        "description": "Non-executable demonstration of permission decisions.",
        "inputs": {},
        "outputs": {},
        "permissions": ["filesystem.read", "network.connect"],
    }
    with tempfile.TemporaryDirectory(prefix="openworkspace-demo-") as directory:
        registry = CapabilityRegistry(Path(directory) / "registry.sqlite3")
        registry.register(manifest)
        decisions = registry.evaluate(
            "demo.local-review", {"filesystem.read"}
        )
        result = {
            "demo": "permission-evaluation",
            "capability_id": manifest["id"],
            "decisions": [
                {
                    "permission": item.permission,
                    "allowed": item.allowed,
                    "reason": item.reason,
                }
                for item in decisions
            ],
            "executed": False,
            "os_access_enforced": False,
            "workspace_persisted": False,
        }
    return result


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] == "init":
        parser = argparse.ArgumentParser(
            prog="openworkspace init",
            description="Initialize local OpenWorkSpace metadata stores.",
        )
        parser.add_argument(
            "--path", type=Path, default=Path(".openworkspace"),
            help="workspace directory (default: .openworkspace)",
        )
        try:
            args = parser.parse_args(arguments[1:])
        except SystemExit as exc:
            return int(exc.code or 0)
        try:
            result = {"initialized": True, **initialize_workspace(args.path)}
            print(json.dumps(result, sort_keys=True))
            return 0
        except (OSError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    if arguments and arguments[0] == "demo":
        parser = argparse.ArgumentParser(
            prog="openworkspace demo",
            description="Run a safe, non-executing permission evaluation demo.",
        )
        try:
            parser.parse_args(arguments[1:])
        except SystemExit as exc:
            return int(exc.code or 0)
        print(json.dumps(run_demo(), sort_keys=True))
        return 0
    try:
        return existing_cli(arguments)
    except SystemExit as exc:
        return int(exc.code or 0)


if __name__ == "__main__":
    raise SystemExit(main())
