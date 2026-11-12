# Security Guide

## Pre-alpha warning

Do not rely on OpenWorkSpace 0.1 as a production security boundary or use it to run untrusted code. It has no OS-level sandbox, plugin execution engine, credential vault, network firewall, signed update system, or complete identity/authorization service.

## What is implemented

- Strict validation of the current capability manifest.
- A permission-decision helper that allows only exact explicit grants.
- A local JSONL evidence journal with SHA-256 hash chaining and verification.
- CI tests for manifest validation, permission decisions, CLI behavior, and journal tampering.

## What is not implemented

A permission helper does not intercept system calls. A manifest's declared permissions do not constrain a process. A hash chain does not protect against a privileged local administrator who can rewrite the journal and recompute the chain. A signature would not prove code is benign.

## Safe-use guidance

- Do not add credentials or sensitive personal data to test fixtures.
- Do not execute downloaded packages or repositories through this project.
- Keep the source tree and dependencies updated through a reviewed process.
- Treat all imported files, web content, model outputs, and manifests as untrusted.
- Use a disposable environment for experimentation, understanding that ordinary containers are not automatically secure sandboxes.
- Report suspected vulnerabilities privately using the repository's security reporting feature where available.

Read [SECURITY.md](../../SECURITY.md), [the threat model](../../architecture/threat-model.md), and [security requirements](../../architecture/security-requirements.md).
