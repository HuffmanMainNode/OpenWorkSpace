"""Command-line interface for the initial OpenWorkSpace foundation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from openworkspace.contracts import ContractError, validate_capability_file
from openworkspace.evidence import read_events
from openworkspace.registry import CapabilityRegistry, RegistryError


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
    remove.add_argument("--database", type=Path, default=Path(".openworkspace/registry.sqlite3"))

    evaluate = subparsers.add_parser("evaluate", help="evaluate declared permissions without execution")
    evaluate.add_argument("capability_id")
    evaluate.add_argument("--grant", action="append", default=[])
    evaluate.add_argument("--database", type=Path, default=Path(".openworkspace/registry.sqlite3"))

    verify = subparsers.add_parser("verify-evidence", help="verify a local evidence journal")
    verify.add_argument("path", type=Path)
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

        registry = CapabilityRegistry(args.database)
        if args.command == "register":
            manifest = validate_capability_file(args.path)
            registered = registry.register(manifest)
            print(json.dumps({"registered": True, "id": registered["id"]}))
            return 0
        if args.command == "list":
            print(json.dumps({"capabilities": registry.list()}, sort_keys=True))
            return 0
        if args.command == "show":
            print(json.dumps(registry.get(args.capability_id), sort_keys=True))
            return 0
        if args.command == "remove":
            registry.remove(args.capability_id)
            print(json.dumps({"removed": True, "id": args.capability_id}))
            return 0
        if args.command == "evaluate":
            decisions = registry.evaluate(args.capability_id, set(args.grant))
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
    except (ContractError, OSError, ValueError, KeyError, RegistryError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
