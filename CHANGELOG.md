# Changelog

## [0.1.0] - Unreleased

### Fixed
- Cache the evidence schema validator and make journal appends validate only the final complete event.
- Write each evidence event with one append-mode descriptor write and fsync; fsync the parent directory on first journal creation where directory fsync is supported.
- Detect torn JSONL tails, block unsafe appends, preserve torn fragments during explicit repair, and record recovery metadata.
- Serialize journal readers with writers and expose torn-tail state in `verify-evidence`.
- Reject task self-dependencies before dependency lookup and remove the unsupported `unknown` identity-status CLI choice.
- Correct class-scope `list` annotation shadowing, Windows evidence-lock platform detection, and the PowerShell activation example.

### Tooling
- Add mypy to development dependencies and enforce source type checking in CI.

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
- First-run workspace initialization and a safe, non-executing permission evaluation demo.
- Complete CLI help visibility and clean-environment command smoke tests.
- Storage provider and long-term backup/restore architecture documentation, with current non-implementation boundaries clearly stated.
- Shared data catalogs and synthetic fixtures for published contract schemas.
- Qualification requirements, environment matrix, and report schema.
- Repository population register and automated local Markdown-link validation.
- Shared SQLite configuration using WAL mode, NORMAL synchronous setting, and a 5-second busy timeout across local stores.
- Cross-process evidence journal writer locking and fsync on append.
- Machine-readable project discovery descriptor, AI-agent operating instructions, and compact documentation index.
- Metadata-first community and first-party resource contribution process with a versioned JSON Schema contract.
- Resource catalog policy separating first-party, community, optional packs, and local-only additions.
- Automated validation tests for discovery metadata, contribution schema, contribution template, and intake boundaries.
- CI runtime dependency vulnerability auditing, weekly dependency compatibility checks, and Dependabot update configuration.

### Security and reliability boundaries
- Identity records are metadata, not authenticated or cryptographically verified identities.
- Task records are not executed by a scheduler or worker runtime.
- Message queue is local-only and does not authenticate sender claims or provide network transport.
- No third-party plugin execution, package installer, or arbitrary code runner.
- No OS-level sandbox, credential vault, network firewall, or identity authority.
- SQLite audit tables and local digests are not tamper-proof against the database owner.
- Evidence hash chain is tamper-evident, not tamper-proof against a privileged local administrator.
- JSONL evidence appends use cross-process writer locking and fsync, but lack an external integrity anchor and completed crash/power-loss/network-filesystem qualification.
- No complete portable backup/restore workflow or native cloud storage connector is implemented.
- Windows and macOS are not release-qualified.
