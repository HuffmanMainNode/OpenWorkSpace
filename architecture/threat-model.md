# Initial Threat Model

## Assets
User data and local files; credentials and cryptographic material; capability manifests, packages, and dependencies; policy decisions; evidence journals and recovery material; integrity of the installation and update process.

## Trust boundaries
1. User and local operating-system account.
2. OpenWorkSpace core process.
3. Local files and imported manifests.
4. External packages, repositories, models, and integrations.
5. Optional network-connected systems.
6. Other local users and processes.

## Threats
- Malformed or adversarial manifests.
- Dependency substitution and package confusion.
- Unauthorized filesystem or network access.
- Prompt injection through imported content.
- Credential exposure in logs or task payloads.
- Resource exhaustion and retry storms.
- Partial writes, corrupted journals, interrupted updates.
- Malicious or compromised update channels.
- Privileged local attacker replacing data and verification logic.

## Current mitigations
Strict JSON Schema validation with unknown fields rejected; explicit permission decisions default to deny; no arbitrary third-party code execution; hash-linked local evidence records with verification; tests for malformed contracts and journal tampering.

## Known gaps
No OS-level sandbox, process isolation, filesystem confinement, network egress enforcement, secret vault, signed release process, external trust anchor, or complete identity system is implemented. A local administrator can rewrite the hash chain and recompute hashes. Do not treat this release as a production security boundary.
