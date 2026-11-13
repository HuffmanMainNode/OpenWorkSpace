# OpenWorkSpace

**Discover. Integrate. Build. Verify. Extend.**

OpenWorkSpace is an open-source, local-first digital workshop for discovering and connecting software, AI systems, tools, knowledge, and resources, then assembling new capabilities. It is an independent capability ecosystem, not a hosted platform or replacement operating system. No central service, account, subscription, token, or vendor-specific runtime is required by design.

## Current status

**Pre-alpha, foundation in active development.** The current Python package provides a declarative capability registry, local identity metadata lifecycle, local task lifecycle store, local SQLite message queue, permission-decision helper, and hash-linked evidence journal.

| Capability | Status | Boundary |
|---|---|---|
| Workspace initialization and demo | Implemented | Idempotent local store setup; demo is temporary and non-executing |
| Capability manifest contract | Implemented | JSON Schema 2020-12 validation |
| Local capability registry | Implemented | SQLite metadata store; no code execution |
| Registry audit | Implemented | Local audit records; database owner can alter the database |
| Permission decision primitive | Implemented | Exact explicit grants only; not OS enforcement |
| Identity metadata lifecycle | Implemented | Local records and status transitions; local Ed25519 key binding/signatures; no real-world identity proof or remote authentication |
| Task lifecycle store | Implemented | State transitions, active owner-record check, dependency readiness, retry limits; no task execution |
| Local message queue | Implemented | SQLite envelopes, active identity metadata checks, inbox and acknowledgement; no network transport or sender authentication |
| Evidence journal | Implemented | JSONL hash chain with cross-process writer lock and fsync; no external integrity anchor |
| Local resource catalog | Implemented | Metadata registration, search, trust-state lifecycle; no downloads or execution |
| External package intake | Implemented | Local manifest validation and artifact digest verification; no download, unpacking, or execution |
| Third-party plugin execution | Disabled | No arbitrary external code execution |
| OS-level sandbox | Not implemented | Required before untrusted execution |
| Cross-language SDK | Planned | Shared contract tests required |
| Machine-readable discovery | Added | Root descriptor, AI-agent instructions, and compact documentation index |
| Community contribution intake | Added | Metadata-first pull-request process; no automatic installation or execution |
| First-party resource catalog | Policy established | Repository-by-repository public, non-fork, license and provenance review remains separate |

## Design principles

- **Local-first:** core workflows should run locally and remain useful offline.
- **Open and portable:** no mandatory hosted service, proprietary runtime, or vendor lock-in.
- **Modular:** use and replace capabilities independently where practical.
- **Interoperable:** publish versioned, language-neutral contracts.
- **Default deny:** installation or discovery never grants permissions. Policy decisions remain advisory until an OS-level isolation backend is qualified.
- **Evidence over claims:** functionality and security statements require tests and documented limits.
- **Respect existing tools:** integrate proven software rather than rebuilding everything.
- **Privacy by design:** data remains local by default; telemetry export requires explicit configuration.
- **Independent extension:** users may add local resources without changing core code or submitting them upstream.
- **Machine-readable by design:** agents can discover project status, contracts, contribution rules, and security boundaries from structured files.

## Product architecture

1. **Core:** contracts, identity, configuration, policy, lifecycle, evidence.
2. **Connect:** adapters for applications, services, devices, systems.
3. **Exchange:** discovery, capability metadata, packages, resource catalogs.
4. **Atlas:** manuals, knowledge, technical references, provenance.
5. **Foundry:** requirements, capability-gap analysis, assembly, testing, delivery.
6. **Command Center:** optional local visibility and control interface.

These are product domains, not mandatory microservices.

## Security boundary

A manifest describes a capability. It does not make it safe, trusted, authorized, or executable. Identity records are local metadata and do not authenticate a person or prove control of a cryptographic key. Task records do not execute themselves. The message queue is local-only and does not authenticate sender claims. Signatures and hashes do not prove benign behavior.

The current release does not execute third-party plugin code. Ordinary in-process Python execution is not a security sandbox.

See [SECURITY.md](SECURITY.md), [the threat model](architecture/threat-model.md), and [the security guide](documentation/security/README.md).

## Quick start

Requires Python 3.11 or newer. Current CI tests Ubuntu with Python 3.11, 3.12, and 3.13.

```bash
git clone https://github.com/HuffmanMainNode/OpenWorkSpace.git
cd OpenWorkSpace
python -m venv .venv
. .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
pytest
ruff check .
openworkspace --help
openworkspace init
openworkspace demo
```

### Capability registry

```bash
openworkspace validate-manifest examples/hello-capability.json
openworkspace register examples/hello-capability.json --database .openworkspace/registry.sqlite3
openworkspace list --database .openworkspace/registry.sqlite3
openworkspace evaluate example.hello --grant filesystem.read --database .openworkspace/registry.sqlite3
```

Permission evaluation is metadata only. It does not grant operating-system access or execute a capability.

### Local identity, task, and message lifecycle

The default runtime database is `.openworkspace/runtime.sqlite3`. Create the two example identity records before creating tasks or sending messages:

```bash
openworkspace identity-create examples/contracts/identity.json
openworkspace identity-create examples/contracts/service-identity.json
openworkspace task-create examples/contracts/task.json
openworkspace task-transition task.example.validation ready --reason "Dependencies satisfied"
openworkspace task-transition task.example.validation running --reason "Claimed locally"
openworkspace task-transition task.example.validation succeeded --reason "Completed"
openworkspace message-send examples/contracts/message.json
openworkspace message-inbox example.local.core
openworkspace message-ack message.example.001 example.local.core
```

