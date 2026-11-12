# Troubleshooting

## `openworkspace: command not found`

Activate the virtual environment where the package was installed, or reinstall with `python -m pip install -e '.[dev]'`.

## Manifest validation fails

- Confirm the file is valid UTF-8 JSON.
- Check required fields: `id`, `version`, `interface_version`, `description`, `inputs`, `outputs`, and `permissions`.
- Use a three-part numeric version such as `0.1.0`.
- Remove undeclared fields. The schema intentionally rejects unknown properties.
- Use only permission names in the schema.

## Registry reports a duplicate

Capability IDs are unique. The registry intentionally refuses to overwrite an existing ID. Review the registered manifest and design a future explicit update/migration workflow rather than deleting data blindly.

## Registry reports an integrity error

The registry stores a SHA-256 digest of each canonical manifest. Preserve a copy of the database before investigating. Do not edit the database to force a successful check. A mismatch can indicate corruption or manual modification.

## Evidence verification fails

The CLI reports a missing, empty, malformed, altered, or broken journal. Preserve a copy of the original before investigation. Do not edit records to make verification pass.

Evidence writers are serialized across processes using an OS-specific file lock. If a process terminates unexpectedly, preserve the original journal and lock file for investigation. Do not edit records to make verification pass.

## Custom workspace path

If you initialized a workspace with `openworkspace init --path /some/path`, commands still use their documented `--database` defaults unless you pass the selected database path explicitly. Use `/some/path/runtime.sqlite3` for identity, task, message, resource, and package commands, and `/some/path/registry.sqlite3` for capability registry commands.

## Tests fail locally

- Confirm Python is 3.11 or newer.
- Recreate the virtual environment if dependencies are inconsistent.
- Install the development extra.
- Run `pytest -ra` and `ruff check .`.
- Include Python version, operating system, command, exit code, and relevant error output in a bug report. Remove secrets and personal data first.

## Security concern

Do not publish exploit details, credentials, private data, or sensitive logs in a public issue. Follow [SECURITY.md](../../SECURITY.md).
