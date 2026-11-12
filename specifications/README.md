# Contract Specifications

The JSON files in this directory are normative schema documents for the current public contract drafts. They use JSON Schema Draft 2020-12.

## Contract index

| File | Purpose | Implementation status |
|---|---|---|
| capability.schema.json | Declarative capability description | Validator implemented |
| identity.schema.json | Principal identity metadata | Schema draft only |
| task.schema.json | Durable task envelope | Schema draft only |
| message.schema.json | Interoperable message envelope | Schema draft only |
| permission.schema.json | Permission decision record | Schema draft only |
| evidence.schema.json | Evidence event envelope | Schema draft only; current journal format differs |
| resource.schema.json | Catalog resource metadata | Schema draft only |
| plugin-manifest.schema.json | External package metadata | Schema draft only; execution disabled |

These are initial contract drafts, not a claim that corresponding runtime services exist. The current JSONL evidence journal is an internal prototype and does not yet conform to the published evidence event schema. A migration is required before claiming conformance.

## Compatibility rules

- Reject unknown fields unless a contract version explicitly documents extensibility.
- Do not silently reinterpret missing or unknown values.
- Treat timestamps as RFC 3339 date-time strings.
- Treat package metadata as untrusted input.
- A valid schema instance is not a security approval.
- Add shared positive and negative fixtures before publishing independent SDKs.
