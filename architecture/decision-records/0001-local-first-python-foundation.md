# ADR 0001: Local-first Python foundation

- **Status:** Accepted for 0.1, revisitable
- **Date:** 2026-11-12

## Context

The project needs a small executable foundation that can be installed and tested locally without a hosted control plane. It must demonstrate strict contracts, explicit permission decisions, and inspectable evidence before attempting a broad plugin ecosystem.

## Decision

Use Python 3.11+ for the initial core and CLI. Use JSON Schema Draft 2020-12 for the first public capability manifest. Use SQLite or other persistent registry storage only when a concrete registry implementation is designed; no database is required by the current 0.1 code. Keep third-party code execution disabled.

## Consequences

The first implementation is accessible and easy to test, but it does not establish cross-language compatibility, OS-level isolation, or production security. A TypeScript consumer and additional platform qualification remain separate milestones.

## Revisit when

A second independent language implementation is ready, platform constraints are measured, or performance/security requirements demonstrate that the core runtime should change.
