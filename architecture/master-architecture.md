# Master Architecture

OpenWorkSpace is a modular, local-first capability ecosystem. It helps people and existing systems discover tools and resources, connect independently maintained technology, preserve operational knowledge, and assemble capabilities without a central hosted platform.

## Constraints
1. Core operation should remain useful offline.
2. No mandatory server, account, subscription, token, or proprietary runtime.
3. Integrations are optional and independently removable.
4. Contracts are versioned and language-neutral where practical.
5. Discovery never implies trust or execution authorization.
6. Untrusted code execution stays disabled until isolation is qualified.
7. Data export, network access, and telemetry are explicit policy decisions.

## Product domains
- **Core:** contracts, identity, configuration, policy, lifecycle, evidence.
- **Connect:** adapters to applications, services, devices, and protocols.
- **Exchange:** discovery, registries, package metadata, resource catalogs.
- **Atlas:** manuals, knowledge, provenance, technical references.
- **Foundry:** requirements, capability-gap analysis, assembly, testing, delivery.
- **Command Center:** optional local visibility and control.

These are conceptual domains, not mandatory microservices.

## Initial implementation
The 0.1 Python package and CLI validate declarative capability manifests against JSON Schema 2020-12, expose a default-deny permission-decision primitive, and write/verify a local hash-linked JSONL evidence journal. The permission primitive is not an OS enforcement mechanism. The journal is not tamper-proof against a privileged local administrator.

## Trust lifecycle
A future lifecycle should distinguish discovery, acquisition, inspection, qualification, authorization, execution, monitoring, revocation, and removal. A manifest is descriptive metadata only. Publisher, digest, license, dependencies, permissions, behavior, compatibility, and maintenance require independent assessment.

JSON Schema 2020-12 is the initial manifest format. Other protocols and language SDKs may be adopted through documented adapters when they solve concrete needs. No protocol is mandatory for core operation.
