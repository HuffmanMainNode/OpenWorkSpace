# Integration Handbook

No external integration is currently shipped or executed by the 0.1 core. This guide defines the review process for future integrations.

## Before proposing an integration

1. Identify a concrete user need and why an existing tool is preferable to a new implementation.
2. Locate the official publisher and canonical source.
3. Determine the license, redistribution rights, and applicable terms.
4. Record version, maintainer, dependencies, supported platforms, and update policy.
5. Describe all data read, written, transmitted, and retained.
6. List permissions, filesystem paths, network destinations, devices, and credentials required.
7. Define timeouts, retries, idempotency, cancellation, and failure behavior.
8. Provide isolated test evidence and a removal/recovery procedure.

## Intake states

Discovered → staged → inspected → qualified → authorized → enabled → monitored → revoked/removed.

Each state must be explicit. A catalog listing or successful metadata inspection does not grant permission to execute.

## Integration proposal template

Use this template in a design issue or pull request:

- Name and stable ID:
- Publisher and official source:
- Version and maintenance status:
- License and redistribution rights:
- Purpose and alternatives considered:
- Platforms and dependencies:
- Inputs, outputs, and data classification:
- Required permissions and scope:
- Network destinations and authentication:
- Isolation and resource limits:
- Tests and evidence:
- Known limitations:
- Disable, revoke, uninstall, and recovery:
