# First run and safe demonstration

OpenWorkSpace provides two convenience commands for first-time users.

## Initialize a local workspace

From the repository root, run:

```bash
openworkspace init
```

This creates `.openworkspace/` with:
- `runtime.sqlite3` for local identity, task, message, resource, and package metadata.
- `registry.sqlite3` for capability manifests and registry audit metadata.
- `evidence.jsonl` as an initially empty local evidence journal.

Choose another directory with `openworkspace init --path ./my-workspace`.

Initialization is repeatable. Existing SQLite databases are initialized through each store's schema setup, and an existing evidence journal is never truncated or replaced. Back up important data before experimenting with development builds.

## Run the safe demonstration

```bash
openworkspace demo
```

The demo creates a temporary registry, evaluates a synthetic capability with one explicit grant and one missing grant, prints the decisions as JSON, and removes the temporary workspace when it exits.

The demo does **not** execute a capability, access the operating system on its behalf, or enforce filesystem/network restrictions. It demonstrates the current permission-decision primitive only. A denied decision is not proof that an operating-system operation was blocked.

## Existing commands

All existing commands remain available, including `validate-manifest`, `register`, `list`, `evaluate`, identity, task, message, resource, package, and evidence operations. Run `openworkspace --help` for the complete command list.
