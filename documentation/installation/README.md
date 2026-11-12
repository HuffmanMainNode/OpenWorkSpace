# Installation Guide

## Supported baseline

The CI pipeline tests Python 3.11, 3.12, and 3.13 on Ubuntu. Windows and macOS are not yet release-qualified. The package is pre-alpha; use a disposable workspace for evaluation.

## Install for use

Clone the repository and install the package into an isolated virtual environment:

```bash
git clone https://github.com/HuffmanMainNode/OpenWorkSpace.git
cd OpenWorkSpace
python -m venv .venv
```

Activate the environment:

```bash
# Linux / macOS
. .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install the runtime package and initialize a local workspace:

```bash
python -m pip install --upgrade pip
python -m pip install .
openworkspace --help
openworkspace init
openworkspace demo
```

The demo is non-executing and uses temporary data. The default persistent workspace is `.openworkspace/`.

## Developer installation

To run tests and lint checks, install the development extra instead:

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
```

## Local data locations

The default runtime database is `.openworkspace/runtime.sqlite3`; capability registry metadata is stored in `.openworkspace/registry.sqlite3`. Commands accept explicit `--database` paths. If you initialize a custom path with `openworkspace init --path /some/path`, pass `/some/path/runtime.sqlite3` to identity, task, message, resource, and package commands, and `/some/path/registry.sqlite3` to capability registry commands.

SQLite may create `-wal` and `-shm` sidecar files while a database is active. Do not copy only the main database file while the application is running. Use SQLite's backup facilities or stop all writers and preserve the complete workspace.

Evidence journals are user-selected JSONL files and are created when the first event is appended. Include them in backup/retention planning when needed. The project does not yet ship a complete backup/restore command or native cloud connector. See the [storage and backup guide](../storage/README.md).

## Offline installation

An offline installation bundle is not published. A user may prepare a wheelhouse on a trusted connected machine, transfer it through an approved process, and install with pip's `--no-index --find-links` options. Verify dependency provenance and hashes before use.

## Removal

Deactivate the virtual environment and remove the cloned source directory and environment. Registry databases, runtime databases, encrypted key files, and evidence journals are user data and are not automatically removed. Preserve or securely dispose of them according to your retention needs.
