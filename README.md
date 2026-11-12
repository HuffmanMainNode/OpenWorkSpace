# OpenWorkSpace

**Discover. Integrate. Build. Verify. Extend.**

OpenWorkSpace is an open-source, local-first digital workshop for discovering and connecting software, AI systems, tools, knowledge, and resources, then assembling new capabilities. It is an independent capability ecosystem, not a hosted platform or replacement operating system. No central service, account, subscription, token, or vendor-specific runtime is required by design.

## Current status

**Pre-alpha, foundation in active development.** The current Python package provides a declarative capability registry, local identity metadata lifecycle, local task lifecycle store, local SQLite message queue, permission-decision helper, and hash-linked evidence journal.

| Capability | Status | Boundary |
|---|---|---|
| Capability manifest contract | Implemented | JSON Schema 2020-12 validation |
| Local capability registry | Implemented | SQLite metadata store; no code execution |
| Registry audit | Implemented | Local audit records; database owner can alter the database |
| Permission decision primitive | Implemented | Exact explicit grants only; not OS enforcement |
| Identity metadata lifecycle | Implemented | Local records and status transitions; local Ed25519 key binding and signatures; no real-world identity proof or remote authentication |
| Task lifecycle store | Implemented | State transitions, active owner-record check, dependency readiness, retry limits; no task execution |
| Local message queue | Implemented | SQLite envelopes, active identity metadata checks, inbox and acknowledgement; no network transport or sender authentication |
| Evidence journal | Implemented | JSONL hash chain; no multi-writer lock or external integrity anchor |
| Local resource catalog | Implemented | Metadata registration, search, trust-state lifecycle; no downloads or execution |
| External package intake runtime | Specified | Metadata schema only; no installer or execution |
| Third-party plugin execution | Disabled | No arbitrary external code execution |
| OS-level sandbox | Not implemented | Required before untrusted execution |
| Cross-language SDK | Planned | Shared contract tests required |

## Design principles

- **Local-first:** core workflows should run locally and remain useful offline.
- **Open and portable:** no mandatory hosted service, proprietary runtime, or vendor lock-in.
- **Modular:** use and replace capabilities independently where practical.
- **Interoperable:** publish versioned, language-neutral contracts.
- **Default deny:** installation or discovery never grants permissions.
- **Evidence over claims:** functionality and security statements require tests and documented limits.
- **Respect existing tools:** integrate proven software rather than rebuilding everything.
- **Privacy by design:** data remains local by default; telemetry export requires explicit configuration.

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
. .venv/bin/activate  # Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -e '.[dev]'
pytest
ruff check .
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

See the [getting started guide](documentation/getting-started/README.md), [installation guide](documentation/installation/README.md), and [troubleshooting guide](documentation/troubleshooting/README.md).

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
- [Contribution guide](CONTRIBUTING.md)
- [Governance](GOVERNANCE.md)

## Roadmap

- [x] Initial Python package and CLI.
- [x] Capability manifest validation and local registry.
- [x] Default-deny permission decision primitive.
- [x] Registry audit trail and local hash-linked evidence journal.
- [x] Local identity metadata lifecycle.
- [x] Local task lifecycle store with dependency-aware readiness.
- [x] Local message queue with recipient inbox and acknowledgement.
- [x] Initial architecture, security, integration, data catalog, and contributor documentation.
- [x] Local encrypted Ed25519 key binding, signing, and signature verification.\n- [ ] Remote authentication, key rotation/recovery, and distributed revocation.
- [ ] Runtime task scheduler, worker execution, cancellation, and recovery.
- [ ] Authenticated message transport and protocol negotiation.
- [ ] Permission enforcement at actual OS/process boundaries.
- [ ] Journal locking, crash consistency, and external integrity anchors.
- [ ] Qualified isolation before untrusted code execution.
- [ ] Independent TypeScript contract consumer and shared fixtures.
- [x] Local resource catalog with provenance metadata and explicit trust-state lifecycle.
- [ ] Reviewed integrations, knowledge resources, and community workflows.
- [ ] Windows and macOS qualification.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Do not claim a capability is complete until its acceptance tests pass.

## License

Original project code is offered under Apache-2.0. Third-party integrations, packages, datasets, models, and documentation retain their own licenses and terms. A catalog entry never implies redistribution rights.
