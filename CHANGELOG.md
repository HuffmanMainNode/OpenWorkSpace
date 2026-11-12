# Changelog

## [0.1.0] - Unreleased

### Added
- Initial Python package and CLI.
- JSON Schema 2020-12 capability manifest contract and validator.
- Local SQLite capability registry with duplicate-ID rejection and manifest digest verification.
- Registry audit records and permission-decision evaluation.
- Local hash-linked JSONL evidence journal with strict schema and chain verification.
- Shared data catalogs for permissions, capability domains, resource types, trust states, data classification, lifecycle, and protocol candidates.
- Synthetic fixtures for all published contract schemas.
- Qualification requirements, environment matrix, and report schema.
- Repository population register and automated local Markdown-link validation.
- CI matrix for Python 3.11, 3.12, and 3.13.

### Security and reliability boundaries
- No third-party plugin execution, package installer, or arbitrary code runner.
- No OS-level sandbox, credential vault, network firewall, or identity authority.
- SQLite audit triggers are not tamper-proof against the database owner.
- Evidence hash chain is tamper-evident, not tamper-proof against a privileged local administrator.
- JSONL evidence journal does not provide concurrent multi-process writer locking or crash-consistency guarantees.
- Identity, task, message, resource, and external package contracts are specifications only.
- Windows and macOS are not release-qualified.
