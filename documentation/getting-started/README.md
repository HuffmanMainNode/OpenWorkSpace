# Getting Started

OpenWorkSpace is a developer-oriented pre-alpha foundation. It validates declarative capability manifests, maintains local identity metadata, stores tasks and their lifecycle, and provides a local message queue. It does not authenticate identity claims, execute tasks, or transport messages across a network.

## Requirements

- Python 3.11 or newer.
- Git.
- Internet access to obtain source and dependencies. Runtime database operations are local after installation.

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
.venv\Scripts\Activate.ps1
```

Install and test:

```bash
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
pytest
ruff check .
```

## Capability registry

```bash
openworkspace validate-manifest examples/hello-capability.json
openworkspace register examples/hello-capability.json --database .openworkspace/registry.sqlite3
openworkspace list --database .openworkspace/registry.sqlite3
openworkspace show example.hello --database .openworkspace/registry.sqlite3
openworkspace evaluate example.hello --grant filesystem.read --database .openworkspace/registry.sqlite3
```

The registry stores declarative metadata. It does not download packages, launch processes, or execute capability code. Permission evaluation is not OS enforcement.

## Local identity metadata

Use the synthetic identity fixtures:

```bash
openworkspace identity-create examples/contracts/identity.json
openworkspace identity-create examples/contracts/service-identity.json
openworkspace identity-show example.user.local
openworkspace identity-keygen example.user.local
# Passphrase is prompted securely and is never accepted as a command-line argument.
openworkspace identity-status example.user.local suspended --reason "Example lifecycle demonstration"
openworkspace identity-status example.user.local active --reason "Example reactivation"
```

Identity records are local metadata. The implementation can bind an encrypted local Ed25519 private key to a public key recorded in the identity metadata, then sign and verify files. The signature proves possession of that private key for the signed bytes, not a real-world identity or remote trust. The private key is encrypted with a passphrase and stored under `.openworkspace/keys`; POSIX permissions are restricted to the owner. Windows ACLs are not configured by this package.

Sign a file and verify it against the registered public key:

```bash
openworkspace identity-sign example.user.local ./document.bin
openworkspace identity-verify example.user.local ./document.bin BASE64_SIGNATURE
```

The signing command prints a base64 signature. Keep private keys and passphrases out of source control, logs, fixtures, and issue reports.

## Task lifecycle

The task fixture is owned by `example.user.local`, so create that identity first:

```bash
openworkspace task-create examples/contracts/task.json
openworkspace task-list
openworkspace task-show task.example.validation
openworkspace task-refresh-ready
openworkspace task-transition task.example.validation running --reason "Claimed for demonstration"
openworkspace task-transition task.example.validation succeeded --reason "Demonstration completed"
```

The store enforces declared state transitions, active local owner-record presence, dependency completion before readiness, and retry limits. It does not schedule workers, execute task code, authenticate the operator, or guarantee exactly-once work.

## Local message queue

The message fixture uses the example user and service identities. Create both first:

```bash
openworkspace message-send examples/contracts/message.json
openworkspace message-inbox example.local.core
openworkspace message-ack message.example.001 example.local.core
```

Messages are stored locally in SQLite. The queue checks that sender and recipient metadata records exist and are active, validates envelopes, rejects duplicate message IDs, and allows the declared recipient identifier to acknowledge a message. This is not sender authentication, authenticated recipient access, or network transport. Do not use it as a security boundary.

## Local resource catalog

Register and inspect the synthetic reference resource:

```bash
openworkspace resource-register examples/contracts/resource.json
openworkspace resource-list --search "Example reference"
openworkspace resource-show resource.example.manual
openworkspace resource-trust resource.example.manual inspected --reason "Metadata reviewed"
```

Resources begin as `uninspected`. Trust transitions must follow the defined lifecycle. The catalog records metadata only: it does not fetch source URLs, verify licenses, qualify code, or authorize execution.

## External package intake

The package fixture is metadata-only and uses a reserved example URL. To register a package, create a local artifact and generate a manifest whose `digest` matches its SHA-256:

```bash
openworkspace package-validate ./package-manifest.json
openworkspace package-verify ./package-manifest.json ./package-artifact.bin
openworkspace package-register ./package-manifest.json ./package-artifact.bin
openworkspace package-list
openworkspace package-show example.package 1.0.0
```

The intake verifies the local bytes and records metadata. It does not download the source URL, unpack archives, inspect package behavior, verify publisher signatures, install dependencies, or execute code. A matching digest proves byte consistency only.

## Evidence journal

Create an event with the Python API:

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

## Storage

The default runtime database is `.openworkspace/runtime.sqlite3`. Capability metadata uses `.openworkspace/registry.sqlite3` by default. Pass `--database` to select another local SQLite file. Back up databases while the application is stopped or use SQLite's supported backup facilities; copying only the main database file while WAL activity is ongoing may omit committed data.

All examples are synthetic. Do not put secrets, private user records, or production credentials into fixtures or logs.
