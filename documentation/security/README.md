# Security Guide

## Pre-alpha warning

Do not rely on OpenWorkSpace as a production security boundary or use it to run untrusted code. It has no OS-level sandbox, plugin execution engine, credential vault, network firewall, signed update system, or complete identity/authorization service.

## Implemented

- Strict capability manifest validation.
- Local SQLite registry with duplicate-ID rejection and stored-manifest digest checks.
- Local identity records with encrypted Ed25519 private-key storage, public-key binding, and file-signature verification.
- Registry, identity, task, and message audit records protected from ordinary SQL update/delete statements by triggers.
- Permission-decision helper allowing only exact explicit grants.
- Local JSONL evidence journal with schema validation and SHA-256 hash chaining.
- CI tests for validation, policy decisions, registry behavior, CLI, and journal tampering.

## Important limitations

- SQLite audit triggers are not tamper-proof against a database owner who can drop triggers or rewrite the file.
- Registry metadata is descriptive. The registry does not run or isolate capabilities.
- Ed25519 signatures prove possession of the bound private key for specific bytes, not a real-world identity or remote authentication.
- Private key files are encrypted with a user passphrase and restricted to owner permissions on POSIX. Windows ACLs are not configured by this package.
- Local revocation does not propagate to other workspaces or remote systems.
- Task records are not executed by a worker engine. Message records remain in a local queue and sender identifiers are not authenticated.
- Local audit triggers deter ordinary SQL mutation but can be dropped by a database owner.
- A permission helper does not intercept system calls.
- Evidence hash chains do not protect against privileged local administrators who can rewrite the journal and recompute hashes.
- The JSONL journal has no inter-process writer lock or crash-consistency guarantee.
- A valid manifest, package digest, or signature is not proof of benign behavior.

## Safe-use guidance

- Do not add credentials or sensitive personal data to test fixtures.
- Do not execute downloaded packages or repositories through this project.
- Keep source and dependencies updated through a reviewed process.
- Treat imported files, web content, and model outputs as untrusted.
- Use a disposable environment for experiments, understanding that ordinary containers are not automatically secure sandboxes.
- Report suspected vulnerabilities privately using the repository's security reporting feature where available.

Read [SECURITY.md](../../SECURITY.md), [the threat model](../../architecture/threat-model.md), and [security requirements](../../architecture/security-requirements.md).
