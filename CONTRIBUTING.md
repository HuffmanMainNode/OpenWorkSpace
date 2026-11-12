# Contributing

Thank you for helping build an open, portable digital workshop.

1. Search existing issues and pull requests before starting.
2. Explain the user need and expected behavior.
3. Identify security, privacy, licensing, compatibility, and offline implications.
4. Keep changes focused and document limitations.
5. Install development dependencies with `python -m pip install -e '.[dev]'`.
6. Run `pytest` and `ruff check .` before submitting.
7. Add tests for changed behavior and failure cases.
8. Do not add network access, telemetry export, or code execution without an explicit design and permission boundary.
9. Document dependency purpose and license.

Tests must be reproducible. A passing unit test does not establish system security, sandbox isolation, or production readiness.

By intentionally submitting a contribution for inclusion, you agree it is offered under the repository's Apache-2.0 license unless a separate written agreement states otherwise. Submit only work you have the right to contribute and preserve third-party notices.
