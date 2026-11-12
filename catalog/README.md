# Resource Catalog

The catalog is a directory of independently maintained resources that users may inspect and choose to use. It is not a package manager, plugin loader, execution service, or trust authority.

## Catalog boundaries

- **First-party:** projects published by the OpenWorkSpace maintainer's public accounts and verified as public, non-fork repositories before listing.
- **Community:** independently authored third-party projects reviewed for provenance, license, maintenance, compatibility, and security posture.
- **Packs:** optional curated groupings of catalog references. Packs do not silently install dependencies.
- **Local additions:** users may maintain private catalogs or local resource directories without submitting upstream.

## Resource lifecycle

`discovered -> inspected -> qualified -> approved -> available -> revalidated`

Alternative outcomes include `reference-only`, `deferred`, `rejected`, and `revoked`. Catalog presence does not imply code integration or permission to execute.

## Distribution modes

1. **Reference-only:** canonical upstream link and metadata.
2. **Metadata-only:** manifest and documentation, no upstream source copied.
3. **Source-link:** directs the user to the pinned upstream revision.
4. **Approved archive:** a reproducible source archive only after license and notice review, with pinned revision and SHA-256 checksum.

Direct upstream links are the default. Do not redistribute a project merely because its repository is public. No archive is allowed until license compatibility and redistribution conditions are confirmed.

## Machine-readable records

Catalog records use [the contribution schema](../specifications/contribution.schema.json). The root [workspace discovery descriptor](../openworkspace.json) points automated consumers to the primary machine-readable interfaces. These records are descriptive and never grant authority.

## Security and provenance

Every promoted record should preserve canonical repository URL, owner/publisher, immutable revision, SPDX license identifier, upstream notices, review state, review date, known limitations, and the reason for its distribution mode. Revalidate archived or installable resources when upstream revisions or advisories change.
