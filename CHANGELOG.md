# Changelog

## [0.1.0] - Unreleased

### Added
- Initial Python package and CLI.
- JSON Schema 2020-12 capability manifest contract and validator.
- Local SQLite capability registry with duplicate-ID rejection and manifest digest verification.
- Registry audit records and permission-decision evaluation.
- Local hash-linked JSONL evidence journal with strict schema and chain verification.
- Local identity metadata registry with audited active, suspended, and revoked lifecycle transitions.
- Passphrase-encrypted local Ed25519 key storage, public-key binding, and file-signature helpers.
- Local task lifecycle store with active owner-record checks, dependency-aware readiness refresh, retry limits, integrity checks, and audited transitions.
- Local SQLite message queue with active identity metadata checks, inbox retrieval, recipient acknowledgement, and audit events.
- Local resource catalog with metadata search, explicit trust-state transitions, digest checks, and append-only audit records.
- External package manifest validation and local artifact SHA-256 verification with execution disabled.
- CLI commands for capability, identity, task, message, resource, package intake, and evidence operations.
- Shared data catalogs and synthetic fixtures for published contract schemas.
- Qualification requirements, environment matrix, and report schema.
- Repository population register and automated local Markdown-link validation.
- Shared SQLite configuration using WAL mode, NORMAL synchronous setting, and a 5-second busy timeout across local stores.
- Cross-process evidence journal writer locking and fsync on append.
- CI stress test for concurrent journal writers and SQLite configuration.

### Security and reliability boundaries
- Identity records are metadata, not authenticated or cryptographically verified identities.
- Task records are not executed by a scheduler or worker runtime.
- Message queue is local-only and does not authenticate sender claims or provide network transport.
- No third-party plugin execution, package installer, or arbitrary code runner.
- No OS-level sandbox, credential vault, network firewall, or identity authority.
- SQLite audit tables and local digests are not tamper-proof against the database owner.
- Evidence hash chain is tamper-evident, not tamper-proof against a privileged local administrator.
- JSONL evidence journal does not provide concurrent multi-process writer locking or crash-consistency guarantees.
- Windows and macOS are not release-qualified.
