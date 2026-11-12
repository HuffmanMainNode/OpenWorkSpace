# OpenWorkSpace Data Pack

This directory contains small, version-controlled reference catalogs that define shared vocabulary for the project. The catalogs are descriptive data, not executable configuration and not permission grants.

## Catalogs

- `catalogs/permissions.json`: canonical permission identifiers, risk labels, and explanations.
- `catalogs/capability-domains.json`: broad capability categories.
- `catalogs/resource-types.json`: resource and package classifications.
- `catalogs/trust-states.json`: trust and qualification vocabulary.
- `catalogs/data-classification.json`: data sensitivity and handling defaults.
- `catalogs/lifecycle.json`: conceptual resource lifecycle states.
- `catalogs/protocol-candidates.json`: possible interoperability adapter targets, none shipped by this release.

## Fixtures

`../examples/contracts/` contains valid sample records for the published schemas. They are synthetic test data and contain no credentials, private datasets, or live service endpoints.

## Governance

Catalog changes that alter permission names, trust states, data classifications, or lifecycle transitions are compatibility-sensitive. Update the related schema, documentation, tests, and changelog together. Unknown values must not silently become trusted or allowed.

The permission catalog is the human-readable reference for permission identifiers. The capability schema currently contains the matching enum. A test checks that both remain aligned.
