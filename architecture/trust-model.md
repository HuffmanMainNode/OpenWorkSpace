# Trust Model

Trust is contextual and revocable. No component is trusted solely because it is installed, locally available, signed, previously approved, or produced by an AI system.

- **Uninspected:** newly discovered or acquired; not eligible for execution.
- **Inspected:** metadata and contents reviewed; not an authorization.
- **Qualified:** defined tests passed within a stated environment and scope.
- **Authorized:** an identified authority granted specific permissions for a defined purpose.
- **Restricted:** use is limited by policy or known weakness.
- **Quarantined / Revoked:** new use is prohibited pending review or permanently withdrawn.

These states are not a simple quality ladder. Qualification does not imply authorization. A valid signature does not prove benign behavior. Missing evidence is unknown, not clean.

The 0.1 core validates metadata and evaluates explicit permission grants. It does not qualify or authorize external executable packages and does not run them.
