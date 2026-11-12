"""Command-line interface for the initial OpenWorkSpace foundation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from openworkspace.contracts import ContractError, validate_capability_file
from openworkspace.evidence import read_events


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openworkspace", description="Local-first digital workshop tools")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate-manifest", help="validate a capability manifest")
    validate.add_argument("path", type=Path)
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
        events = read_events(args.path)
        print(json.dumps({"valid": True, "events": len(events)}))
        return 0
    except (ContractError, OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
