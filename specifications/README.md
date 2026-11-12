# Contract Specifications

The JSON files in this directory are normative schema drafts for the current public contract set. They use JSON Schema Draft 2020-12.

| File | Purpose | Runtime status |
|---|---|---|
| capability.schema.json | Declarative capability description | Implemented and validated by package |
| registry.schema.json | Local registry storage envelope | Schema published; SQLite rows validated by application logic |
| identity.schema.json | Principal identity metadata | Implemented as local metadata lifecycle; no authentication |
| task.schema.json | Task envelope and retry metadata | Implemented as local state store; no execution engine |
| message.schema.json | Interoperable message envelope | Implemented as local queue; no network transport |
| permission.schema.json | Permission decision record | Schema published; permission helper is not enforcement |
| evidence.schema.json | Hash-linked evidence event | Implemented by evidence journal |
| resource.schema.json | Resource catalog metadata | Schema draft only |
| plugin-manifest.schema.json | External package metadata | Schema draft only; execution disabled |
| contribution.schema.json | Metadata-first resource proposal | Implemented as intake contract; no installer |
| workspace-discovery.schema.json | Machine-readable project discovery descriptor | Implemented as repository metadata; not an authorization interface |

## Compatibility rules

- Reject unknown fields unless a contract version explicitly documents extensibility.
- Do not silently reinterpret missing or unknown values.
- Treat timestamps as RFC 3339 date-time strings.
- Treat package metadata as untrusted input.
- A valid schema instance is not a security approval.
- Add shared positive and negative fixtures before publishing independent SDKs.

Runtime implementations are intentionally narrower than the full product architecture. Identity records are not authenticated credentials. Task records are not executed. Local message queue records are not remotely transported and their sender identifiers are not cryptographically authenticated.
