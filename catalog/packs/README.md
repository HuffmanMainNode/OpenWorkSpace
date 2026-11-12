# Optional Resource Packs

These packs are **curated discovery lists**, not monolithic bundles or installation plans. They expose useful first-party projects while keeping OpenWorkSpace Core small and independent.

## Available discovery packs

| Pack | Purpose |
|---|---|
| Agent Safety and Trust | Policy, identity, delegation boundaries, emergency control, and portable safety contracts |
| Protocol and Interoperability | Protocol registries, message codecs, mappings, and conformance evidence |
| Evidence and Defensive Security | Local defensive assessment, provenance, integrity, and integration projects |
| Swarm Coordination | Task coordination, state models, and orchestration boundaries |
| Research and OSINT | Public-source research catalogs and policy-gated analysis scaffolds |
| Conformance and Test Corpora | Synthetic retry, delegation, metrics, memory, and evaluation fixtures |

The machine-readable source is `first-party-packs.json`, validated by `specifications/resource-packs.schema.json`.

## Safety and distribution policy

- Every item references a project ID in `catalog/first-party/repositories.json`.
- All items are reference-only. No code or archive is included.
- Pack inclusion is not a security endorsement, test certification, or legal approval.
- Every project remains individually optional.
- No automatic download, installation, permission grant, or execution occurs.
- License and file-level provenance review is required before any source archive is redistributed.
- Projects with unclear or mixed license status remain link-only.
- Review each upstream project's README, SECURITY policy, dependencies, platform support, and current release state before use.

Users can clone any linked public repository directly and evaluate it locally. OpenWorkSpace should not silently change upstream repositories or pin moving branches as if they were releases.
