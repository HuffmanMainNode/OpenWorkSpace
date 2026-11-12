# Community and first-party resource contributions

OpenWorkSpace welcomes independent tools, adapters, schemas, datasets, documentation, test fixtures, and research resources. Contributions are optional additions. They must not make the core depend on a contributor's service or repository.

## Submission location

Create a directory:

```text
contributions/
  inbox/
    <contribution-id>/
      contribution.json
      README.md
      REVIEW-NOTES.md
```

Use a lowercase kebab-case ID, 3 to 64 characters. Copy the starting manifest from [templates/contribution.json](templates/contribution.json). Validate it against [the contribution schema](../specifications/contribution.schema.json).

The inbox is a proposal queue, not an approved catalog. Maintainers move approved records into the appropriate catalog only after review. A pull request does not imply acceptance.

## What to submit

- A concise explanation of the problem solved and intended users.
- Canonical public source repository and an immutable 40-character commit SHA when available.
- Publisher identity/profile and original author attribution.
- SPDX license identifier and redistribution status.
- Maturity, supported platforms, dependencies, and known limitations in README.md.
- Required permissions, network destinations, and whether the tool executes code.
- Reproducible test or verification evidence.
- A clear distinction between upstream functionality and OpenWorkSpace integration status.

## What not to submit

- Private repositories, private source, secrets, credentials, personal data, or proprietary material.
- Unlicensed or license-ambiguous source code for redistribution.
- Executable binaries, installers, archives, vendored dependencies, or opaque payloads in the initial intake proposal.
- Automatically running install scripts, post-install hooks, or code that changes the host system.
- Claims that a tool is safe, sandboxed, verified, or production-ready without reproducible evidence.

Initial submissions are metadata-first and link to upstream source. Do not place third-party source code in the inbox. A later, separately reviewed archive process may allow redistribution where the license permits it.

## Review lifecycle

```text
proposed -> triage -> source-and-license-review -> technical-review
         -> security-review -> qualification -> catalog-promotion
         -> periodic-revalidation
```

A proposal may instead be rejected, deferred, restricted to reference-only, or revoked. Discovery is not endorsement. A valid manifest is not a trust decision. Approval for catalog listing is not approval to execute.

## Maintainer review checklist

1. Confirm the repository is public and the submitted revision exists.
2. Confirm source ownership and author attribution without relying only on the submitter's claim.
3. Identify the exact SPDX license and inspect its terms and upstream notices.
4. Review maintenance, release history, dependencies, supported platforms, and open security advisories.
5. Inspect source and build/install behavior without executing untrusted code.
6. Identify network destinations, permissions, secrets, subprocesses, filesystem writes, and data handling.
7. Run appropriate static checks and tests in a controlled review environment.
8. Record test evidence, limitations, reviewer, date, and decision.
9. Choose reference-only, metadata-only, source-link, or approved-archive distribution.
10. Revalidate periodically and provide a revocation path.

## Pull request rules

- One resource per directory and preferably one resource per pull request.
- Keep changes inside `contributions/inbox/<id>/` unless maintainers request otherwise.
- Do not edit the core catalog, trust state, or release metadata in the same submission.
- Include no binary files or generated build output.
- Expect requested changes or rejection if provenance, licensing, or safety cannot be established.
- By submitting original work, contributors agree to the project's contribution terms in CONTRIBUTING.md. Third-party works remain under their own licenses.

## Local use

Anyone may clone OpenWorkSpace and maintain a private local catalog or local resource directory. Local additions do not need to be submitted upstream. Do not assume local catalog entries are trusted or executable.
