# Integration Model

OpenWorkSpace is an integration environment, not a replacement for the tools it connects. Integrations must remain optional, explicit, independently removable, and replaceable without making the local core depend on a vendor account.

## Integration classes

1. **Reference-only:** links to external documentation; no connection or execution.
2. **Manual adapter:** user invokes an independently installed tool outside the core.
3. **Local process adapter:** a declared local process interface with explicit permissions and resource limits.
4. **Network adapter:** a declared remote endpoint with explicit egress policy, authentication, timeouts, and data disclosure.
5. **Protocol adapter:** a versioned implementation of a published protocol such as MCP or A2A.
6. **Isolated capability:** executable package running only inside a separately qualified isolation boundary.
7. **Storage adapter:** a provider-neutral backup object interface implemented by optional filesystem, cloud-drive, WebDAV, SFTP, or object-storage backends.

## Minimum integration record

Every integration proposal must document:
- Stable integration ID and version.
- Publisher, canonical source, maintainer, and support status.
- License and redistribution constraints.
- Supported platforms and versions.
- Input and output data types.
- Required permissions and scope.
- Network destinations and data sent, if any.
- Authentication and secret-handling model.
- Dependencies and update mechanism.
- Failure modes, timeouts, retry behavior, and idempotency.
- Test evidence and known limitations.
- Disable, revoke, uninstall, and recovery procedures.

Storage adapters must additionally document:
- Client-side encryption and key recovery.
- Consistent SQLite snapshot behavior, including WAL handling.
- Object naming, versioning, retention, and deletion semantics.
- Integrity verification before and after transfer.
- Interrupted transfer and retry behavior.
- Restore to a new workspace without silent overwrite.
- Provider outages, account lockout, quota limits, and credential renewal.

## Safety rules

- No integration is trusted because it is popular or listed.
- No network connection is implicit.
- No secrets are copied into prompts or logs by default.
- Imported content is untrusted data, never authority to change policy.
- A protocol adapter does not confer permission to access every tool exposed by that protocol.
- Remote systems remain outside the local node's guaranteed control.
- A cloud sync folder is not automatically a safe backup target for a live SQLite workspace.
- Backup upload must be non-destructive by default; mirroring or deletion requires explicit user intent.
- Provider credentials and configuration remain outside the repository and normal workspace data.

## Current status

The 0.1 foundation has no integration runner, network connector, package installer, MCP server, A2A adapter, native cloud storage connector, or arbitrary plugin loader. External tools such as rclone may be operated manually by users, but they are not controlled, configured, or qualified by OpenWorkSpace. The current project also lacks a complete portable backup/restore format. See [Storage, Backup, and Long-Term Recovery](../documentation/storage/README.md).

These capabilities must be introduced separately with tests and explicit permission enforcement.
