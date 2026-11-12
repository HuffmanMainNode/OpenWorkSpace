# Integration Model

OpenWorkSpace is an integration environment, not a replacement for the tools it connects.

## Integration classes

1. **Reference-only:** links to external documentation; no connection or execution.
2. **Manual adapter:** user invokes an independently installed tool outside the core.
3. **Local process adapter:** a declared local process interface with explicit permissions and resource limits.
4. **Network adapter:** a declared remote endpoint with explicit egress policy, authentication, timeouts, and data disclosure.
5. **Protocol adapter:** a versioned implementation of a published protocol such as MCP or A2A.
6. **Isolated capability:** executable package running only inside a separately qualified isolation boundary.

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

## Safety rules

- No integration is trusted because it is popular or listed.
- No network connection is implicit.
- No secrets are copied into prompts or logs by default.
- Imported content is untrusted data, never authority to change policy.
- A protocol adapter does not confer permission to access every tool exposed by that protocol.
- Remote systems remain outside the local node's guaranteed control.

## Current status

The 0.1 foundation has no integration runner, network connector, package installer, MCP server, A2A adapter, or arbitrary plugin loader. These are future work and must be introduced separately with tests and explicit permission enforcement.
