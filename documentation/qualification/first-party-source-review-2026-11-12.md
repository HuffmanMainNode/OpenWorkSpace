# First-party source qualification: initial review

**Review date:** 2026-11-12  
**Scope:** public, non-fork repositories only, from the three owner-designated accounts  
**Target repository changed:** OpenWorkSpace only  
**Source repositories modified:** none

## Purpose and review boundary

This is an initial, evidence-backed source sampling pass. It is not a complete code audit, independent security assessment, reproducible-build assessment, or authorization to redistribute or execute any source. All reviewed projects remain reference-only. No code, archive, binary, dependency, credential, or private material was copied into OpenWorkSpace.

For each source, public visibility and `fork=false` were rechecked before reading repository contents. The catalog now pins the exact default-branch commit reviewed on this date. A pin identifies the snapshot; it does not imply approval.

## Results

| Project | Pinned source revision | Review performed | Preliminary assessment |
|---|---|---|---|
| [Multi-Agent-Swarm-Guardrails](https://github.com/HuffmanMainNode/Multi-Agent-Swarm-Guardrails) | `f4f42ad79678bc16b7a7539c0b6ed9c28b81f885` | README, Apache-2.0 LICENSE, NOTICE, packaging metadata, policy evaluator, policy tests | Strong reference candidate for deny-by-default policy contracts and conformance. The implementation explicitly does not authenticate principals, protect policy provenance, mediate OS side effects, or provide a sandbox. Optional TUF/SPIFFE features and experimental Linux broker require separate threat-model and dependency review. |
| [Huffman-Protocol](https://github.com/HuffmanMainNode/Huffman-Protocol) | `a360d60c2d2245cf6df4a1c2e7b0945299ccf676` | README, Apache-2.0 LICENSE, packaging metadata, offline validation module, validation tests | Strong reference candidate for schemas, manifests, registry validation, and declarative conformance. The README explicitly says H-PACK does not authenticate publishers, verify signatures, or rerun tests. No certification or universal compatibility guarantee. |
| [Open-Intelligence-Exchange](https://github.com/HuffmanMainNode/Open-Intelligence-Exchange) | `8062c55588cd4e811fd3bda280fde5866a4f469a` | README, MIT LICENSE, packaging metadata, identity implementation, secure transport implementation, protocol and secure-transport tests | High-value protocol reference, but security-sensitive. Review confirms Ed25519 identity/signature, X25519 key agreement, HKDF, ChaCha20-Poly1305, replay controls, and opt-in network transport are described and partly represented in tests. Private keys are stored unencrypted on disk with POSIX mode restrictions; Windows does not enforce those bits. Key custody, trust enrollment, certificate lifecycle, network exposure, and full transport threat model require deeper review. |
| [Huffman-Cyber-Observatory](https://github.com/HuffmanMainNode/Huffman-Cyber-Observatory) | `22614667f656334361f5d7785d80c92bda98de9f` | README, MIT LICENSE, packaging metadata, CLI entrypoint | Useful optional local defensive-tool reference. Network contact is explicit for CISA KEV and separately opt-in for OSV; filesystem secret scanning is described as local/redacted. Encryption buffers files and has a documented 64 MiB limit. This pass did not inspect all scanners, crypto, feed, SBOM, release, or workflow code, so it is not runtime-qualified. |
| [Huffman-Defensive-Intelligence](https://github.com/HuffmanMainNode/Huffman-Defensive-Intelligence) | `36a7e9b72c2a9e6885645add071544e3b17ebec3` | README, MIT LICENSE, packaging metadata, upstream integration contract | Useful architecture and adapter-contract reference. Documentation describes local event integration and approval boundaries, and explicitly disclaims WAN transport, distributed consensus, production PKI, and independent security audit. The adapter implementation and persistence code need further source-level review before any integration recipe is considered. |
| [Open-Agent-Compatibility-Fixtures](https://github.com/HuffmanRepositories/Open-Agent-Compatibility-Fixtures) | `948bd398ee10050c099852e87970aaf5d3977c9c` | README and MIT LICENSE | Synthetic fixture corpus, not a runtime or certification program. Useful as a linked test-data reference; individual fixture content and source-spec provenance remain to be reviewed. |
| [Open-Agent-Run-Metrics-Interop](https://github.com/HuffmanRepositories/Open-Agent-Run-Metrics-Interop) | `f9776a4172eb1a7c3fad5cd592ace252b1e26ad9` | README | Draft accounting/interoperability fixtures only. Not a pricing catalog, billing service, budget enforcer, or correctness/certification claim. License file and fixture provenance not yet reviewed. |
| [Agent-Delegation-Scope-Boundary-Fixtures](https://github.com/HuffmanRepositories/Agent-Delegation-Scope-Boundary-Fixtures) | `7ea4d9b01f6c3145e3002b7b88eb198744cba270` | README | Synthetic draft fixtures and simplified model only. Not an authorization protocol, identity system, production policy engine, or conformance proof. License file and fixture provenance not yet reviewed. |
| [Agent-Tool-Retry-Idempotency-Fixtures](https://github.com/HuffmanRepositories/Agent-Tool-Retry-Idempotency-Fixtures) | `e93332c3b37ea6e044795904924f4f07eb5f2c77` | README | Synthetic draft fixture corpus only. Explicitly does not claim exactly-once execution or provide a retry runtime. License file and fixture provenance not yet reviewed. |

## Integration decisions

1. Keep all nine entries **reference-only**. Do not bundle, install, import, or execute them through OpenWorkSpace.
2. Keep all redistribution approvals **not-approved**. A top-level license file is a necessary signal, not proof that every embedded fixture, standard excerpt, generated artifact, or dependency is distributable under that license.
3. Prioritize follow-up review of MASG and Huffman Protocol for schema and conformance cross-reference only. They have the clearest low-risk read-only integration boundary.
4. Treat OIX as a high-sensitivity optional protocol reference. Do not make it a default network service or auto-trust peer identities.
5. Treat HCO network commands as explicit opt-in operations. Do not invoke them during discovery or validation.
6. HDI remains an architecture/reference link until adapter and persistence code are reviewed.
7. Fixture repositories remain test-data references. Do not present draft fixture validation as implementation conformance.

## Follow-up work required before qualification

- Inspect complete source trees, all tests, workflow permissions, release workflows, dependency lockfiles, and security advisories.
- Inspect fixture files individually and verify source/version attribution, generated content, and license boundaries.
- Run tests only in a disposable, network-disabled environment after reviewing test code and dependencies. This initial pass did not execute upstream code.
- Perform static analysis and dependency vulnerability checks using pinned dependency sets.
- Review platform-specific file permissions, key storage, path handling, network destinations, TLS configuration, replay-state durability, and error handling.
- Record exact commands, environment, outputs, and limitations before changing any entry from source-sampled to a stronger qualification state.
- Only then consider integration adapters, and only with explicit user approval. Redistribution and execution require separate approvals.

## Evidence quality and limitations

The catalog's `source-sampled` state means selected source and test files were inspected. It does not mean the full source tree was reviewed or the project was tested locally. `license_review: reviewed` means the repository's top-level LICENSE text was read for that pinned snapshot; it is not a legal opinion or a complete provenance audit. The three fixture repositories whose LICENSE files were not read remain `not-established`.

Repository commit pins are immutable identifiers. Their associated branches may move. Recheck visibility, fork status, license files, and source revisions before future integration work.
