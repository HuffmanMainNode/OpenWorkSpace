# Getting Started

OpenWorkSpace is currently a developer-oriented pre-alpha foundation. The working 0.1 features validate a declarative capability manifest, evaluate explicit permission grants, and verify a local hash-linked evidence journal. It does not yet install or execute third-party capabilities.

## Requirements

- Python 3.11 or newer.
- Git.
- Internet access only to obtain the source and development dependencies. The CLI operations themselves are local.

## From a source checkout

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

Install and test:

```bash
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
pytest
ruff check .
```

## Try the examples

```bash
openworkspace validate-manifest examples/hello-capability.json
```

To verify a journal, first create one using the Python API:

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

The journal is tamper-evident, not tamper-proof against a privileged local administrator. See the security guide before using it for sensitive workloads.