These operations manipulate local metadata and records. They do not provide identity authentication, worker execution, authenticated message delivery, or network transport.

## Evidence journal integrity and recovery

The local JSONL evidence journal verifies each complete event and its hash-chain link. Appends validate the final complete event rather than rereading the entire history. A final record without its newline is treated as a torn tail: new appends stop, and `openworkspace verify-evidence PATH` reports `torn_tail: true` with a non-zero exit.

Use `openworkspace evidence-repair PATH` only after reviewing the failure. Repair requires the complete preceding chain to verify, preserves the incomplete suffix in a separate `PATH.torn-<UTC timestamp>` file with restrictive permissions, truncates only the torn suffix, and appends a `journal.recovered` event containing the fragment length and SHA-256. It refuses clean journals and journals with corruption in a complete line. Keep the original journal and fragment sidecar as evidence.

**Integrity limits remain:** deleting complete trailing events is not detected by the local chain alone, and an attacker able to rewrite the whole journal can recompute the chain. Independent signed checkpoints are not implemented; that architectural decision remains owner-reserved. The journal is tamper-evident, not tamper-proof, and repair is not a substitute for backups or external integrity anchors.

## Extend OpenWorkSpace

Users may maintain a local resource collection without modifying the core. Community projects can be proposed through pull requests using the metadata-first intake process.

- [Resource catalog and distribution policy](catalog/README.md)
- [Local-only resource workspace](local-resources/README.md)
- [First-party resource collection](catalog/first-party/README.md)
- [Community resource collection](catalog/community/README.md)
- [Optional resource packs](catalog/packs/README.md)
- [Contribution intake and review process](contributions/README.md)
- [Contribution manifest schema](specifications/contribution.schema.json)
- [AI-agent instructions](AGENTS.md)
- [Machine-readable workspace descriptor](openworkspace.json)
- [Compact documentation index](llms.txt)

Submissions are not automatically trusted, installed, or executed. Direct upstream links are the default; redistribution requires license review.

See the [getting started guide](documentation/getting-started/README.md), [installation guide](documentation/installation/README.md), [storage and backup guide](documentation/storage/README.md), and [troubleshooting guide](documentation/troubleshooting/README.md).

## Repository guide

- [Architecture](architecture/master-architecture.md)
- [Garage model](architecture/garage-model.md)
- [Security requirements](architecture/security-requirements.md)
- [Integration model](architecture/integration-model.md)
- [Compatibility policy](architecture/compatibility-policy.md)
- [Contract specifications](specifications/README.md)
- [Shared data catalogs](data/README.md)
- [Repository population register](REPOSITORY-CATALOG.md)
- [Contract fixtures](examples/contracts/README.md)
- [Qualification requirements](qualification/requirements.yaml)
- [Test matrix](qualification/test-matrix.yaml)
- [Integration handbook](documentation/integrations/README.md)
- [Storage, backup, and long-term recovery](documentation/storage/README.md)
- [Contribution guide](CONTRIBUTING.md)
- [Governance](GOVERNANCE.md)

## Roadmap

- [x] Initial Python package and CLI.
- [x] Idempotent local workspace initialization and safe permission-evaluation demo.
- [x] Capability manifest validation and local registry.
- [x] Default-deny permission decision primitive.
- [x] Registry audit trail and local hash-linked evidence journal.
- [x] Local identity metadata lifecycle.
- [x] Local task lifecycle store with dependency-aware readiness.
- [x] Local message queue with recipient inbox and acknowledgement.
- [x] Initial architecture, security, integration, data catalog, and contributor documentation.
- [x] Local encrypted Ed25519 key binding, signing, and signature verification.
- [ ] Remote authentication, key rotation/recovery, and distributed revocation.
- [ ] Runtime task scheduler, worker execution, cancellation, and recovery.
- [ ] Authenticated message transport and protocol negotiation.
- [ ] Permission enforcement at actual OS/process boundaries.
- [x] Cross-process evidence journal writer locking and fsync.
- [x] Torn-tail detection and guarded repair with preserved fragment and recovery event.
- [ ] External integrity anchors and power-loss qualification.
- [ ] Qualified isolation before untrusted code execution.
- [ ] Independent TypeScript contract consumer and shared fixtures.
- [x] Local resource catalog with provenance metadata and explicit trust-state lifecycle.
- [x] External package metadata intake and local artifact digest verification, with execution disabled.
- [ ] Verified backup and restore workflow with encryption and integrity checks.
- [ ] Optional storage adapters for local folders, cloud drives, and object storage.
- [x] Machine-readable project discovery and AI-agent operating guidance.
- [x] Metadata-first community contribution intake and validation contract.
- [ ] First-party repository inventory and license/provenance qualification.
- [ ] Reviewed integrations, knowledge resources, and community workflows.
- [ ] Windows and macOS qualification.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Do not claim a capability is complete until its acceptance tests pass.

## License

Original project code is offered under Apache-2.0. Third-party integrations, packages, datasets, models, and documentation retain their own licenses and terms. A catalog entry never implies redistribution rights.

## Offline catalog validation

From a local clone, validate the first-party resource catalog, optional resource packs, and machine-readable source qualification records:

```bash
openworkspace validate-catalog --root .
```

This command reads only the selected local repository files. It does not contact GitHub, download resources, install dependencies, or execute upstream projects. It checks JSON schemas, repository and pack references, owner counts, immutable source revision pins, and consistency between qualification records and catalog entries. A successful result validates metadata consistency only; it is not a security certification or approval to install, execute, or redistribute a resource.
