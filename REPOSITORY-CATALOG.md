# Repository Catalog and Population Register

This index distinguishes shipped code from specifications and planned systems. A file existing in the repository does not imply that its described runtime exists.

## Project foundation

| Area | Contents | State |
|---|---|---|
| Packaging | `pyproject.toml`, package metadata, CLI entry point | Implemented |
| Licensing | Apache-2.0 project license | Published |
| CI | Python 3.11, 3.12, 3.13 install, tests, Ruff, wheel smoke tests | Implemented |
| Community | Contribution guide, governance, conduct, issue templates | Published |
| Security disclosure | Security policy and threat model | Published |

## Executable core

| Module | Responsibility | State |
|---|---|---|
| `contracts.py` | Validate capability manifests | Implemented |
| `registry.py` | Local SQLite registry, duplicate protection, digest check, transactional audit | Implemented |
| `policy.py` | Explicit permission decision helper | Implemented, not OS enforcement |
| `identity.py` | Local identity metadata lifecycle, encrypted Ed25519 key binding, and audit | Implemented, no authentication or cryptographic identity proof |
| `tasks.py` | Task state store, active owner-record check, dependency readiness refresh, retry limits, audit | Implemented, no task execution engine |
| `messages.py` | Local SQLite message queue, active identity metadata checks, inbox, acknowledgement, audit | Implemented, no network transport or sender authentication |
| `resources.py` | Local resource catalog, search, trust-state lifecycle, audit | Implemented, metadata only; no downloads or execution |
| `packages.py` | Package manifest validation, local artifact digest verification, metadata ledger | Implemented, no downloads, unpacking, signature verification, or execution |
| `packages.py` | Package manifest validation, local artifact digest verification, metadata ledger | Implemented, no download, unpacking, signature verification, or execution |
| `evidence.py` | Schema-validated JSONL hash chain with cross-process writer locking and fsync | Implemented, no external integrity anchor or power-loss qualification |
| `database.py` | Shared SQLite WAL, synchronous, and busy-timeout configuration | Implemented |\n| `cli.py` | Capability, identity, task, message, resource, package-intake, and evidence commands | Implemented |

## Contract and data pack

- `specifications/`: capability, registry, identity, task, message, permission, evidence, resource, and external package schemas.
- `data/catalogs/`: permission identifiers, capability domains, resource types, trust states, data classification, lifecycle, and protocol candidates.
- `examples/contracts/`: synthetic fixtures for published contract schemas.
- `qualification/`: requirement register, environment matrix, and qualification report schema.

## Architecture and documentation

- `architecture/`: master architecture, garage model, threat model, trust model, integration model, security requirements, compatibility policy, and architecture decision record.
- `documentation/`: installation, getting started, integrations, security, troubleshooting.
- `SECURITY.md`, `CONTRIBUTING.md`, `GOVERNANCE.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`.

## Explicitly not shipped

No third-party code runner, plugin loader, package downloader, OS sandbox, secret vault, network firewall, identity authority, task execution engine, network message broker, agent runtime, MCP/A2A adapter, cloud service, hosted control plane, telemetry exporter, or cross-language SDK is included.

## Verification

Tests cover schema validity, fixture conformance, permission catalog consistency, registry behavior, identity lifecycle, task lifecycle and dependencies, message queue operations, duplicate and tampered data, concurrent distinct registrations, multi-process evidence writers, evidence tampering, CLI flows, and local Markdown links. The CI matrix is the authoritative record of the latest tested commit and environment.
