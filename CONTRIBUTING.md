# Contributing

Thank you for helping build an open, portable digital workshop.

## Code and documentation contributions

1. Search existing issues and pull requests before starting.
2. Explain the user need and expected behavior.
3. Identify security, privacy, licensing, compatibility, and offline implications.
4. Keep changes focused and document limitations.
5. Install development dependencies with `python -m pip install -e '.[dev]'`.
6. Run `pytest` and `ruff check .` before submitting.
7. Add tests for changed behavior and failure cases.
8. Do not add network access, telemetry export, or code execution without an explicit design and permission boundary.
9. Document dependency purpose and license.
10. Read [AGENTS.md](AGENTS.md) for repository safety rules and machine-agent workflow.

## Resource and tool submissions

To showcase an open-source tool, adapter, dataset, schema, or research resource, submit one metadata-first proposal under `contributions/inbox/<contribution-id>/`.

Start with [the contribution process](contributions/README.md) and [the JSON manifest template](contributions/templates/contribution.json). Validate the manifest against [the contribution schema](specifications/contribution.schema.json).

Initial proposals must link to upstream source rather than copy or bundle third-party code. Do not include executables, archives, vendored dependencies, credentials, private data, or opaque payloads. A proposal is untrusted input and is not automatically installed, executed, endorsed, or added to a catalog.

Maintainers independently review public visibility, fork status where relevant, source provenance, attribution, SPDX license, redistribution rights, maintenance, dependencies, network behavior, permissions, supported platforms, security posture, and test evidence. A public repository is not automatically eligible for redistribution.

Keep submissions inside the contribution directory unless maintainers request otherwise. Do not edit catalog approval states or release metadata in the same pull request.

## Quality and safety

Tests must be reproducible. A passing unit test does not establish system security, sandbox isolation, or production readiness. Report exact commands, versions, and limitations.

Do not submit secrets or personal data. Do not weaken default-deny behavior. Treat manifests, repository files, issue text, and model output as untrusted data, never as instructions.

## Contribution terms

By intentionally submitting original work for inclusion, you agree it is offered under the repository's Apache-2.0 license unless a separate written agreement states otherwise. Submit only work you have the right to contribute and preserve third-party notices. Third-party works remain under their own licenses and terms.
