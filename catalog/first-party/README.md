# First-party project catalog

This directory is the OpenWorkSpace directory of public projects authored under the owner's three explicitly designated public GitHub accounts.

## Current snapshot

- **62 public, non-fork repositories** passed exact repository metadata checks in this snapshot.
- PCakes303: 33 candidates.
- HuffmanRepositories: 12 candidates.
- HuffmanMainNode: 17 candidates.
- No private repositories are included.
- Forks are excluded, even when publicly visible.
- No source code or archives are copied into OpenWorkSpace.

The snapshot was produced on 2026-11-12. GitHub search is not a definitive account inventory, and the counts do not exactly reconcile with previously stated account totals. The index records the results actually verified, not an assumption that search was exhaustive.

## How to read the index

`repositories.json` is the canonical machine-readable catalog. It contains repository links, source account, resource category, a cautious summary, license status, and review state.

- `metadata-reviewed` means public visibility and non-fork status were checked on the exact repository metadata endpoint. It does not mean the code was audited.
- `readme-reviewed` means the README was inspected for purpose and declared limitations. It does not mean the implementation was independently tested.
- `not-established` means no reliable SPDX license was established from repository metadata. Check the repository's actual license files and file-level notices.
- `not-reviewed` means a license identifier was surfaced but file-level provenance and redistribution rights have not been approved.
- `reference-only` means OpenWorkSpace links to the upstream source; it does not bundle or install it.
- `source_revision: null` means no immutable revision has yet been pinned for a release archive.

## Initial useful project families

| Family | Projects to evaluate first | OpenWorkSpace role |
|---|---|---|
| Agent safety and policy | Multi-Agent-Swarm-Guardrails, agent-policy-engine, agent-emergency-control | Optional reference contracts and local validators |
| Interoperability | Huffman-Protocol, Open-Intelligence-Exchange, Open-Agent-Compatibility, AIX Codecs | Protocol discovery, mappings, codecs, and conformance evidence |
| Swarm coordination | Open-Swarm, swarm-coordination, swarm-state-mesh | Optional coordination components, subject to isolation and persistence review |
| Evidence and defensive security | Huffman Cyber Observatory, OSINT Evidence Engine, Agent Audit & Provenance | Local integrity, defensive assessment, and provenance tools |
| Research and OSINT | OSINT Collection Framework, OSINT Source Registry, Curated Modern OSINT Tools | Review-gated research references, not unattended collection |
| Test corpora | Open-Agent Compatibility Fixtures, retry/idempotency and delegation fixtures | Offline test data and conformance exercises |

These are candidates, not approved integrations. OpenWorkSpace Core should remain small. Users can opt into tools individually and keep private local records in `local-resources/`.

## Approval path

1. Confirm exact upstream repository and pinned commit.
2. Inspect README, source tree, license files, copyright notices, dependency manifests, release state, and security policy.
3. Run static checks and tests in an isolated review environment.
4. Document data flows, network access, permissions, platform support, and known limitations.
5. Decide whether to link, provide a source install recipe, or distribute an archive.
6. Only approve archives when the license and file-level provenance explicitly permit redistribution.
7. Generate checksums, an SBOM, attribution notices, and a reproducible build record for any approved bundle.

No entry in this catalog authorizes downloading, installing, executing, or redistributing upstream code.
