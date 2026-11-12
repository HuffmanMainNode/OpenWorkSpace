"""Command-line interface for the OpenWorkSpace local foundation."""

from __future__ import annotations

import argparse
import getpass
import json
import sys
from pathlib import Path

from openworkspace.contracts import ContractError, validate_capability_file
from openworkspace.evidence import read_events
from openworkspace.identity import IdentityError, IdentityRegistry
from openworkspace.identity_keys import IdentityKeyError, IdentityKeyStore
from openworkspace.messages import MessageError, MessageStore
from openworkspace.registry import CapabilityRegistry, RegistryError
from openworkspace.resources import ResourceCatalog, ResourceCatalogError
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

    identity_keygen = subparsers.add_parser(
        "identity-keygen", help="generate a passphrase-encrypted local Ed25519 key"
    )
    identity_keygen.add_argument("identity_id")
    identity_keygen.add_argument(
        "--key-directory", type=Path, default=Path(".openworkspace/keys")
    )
    _database_argument(identity_keygen)

    identity_sign = subparsers.add_parser(
        "identity-sign", help="sign a file with a local identity key"
    )
    identity_sign.add_argument("identity_id")
    identity_sign.add_argument("path", type=Path)
    identity_sign.add_argument(
        "--key-directory", type=Path, default=Path(".openworkspace/keys")
    )
    _database_argument(identity_sign)

    identity_verify = subparsers.add_parser(
        "identity-verify", help="verify a signature against a registered public key"
    )
    identity_verify.add_argument("identity_id")
    identity_verify.add_argument("path", type=Path)
    identity_verify.add_argument("signature")
    _database_argument(identity_verify)

    task_create = subparsers.add_parser("task-create", help="create a local task record")
    task_create.add_argument("path", type=Path)
    _database_argument(task_create)

    task_list = subparsers.add_parser("task-list", help="list local task records")
    _database_argument(task_list)

    task_refresh = subparsers.add_parser(
        "task-refresh-ready", help="promote tasks whose dependencies have succeeded"
    )
    _database_argument(task_refresh)

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

    message_send = subparsers.add_parser("message-send", help="enqueue a local message envelope")
    message_send.add_argument("path", type=Path)
    _database_argument(message_send)

    message_inbox = subparsers.add_parser("message-inbox", help="list a local identity inbox")
    message_inbox.add_argument("identity_id")
    message_inbox.add_argument("--include-acknowledged", action="store_true")
    _database_argument(message_inbox)

    message_ack = subparsers.add_parser("message-ack", help="acknowledge a queued message")
    message_ack.add_argument("message_id")
    message_ack.add_argument("recipient_id")
    _database_argument(message_ack)

    resource_register = subparsers.add_parser(
        "resource-register", help="register a resource metadata record"
    )
    resource_register.add_argument("path", type=Path)
    _database_argument(resource_register)

    resource_list = subparsers.add_parser(
        "resource-list", help="list and filter local resource records"
    )
    resource_list.add_argument("--search")
    resource_list.add_argument("--resource-type")
    resource_list.add_argument("--trust-state")
    _database_argument(resource_list)

    resource_show = subparsers.add_parser(
        "resource-show", help="show a local resource record"
    )
    resource_show.add_argument("resource_id")
    _database_argument(resource_show)

    resource_trust = subparsers.add_parser(
        "resource-trust", help="change a resource trust state"
    )
    resource_trust.add_argument("resource_id")
    resource_trust.add_argument(
        "state",
        choices=[
            "uninspected", "inspected", "qualified", "authorized",
            "restricted", "quarantined", "revoked",
        ],
    )
    resource_trust.add_argument("--reason", required=True)
    _database_argument(resource_trust)
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
        if args.command == "identity-keygen":
            first = getpass.getpass("New identity key passphrase: ")
            second = getpass.getpass("Confirm passphrase: ")
            if first != second:
                raise IdentityKeyError("passphrases do not match")
            binding = IdentityKeyStore(args.key_directory).generate(
                args.identity_id, first, IdentityRegistry(args.database)
            )
            print(json.dumps({
                "identity_id": binding["identity_id"],
                "key_reference": binding["key_reference"],
                "key_generated": True,
            }, sort_keys=True))
            return 0
        if args.command == "identity-sign":
            passphrase = getpass.getpass("Identity key passphrase: ")
            signature = IdentityKeyStore(args.key_directory).sign(
                args.identity_id, args.path.read_bytes(), passphrase,
                IdentityRegistry(args.database),
            )
            print(json.dumps({"signature": signature}, sort_keys=True))
            return 0
        if args.command == "identity-verify":
            valid = IdentityKeyStore.verify(
                args.identity_id, args.path.read_bytes(), args.signature,
                IdentityRegistry(args.database),
            )
            print(json.dumps({"valid": valid}, sort_keys=True))
            return 0 if valid else 4
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
        if args.command == "task-refresh-ready":
            promoted = TaskStore(args.database).refresh_ready()
            print(json.dumps({"promoted": promoted}, sort_keys=True))
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
        if args.command == "message-send":
            envelope = MessageStore(args.database).enqueue(_read_json(args.path))
            print(json.dumps({"queued": True, "message_id": envelope["message_id"]}))
            return 0
        if args.command == "message-inbox":
            messages = MessageStore(args.database).inbox(
                args.identity_id, include_acknowledged=args.include_acknowledged
            )
            print(json.dumps({"messages": messages}, sort_keys=True))
            return 0
        if args.command == "message-ack":
            MessageStore(args.database).acknowledge(args.message_id, args.recipient_id)
            print(json.dumps({"acknowledged": True, "message_id": args.message_id}))
            return 0
        if args.command == "resource-register":
            record = ResourceCatalog(args.database).register(_read_json(args.path))
            print(json.dumps({"registered": True, "id": record["id"]}))
            return 0
        if args.command == "resource-list":
            records = ResourceCatalog(args.database).list(
                search=args.search,
                resource_type=args.resource_type,
                trust_state=args.trust_state,
            )
            print(json.dumps({"resources": records}, sort_keys=True))
            return 0
        if args.command == "resource-show":
            record = ResourceCatalog(args.database).get(args.resource_id)
            print(json.dumps(record, sort_keys=True))
            return 0
        if args.command == "resource-trust":
            record = ResourceCatalog(args.database).update_trust_state(
                args.resource_id, args.state, reason=args.reason
            )
            print(
                json.dumps(
                    {"id": record["id"], "trust_state": record["trust_state"]},
                    sort_keys=True,
                )
            )
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
        RegistryError, IdentityError, IdentityKeyError, TaskError, MessageError,
        ResourceCatalogError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
