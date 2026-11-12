# Compatibility Policy

Compatibility claims must identify exact versions, platforms, and test evidence.

## Contract versioning

- Contracts are versioned independently from the application release.
- Breaking changes require a new major contract version or a documented migration path.
- Additive fields must be introduced deliberately and consumers must define unknown-field behavior.
- The initial capability manifest is strict and rejects unknown fields.
- JSON Schema Draft 2020-12 is the initial schema dialect.

## Platform support

Python 3.11, 3.12, and 3.13 are the current CI test matrix on Ubuntu. This does not yet establish Windows or macOS support, nor does it establish compatibility with every Linux distribution.

## Cross-language support

A language SDK is not considered compatible until it passes the shared positive and negative contract fixtures. Independent implementations must agree on validation behavior for required fields, unknown fields, formats, enumerations, and version negotiation.

## Dependency policy

Dependencies must have a documented purpose, supported version range, license, maintenance status, and update plan. Lockfiles or reproducible build inputs should be added when distribution requirements justify them. Dependency upgrades require tests and review.

## Status vocabulary

- **Proposed:** idea only.
- **Specified:** interface and acceptance conditions documented.
- **Implemented:** code exists.
- **Tested:** relevant tests ran and passed.
- **Verified:** a defined verification procedure passed with reproducible evidence.
- **Limited:** works only within stated constraints.
- **Blocked:** unsafe or unreliable to deliver.
- **Deferred:** intentionally outside current scope.
- **Revoked:** prohibited from use.
