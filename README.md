# OpenWorkSpace

**Discover. Integrate. Build. Verify. Extend.**

OpenWorkSpace is an open-source, local-first digital workshop for discovering and connecting software, AI systems, tools, knowledge, and resources, then assembling new capabilities. It is an independent capability ecosystem, not a hosted platform or replacement operating system. No central service, account, subscription, token, or vendor-specific runtime is required by design.

## Status

**Pre-alpha, foundation in active development.** Version 0.1 provides capability-manifest validation, explicit permission-decision primitives, a local hash-linked evidence journal, and a small CLI. These are initial building blocks, not a complete security system or plugin platform.

| Capability | Status | Boundary |
|---|---|---|
| Capability manifest contract | Implemented | JSON Schema 2020-12 validation |
| Permission decision primitive | Implemented | Explicit grants only; not an OS enforcement boundary |
| Local evidence journal | Implemented | Hash-linked; not tamper-proof against privileged local administrators |
| CLI | Implemented | Manifest validation and journal verification |
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

## Six product systems

1. **Core:** contracts, identity, configuration, policy, lifecycle, evidence.
2. **Connect:** adapters for applications, services, devices, and systems.
3. **Exchange:** discovery, capability metadata, packages, resource catalogs.
4. **Atlas:** manuals, knowledge, technical references, provenance.
5. **Foundry:** requirements, capability-gap analysis, assembly, testing, delivery.
6. **Command Center:** optional local visibility and control interface.

These are product domains, not mandatory microservices.

## Security boundary

A manifest describes a capability. It does not make it safe, trusted, authorized, or executable. Signatures and hashes help establish origin and integrity; they do not prove benign behavior. The initial release does not execute third-party plugin code. Ordinary in-process Python execution is not a security sandbox.

See [SECURITY.md](SECURITY.md) and [architecture/threat-model.md](architecture/threat-model.md).

## Quick start

Requires Python 3.11 or newer.

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install -e '.[dev]'
pytest
ruff check .
```

```bash
openworkspace validate-manifest path/to/capability.json
openworkspace verify-evidence path/to/events.jsonl
```

Schema: [specifications/capability.schema.json](specifications/capability.schema.json).

## Roadmap

- [x] Initial Python package and CLI.
- [x] Capability manifest contract.
- [x] Default-deny permission decision primitive.
- [x] Local hash-linked evidence journal.
- [ ] Durable local capability registry and identity model.
- [ ] Task, message, permission, and evidence contracts.
- [ ] Integration and resilience tests.
- [ ] Qualified isolation before untrusted code execution.
- [ ] Independent TypeScript contract consumer.
- [ ] Reviewed integrations, knowledge resources, and community workflows.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Do not claim a capability is complete until its acceptance tests pass.

## License

Original project code is offered under Apache-2.0. Third-party integrations, packages, datasets, models, and documentation retain their own licenses and terms. A catalog entry never implies redistribution rights.
