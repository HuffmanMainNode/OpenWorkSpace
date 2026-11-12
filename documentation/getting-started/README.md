# Getting Started

OpenWorkSpace is a developer-oriented pre-alpha foundation. It validates declarative capability manifests, registers them in a local SQLite database, evaluates explicit permission decisions, and verifies a local evidence journal. It does not install or execute third-party capabilities.

## Requirements

- Python 3.11 or newer.
- Git.
- Internet access to obtain source and dependencies. Registry and CLI operations are local after installation.

## Install from source

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
.venv\\Scripts\\Activate.ps1
```

Install and test:

```bash
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
pytest
ruff check .
```

## Validate and register a capability

```bash
openworkspace validate-manifest examples/hello-capability.json
openworkspace register examples/hello-capability.json --database .openworkspace/registry.sqlite3
openworkspace list --database .openworkspace/registry.sqlite3
openworkspace show example.hello --database .openworkspace/registry.sqlite3
```

The registry stores declarative metadata. It does not download packages, launch processes, or execute capability code.

## Evaluate declared permissions

```bash
openworkspace evaluate example.hello --grant filesystem.read --database .openworkspace/registry.sqlite3
```

This command demonstrates the policy helper against grants explicitly supplied by the operator. It is an evaluation record, not an enforcement mechanism. It does not grant the capability access to the filesystem.

## Verify an evidence journal

Create one using the Python API:

```python
from openworkspace.evidence import append_event

append_event(
    "workspace-events.jsonl",
    event_type="example.completed",
    actor="local-user",
    subject="getting-started",
    result="success",
)
```

Then run:

```bash
openworkspace verify-evidence workspace-events.jsonl
```

Missing and empty journals fail verification. The journal is tamper-evident, not tamper-proof against a privileged local administrator. Concurrent writers are not yet supported.
