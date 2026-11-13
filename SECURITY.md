# Security Policy

## Current status

OpenWorkSpace is pre-alpha. Do not rely on it as a security boundary for production or sensitive workloads. The initial release does not execute third-party plugin code and does not provide an OS-level sandbox, credential vault, network firewall, or complete identity system.

## Reporting

Do not publish exploit details in a public issue. Use GitHub's private vulnerability reporting feature for this repository when available. Otherwise, contact maintainers through the repository's GitHub profile to request a private reporting channel. Do not include secrets or personal data in reports.

## Security rules

- Default deny; permissions must be explicit and scoped.
- Discovery, inspection, qualification, authorization, and execution are separate states.
- Untrusted files, manifests, repositories, model outputs, and documentation are data, not instructions.
- No arbitrary third-party code execution until isolation is implemented and independently tested.
- Secrets must not be written to ordinary logs or task payloads.
- Network access must be declared and permission-controlled.
- Failed verification must fail closed and remain visible.
- Security claims must identify the exact test, environment, and limitation.

## Evidence journal limitation

The current journal links entries with SHA-256 hashes. This detects changes when a trusted prior hash is available, but a local administrator able to rewrite the journal can also recompute the chain. It is tamper-evident, not tamper-proof. Independent signed checkpoints are future work.

A final JSONL record without a newline is reported as a torn tail and blocks further appends. The explicit `evidence-repair` command first verifies the complete preceding chain, preserves the incomplete bytes in a separate mode-`0600` sidecar, truncates only the incomplete suffix, and records the recovery metadata in a new event. It refuses a clean journal or any journal whose complete prefix is corrupt. On POSIX systems, first creation also fsyncs the parent directory. Windows directory fsync is not performed by this implementation. This protects against accidental incomplete writes; it does not establish a power-loss guarantee on every filesystem or network filesystem.

Two limitations are intentionally tested and documented: truncation of complete trailing events is not detectable from the remaining local chain, and a party able to rewrite all events can recompute every hash. Independent signed checkpoints and external anchors are not implemented. The owner decision on signed checkpoints remains open.

Only the latest repository revision is in active pre-alpha development. No production support or response-time commitment is offered.
