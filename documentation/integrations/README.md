# Integration Handbook

No native external integration is currently shipped or executed by the 0.1 core. The storage guide documents optional external transfer tools that users may operate independently; those are not OpenWorkSpace-managed connectors.

## Integration categories

- **Reference:** links to official documentation and catalogs. No connection or execution.
- **User-managed external tool:** an independently installed application such as rclone or a vendor sync client. The user configures credentials and operates it outside OpenWorkSpace.
- **Local adapter:** a future reviewed connector to a locally installed application or filesystem.
- **Network adapter:** a future reviewed connector to a remote service, with explicit egress, authentication, scope, and data disclosure.
- **Protocol adapter:** a versioned implementation of a protocol such as MCP or A2A. Protocol support never grants broad access to the tools exposed by that protocol.

## Before proposing an integration

1. Identify a concrete user need and why an existing tool is preferable to a new implementation.
2. Locate the official publisher and canonical source.
3. Determine the license, redistribution rights, applicable terms, and current maintenance status.
4. Record version, maintainer, dependencies, supported platforms, and update policy.
5. Describe all data read, written, transmitted, and retained.
6. List permissions, filesystem paths, network destinations, devices, and credentials required.
7. Define timeouts, retries, idempotency, cancellation, and failure behavior.
8. Provide isolated test evidence and a removal/recovery procedure.
9. For storage providers, document encryption, versioning, retention, deletion behavior, integrity checks, and a tested restore path.

## Intake states

Discovered → staged → inspected → qualified → authorized → enabled → monitored → revoked/removed.

Each state must be explicit. A catalog listing or successful metadata inspection does not grant permission to execute.

## Integration proposal template

Use this template in a design issue or pull request:

- Name and stable ID:
- Publisher and official source:
- Version and maintenance status:
- License and redistribution rights:
- Purpose and alternatives considered:
- Platforms and dependencies:
- Inputs, outputs, and data classification:
- Required permissions and scope:
- Network destinations and authentication:
- Isolation and resource limits:
- Data retention and deletion behavior:
- Tests and evidence:
- Known limitations:
- Disable, revoke, uninstall, and recovery:

## Storage provider work

Google Drive, iCloud Drive, OneDrive, Dropbox, Nextcloud/WebDAV, S3-compatible storage, and local/NAS targets are adoption priorities, but no native provider connector is currently implemented. See the [storage and backup guide](../storage/README.md) for the provider matrix, safe interim workflow, and required backup acceptance criteria.
