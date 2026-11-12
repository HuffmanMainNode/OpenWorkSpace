"""Command-line interface for the OpenWorkSpace local foundation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from openworkspace.contracts import ContractError, validate_capability_file
from openworkspace.evidence import read_events
from openworkspace.identity import IdentityError, IdentityRegistry
from openworkspace.registry import CapabilityRegistry, RegistryError
from openworkspace.tasks import TaskError, TaskStore


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid UTF-8 JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object in {path}")
    return value


def _database_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--database", type=Path, default=Path(".openworkspace/runtime.sqlite3"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openworkspace",
        description="Local-first digital workshop tools",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate-manifest", help="validate a capability manifest")
    validate.add_argument("path", type=Path)

    register = subparsers.add_parser("register", help="validate and register a capability manifest")
    register.add_argument("path", type=Path)
    register.add_argument("--database", type=Path, default=Path(".openworkspace/registry.sqlite3"))

    listing = subparsers.add_parser("list", help="list registered capability metadata")
    listing.add_argument("--database", type=Path, default=Path(".openworkspace/registry.sqlite3"))

    show = subparsers.add_parser("show", help="show a registered capability manifest")
    show.add_argument("capability_id")
    show.add_argument("--database", type=Path, default=Path(".openworkspace/registry.sqlite3"))

    remove = subparsers.add_parser("remove", help="remove a capability metadata record")
    remove.add_argument("capability_id")
    remove.add_argument(
        "--database", type=Path, default=Path(".openworkspace/registry.sqlite3")
    )

    evaluate = subparsers.add_parser(
        "evaluate", help="evaluate declared permissions without execution"
    )
    evaluate.add_argument("capability_id")
    evaluate.add_argument("--grant", action="append", default=[])
    evaluate.add_argument("--database", type=Path, default=Path(".openworkspace/registry.sqlite3"))

    verify = subparsers.add_parser("verify-evidence", help="verify a local evidence journal")
    verify.add_argument("path", type=Path)

    identity_create = subparsers.add_parser(
        "identity-create", help="create a local identity metadata record"
    )
    identity_create.add_argument("path", type=Path)
    _database_argument(identity_create)

    identity_show = subparsers.add_parser("identity-show", help="show local identity metadata")
    identity_show.add_argument("identity_id")
    _database_argument(identity_show)

    identity_status = subparsers.add_parser("identity-status", help="change local identity status")
    identity_status.add_argument("identity_id")
    identity_status.add_argument("status", choices=["active", "suspended", "revoked", "unknown"])
    identity_status.add_argument("--reason", required=True)
    _database_argument(identity_status)

    task_create = subparsers.add_parser("task-create", help="create a local task record")
    task_create.add_argument("path", type=Path)
    _database_argument(task_create)

    task_list = subparsers.add_parser("task-list", help="list local task records")
    _database_argument(task_list)

    task_show = subparsers.add_parser("task-show", help="show a local task record")
    task_show.add_argument("task_id")
    _database_argument(task_show)

    task_transition = subparsers.add_parser("task-transition", help="change a task lifecycle state")
    task_transition.add_argument("task_id")
    task_transition.add_argument(
        "state",
        choices=["pending", "ready", "running", "succeeded", "failed", "cancelled", "blocked"],
    )
    task_transition.add_argument("--reason", required=True)
    _database_argument(task_transition)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate-manifest":
            manifest = validate_capability_file(args.path)
            print(json.dumps({"valid": True, "id": manifest["id"], "version": manifest["version"]}))
            return 0
        if args.command == "verify-evidence":
            events = read_events(args.path)
            print(json.dumps({"valid": True, "events": len(events)}))
            return 0
        if args.command == "identity-create":
            record = IdentityRegistry(args.database).create(_read_json(args.path))
            print(json.dumps({"created": True, "id": record["id"], "status": record["status"]}))
            return 0
        if args.command == "identity-show":
            print(json.dumps(IdentityRegistry(args.database).get(args.identity_id), sort_keys=True))
            return 0
        if args.command == "identity-status":
            record = IdentityRegistry(args.database).set_status(
                args.identity_id, args.status, reason=args.reason
            )
            print(json.dumps({"id": record["id"], "status": record["status"]}, sort_keys=True))
            return 0
        if args.command == "task-create":
            task = TaskStore(args.database).create(_read_json(args.path))
            print(json.dumps({"created": True, "id": task["id"], "state": task["state"]}))
            return 0
        if args.command == "task-list":
            print(json.dumps({"tasks": TaskStore(args.database).list()}, sort_keys=True))
            return 0
        if args.command == "task-show":
            print(json.dumps(TaskStore(args.database).get(args.task_id), sort_keys=True))
            return 0
        if args.command == "task-transition":
            task = TaskStore(args.database).transition(
                args.task_id, args.state, reason=args.reason
            )
            print(json.dumps({"id": task["id"], "state": task["state"]}, sort_keys=True))
            return 0

        if args.command == "register":
            manifest = validate_capability_file(args.path)
            registered = CapabilityRegistry(args.database).register(manifest)
            print(json.dumps({"registered": True, "id": registered["id"]}))
            return 0
        if args.command == "list":
            capabilities = CapabilityRegistry(args.database).list()
            print(json.dumps({"capabilities": capabilities}, sort_keys=True))
            return 0
        if args.command == "show":
            manifest = CapabilityRegistry(args.database).get(args.capability_id)
            print(json.dumps(manifest, sort_keys=True))
            return 0
        if args.command == "remove":
            CapabilityRegistry(args.database).remove(args.capability_id)
            print(json.dumps({"removed": True, "id": args.capability_id}))
            return 0
        if args.command == "evaluate":
            decisions = CapabilityRegistry(args.database).evaluate(
                args.capability_id, set(args.grant)
            )
            print(
                json.dumps(
                    {
                        "executed": False,
                        "decisions": [
                            {
                                "permission": item.permission,
                                "allowed": item.allowed,
                                "reason": item.reason,
                            }
                            for item in decisions
                        ],
                    },
                    sort_keys=True,
                )
            )
            return 0 if all(item.allowed for item in decisions) else 3
    except (
        ContractError, OSError, ValueError, KeyError,
        RegistryError, IdentityError, TaskError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
