# Troubleshooting

## `openworkspace: command not found`

Activate the virtual environment where the package was installed, or invoke the module from that environment. Reinstall with `python -m pip install -e '.[dev]'`.

## Manifest validation fails

- Confirm the file is valid UTF-8 JSON.
- Check required fields: `id`, `version`, `interface_version`, `description`, `inputs`, `outputs`, and `permissions`.
- Use a three-part numeric version such as `0.1.0`.
- Remove undeclared fields. The schema intentionally rejects unknown properties.
- Use only the permission names in the schema.

## Evidence verification fails

The CLI reports the first malformed record, broken link, or hash mismatch. Preserve a copy of the original journal before investigation. Do not edit records to make verification pass. A mismatch may result from corruption, truncation, manual editing, or an attempted alteration.

An empty or nonexistent journal currently verifies as zero events. Do not interpret that as evidence that an operation occurred.

## Tests fail locally

- Confirm Python is 3.11 or newer.
- Recreate the virtual environment if dependencies are inconsistent.
- Install the development extra.
- Run `pytest -ra` and `ruff check .`.
- Include the Python version, operating system, command, exit code, and complete relevant error output in a bug report. Remove secrets and personal data first.

## Security concern

Do not publish exploit details, credentials, private data, or sensitive logs in a public issue. Follow [SECURITY.md](../../SECURITY.md).
