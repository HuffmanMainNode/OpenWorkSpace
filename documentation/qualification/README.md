# Source qualification records

This directory documents evidence records for resources referenced by OpenWorkSpace.

- `../../catalog/first-party/source-qualification.json` is the machine-readable record.
- `../../specifications/source-qualification.schema.json` defines its strict structure.
- `first-party-source-review-2026-11-12.md` is the human-readable review report.

A record is a bounded snapshot, not a security certification. It records exact upstream commits, inspected files, license-file inspection, whether upstream code was executed, and known limitations.

`readme-reviewed` means documentation-level review. `source-sampled` means selected implementation/test files were inspected, not the complete source tree. `tests.executed=false` means upstream tests were not run. `reference-only` does not authorize import, installation, execution, or redistribution. CI enforces the record's consistency with the first-party catalog.
