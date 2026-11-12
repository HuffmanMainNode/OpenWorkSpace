# Installation Guide

## Supported baseline

The CI pipeline tests Python 3.11, 3.12, and 3.13 on Ubuntu. Windows and macOS are not yet release-qualified.

## Editable developer installation

```bash
git clone https://github.com/HuffmanMainNode/OpenWorkSpace.git
cd OpenWorkSpace
python -m venv .venv
python -m pip install -e '.[dev]'
```

Activate the environment using the instructions for your shell, then verify:

```bash
python -c "import openworkspace; print(openworkspace.__version__)"
openworkspace --help
pytest
ruff check .
```

## Local data locations

The CLI accepts an explicit SQLite registry path. A suggested project-local location is `.openworkspace/registry.sqlite3`. This is a convention, not an automatic global data directory. Back up the database while the application is closed or use SQLite's supported backup facilities. WAL sidecar files may exist while the database is active.

Evidence journals are user-selected JSONL files. Keep them separate from temporary build artifacts and include them in backup/retention planning when needed.

## Offline installation

An offline installation bundle is not published. A user may prepare a wheelhouse on a trusted connected machine, transfer it through an approved process, and install with pip's `--no-index --find-links` options. Verify dependency provenance and hashes before use.

## Removal

Deactivate the virtual environment and remove the cloned source directory and environment. Registry databases and evidence journals are user data and are not automatically removed. Preserve or securely dispose of them according to your retention needs.
