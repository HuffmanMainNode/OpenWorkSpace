# Security Requirements

This document defines intended controls. A requirement marked planned or blocked is not an implemented safeguard.

| ID | Requirement | Initial status |
|---|---|---|
| SEC-001 | Default-deny permission decisions | Implemented primitive; not OS enforcement |
| SEC-002 | Discovery must not authorize execution | Design rule |
| SEC-003 | Reject malformed and unknown manifest fields | Implemented for capability schema |
| SEC-004 | Do not execute third-party plugin code | Enforced by absence of an execution feature |
| SEC-005 | Keep secrets out of ordinary logs and task payloads | Policy requirement; no secret subsystem |
| SEC-006 | Network access must be explicit and scoped | Planned |
| SEC-007 | Isolate untrusted execution at OS/WASI boundary before enabling it | Blocked |
| SEC-008 | Preserve failure evidence without hiding errors | Partial; journal primitive exists |
| SEC-009 | Provide verified backup and restore | Planned |
| SEC-010 | Support permission revocation and deny new operations | Planned |
| SEC-011 | Validate archive paths and resource limits before extraction | Planned; no package installer |
| SEC-012 | Protect against dependency substitution and confusion | Planned |
| SEC-013 | Verify release provenance and signed artifacts | Planned |
| SEC-014 | Keep local core useful without network access | Intended; end-to-end qualification pending |
| SEC-015 | Avoid telemetry export by default | No telemetry exporter implemented |

## Required security lifecycle

Discover → stage → inspect → qualify → authorize → execute within qualified boundary → monitor → revoke or remove.

Any missing stage blocks execution. A cryptographic signature establishes a relationship to a signing key; it does not establish that the software is safe. A hash establishes content identity; it does not establish publisher identity or benign behavior.

## Reference frameworks

The project may map controls to NIST SP 800-207 (zero trust), NIST SSDF, SLSA, OWASP supply-chain guidance, and SPDX. Mapping to a framework is not certification or proof of compliance.
