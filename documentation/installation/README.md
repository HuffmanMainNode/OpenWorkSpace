# Installation Guide

## Supported baseline

The CI pipeline currently tests Python 3.11, 3.12, and 3.13 on Ubuntu. Other operating systems are not yet release-qualified.

## Editable developer installation

```bash
git clone https://github.com/HuffmanMainNode/OpenWorkSpace.git
cd OpenWorkSpace
python -m venv .venv
# Activate the environment for your shell.
python -m pip install -e '.[dev]'
```

## Verify installation

```bash
python -c "import openworkspace; print(openworkspace.__version__)"
openworkspace --help
pytest
ruff check .
```

## Offline installation

An offline installation bundle is not yet published. A user may prepare a wheelhouse on a trusted connected machine, transfer it through an approved process, and install with pip's `--no-index --find-links` options. Dependency hashes and provenance should be verified before use. This project does not yet publish a reproducible offline bundle.

## Removal

For an editable source installation, deactivate the virtual environment and remove the cloned directory and virtual environment. Do not delete user-created evidence journals or data unless you have separately verified their location and retention requirements.
