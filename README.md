# OpenWorkSpace

**Discover. Integrate. Build. Verify. Extend.**

OpenWorkSpace is an open-source, local-first digital workshop for discovering and connecting software, AI systems, tools, knowledge, and resources, then assembling new capabilities. It is an independent capability ecosystem, not a hosted platform or replacement operating system. No central service, account, subscription, token, or vendor-specific runtime is required by design.

## Current status

**Pre-alpha, foundation in active development.** The current Python package validates declarative capability manifests, stores them in a local SQLite registry, evaluates explicitly granted permissions, records registry audit events, and writes/verifies a local hash-linked evidence journal. These primitives do not constitute an operating-system security boundary or plugin execution platform.

| Capability | Status | Boundary |
|---|---|---|
| Capability manifest contract | Implemented | JSON Schema 2020-12 validation |
| Local capability registry | Implemented | SQLite metadata store; no code execution |
| Registry duplicate protection | Implemented | Duplicate IDs rejected |
| Registry audit | Implemented | Append-only SQLite audit table; local DB administrator can alter DB |
| Permission decision primitive | Implemented | Exact explicit grants only; not OS enforcement |
| Evidence journal | Implemented | JSONL hash chain, schema-validated; no concurrent writer lock |
| CLI | Implemented | Manifest validation, registry operations, permission evaluation, evidence verification |
| Identity metadata lifecycle | Implemented | Local records and status changes; no authentication or cryptographic identity proof |\n| Task lifecycle store | Implemented | Local state transitions and dependency readiness; no task execution engine |\n| Message, resource, package runtime | Specified | Schemas only |
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

A manifest describes a capability. It does not make it safe, trusted, authorized, or executable. Signatures and hashes help establish origin and integrity; they do not prove benign behavior. The current release does not execute third-party plugin code. Ordinary in-process Python execution is not a security sandbox.

See [SECURITY.md](SECURITY.md), [the threat model](architecture/threat-model.md), and the [security guide](documentation/security/README.md).

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

Register and inspect the declarative example:

```bash
openworkspace validate-manifest examples/hello-capability.json
openworkspace register examples/hello-capability.json --database .openworkspace/registry.sqlite3
openworkspace list --database .openworkspace/registry.sqlite3
openworkspace evaluate example.hello --grant filesystem.read --database .openworkspace/registry.sqlite3
```

The permission command evaluates metadata only. It does not grant the registered capability operating-system access or execute it.

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
- [x] Capability manifest validation.
- [x] Local SQLite capability registry.
- [x] Default-deny permission decision primitive.
- [x] Registry audit trail.
- [x] Local hash-linked evidence journal.
- [x] Initial architecture, security, integration, and contributor documentation.
- [x] Draft identity, task, message, permission, evidence, resource, and package schemas.
- [x] Local identity metadata lifecycle (authentication and cryptographic identity remain unimplemented).
- [x] Local task lifecycle store (task execution and message transport remain unimplemented).
- [ ] Permission enforcement at actual OS/process boundaries.
- [ ] Journal locking, crash consistency, and external integrity anchors.
- [ ] Qualified isolation before untrusted code execution.
- [ ] Independent TypeScript contract consumer and shared fixtures.
- [ ] Reviewed integrations, knowledge resources, and community workflows.
- [ ] Windows and macOS qualification.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Do not claim a capability is complete until its acceptance tests pass.

## License

Original project code is offered under Apache-2.0. Third-party integrations, packages, datasets, models, and documentation retain their own licenses and terms. A catalog entry never implies redistribution rights.
