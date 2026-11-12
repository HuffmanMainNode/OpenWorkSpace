# Contract Specifications

The JSON files in this directory are normative schema drafts for the current public contract set. They use JSON Schema Draft 2020-12.

| File | Purpose | Runtime status |
|---|---|---|
| capability.schema.json | Declarative capability description | Implemented and validated by package |
| registry.schema.json | Local registry storage envelope | Schema published; SQLite rows validated by application logic |
| identity.schema.json | Principal identity metadata | Schema draft only |
| task.schema.json | Task envelope and retry metadata | Schema draft only |
| message.schema.json | Interoperable message envelope | Schema draft only |
| permission.schema.json | Permission decision record | Schema draft only |
| evidence.schema.json | Hash-linked evidence event | Implemented by evidence journal |
| resource.schema.json | Resource catalog metadata | Schema draft only |
| plugin-manifest.schema.json | External package metadata | Schema draft only; execution disabled |

## Compatibility rules

- Reject unknown fields unless a contract version explicitly documents extensibility.
- Do not silently reinterpret missing or unknown values.
- Treat timestamps as RFC 3339 date-time strings.
- Treat package metadata as untrusted input.
- A valid schema instance is not a security approval.
- Add shared positive and negative fixtures before publishing independent SDKs.

The identity, task, message, permission, resource, and package schemas are not yet backed by runtime services. The local SQLite registry stores validated capability metadata, but does not yet implement a portable registry interchange API.
