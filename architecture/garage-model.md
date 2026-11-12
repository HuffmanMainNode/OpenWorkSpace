# The Garage Model

OpenWorkSpace is a digital workshop: a place to find the right tools, understand how they fit, and assemble useful work. The project does not need to own or recreate every tool in the ecosystem.

## Seven conceptual layers

1. **Core Foundation:** contracts, identity, configuration, policy, lifecycle, evidence, and resource controls.
2. **Integration and Exchange:** adapters, package metadata, registries, and interoperability contracts.
3. **Security and Assurance:** inspection, trust decisions, permission boundaries, isolation, monitoring, and recovery.
4. **Operations and Coordination:** task lifecycle, workflow coordination, agent collaboration, and observability.
5. **Knowledge and Instructions:** manuals, blueprints, technical references, provenance, and learning resources.
6. **Tools and Equipment:** software, libraries, AI models, devices, services, and external integrations.
7. **Creation and Construction:** requirements, capability-gap analysis, engineering, assembly, testing, and delivery.

The layers are conceptual boundaries, not a requirement to deploy seven services. A small installation may implement several layers in one local process.

## Resource classification

Every catalog item must declare what it is:

- **Reference:** documentation or knowledge; not executable.
- **External integration:** connects to independently installed software or a remote system.
- **Managed dependency:** a package whose acquisition and lifecycle are managed.
- **Isolated capability:** executable functionality operating inside a qualified isolation boundary.
- **Native capability:** functionality implemented and maintained by this project.

## Intake rule

Discovery is not approval. Acquisition is not inspection. Inspection is not qualification. Qualification is not authorization. No untrusted executable is run merely because it appears in a registry.

## Build rule

Prefer integrating a maintained, suitable tool over recreating it. Before adoption, record its source, license, maintainer, dependencies, compatibility, permissions, security posture, and removal path.
