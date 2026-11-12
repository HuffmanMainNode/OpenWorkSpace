# Storage, Backup, and Long-Term Recovery

## Current implementation status

**No cloud storage connector or complete backup/restore command is shipped in the current pre-alpha release.** The local stores are functional, but users must not interpret a provider appearing in this document as an integration that OpenWorkSpace itself has implemented or qualified.

Current local data may include:

- `.openworkspace/runtime.sqlite3`: identity metadata, task records, local message queue, resource catalog, and package metadata.
- `.openworkspace/registry.sqlite3`: capability registry metadata.
- `.openworkspace/keys/`: passphrase-encrypted Ed25519 private-key files. Losing these files or their passphrases can make signatures impossible to reproduce.
- User-selected JSONL evidence journals. They are not automatically stored under `.openworkspace` unless the user chooses that path.
- Any separately configured manifests, artifacts, local resources, or application data.

SQLite may create `-wal` and `-shm` sidecar files while a database is active. Copying only the main database file while it is active can produce an incomplete backup.

## Provider strategy

OpenWorkSpace should use a provider-neutral storage interface. The core should define backup objects, integrity metadata, retention intent, and restore verification. Provider-specific code should remain optional and independently removable.

| Provider / route | Practical integration route | Current OpenWorkSpace status |
|---|---|---|
| Google Drive | User-managed OAuth through rclone, or a future reviewed Drive API adapter | Not shipped or qualified |
| Apple iCloud Drive | Prefer a user-managed iCloud Drive sync folder where available. rclone also documents an iCloud backend, but it is an external community tool with Apple 2FA/session renewal requirements | Not shipped or qualified |
| Microsoft OneDrive | rclone or a user-managed OneDrive sync folder | Not shipped or qualified |
| Dropbox | rclone or a user-managed Dropbox sync folder | Not shipped or qualified |
| Nextcloud / ownCloud | WebDAV or rclone | Not shipped or qualified |
| S3-compatible object storage | rclone S3 backend, including compatible providers | Not shipped or qualified |
| NAS / removable media | Local filesystem, SMB, or SFTP tooling | Not shipped or qualified |

Provider support varies by backend and can change independently of OpenWorkSpace. Review the provider's current documentation, authentication requirements, API terms, and support status before entrusting it with long-term data.

## Sync storage versus cold archive

Consumer drive products such as Google Drive, iCloud Drive, OneDrive, and Dropbox are useful for convenient off-device copies and multi-device access. They should not automatically be treated as immutable cold storage. Account compromise, accidental deletion, sync propagation, provider retention rules, and account closure can affect every synchronized copy.

For long-term archival retention, consider a separate object-storage destination with versioning, lifecycle tiers, retention controls, or object-lock features where available. Understand retrieval latency, retrieval charges, minimum storage duration, lifecycle transitions, and deletion semantics before choosing a tier. Keep a separate recovery copy of encryption keys and credentials. A provider's durability claim is not a substitute for restore tests.

Useful upstream references:
- [rclone supported storage backends](https://rclone.org/docs/)
- [rclone Google Drive backend](https://rclone.org/drive/)
- [rclone iCloud Drive backend](https://rclone.org/iclouddrive/)
- [rclone crypt client-side encryption](https://rclone.org/crypt/)

The iCloud rclone backend is not an Apple-maintained OpenWorkSpace integration. Its documentation describes Apple ID authentication with two-factor verification and a time-limited trust token that requires renewal. Treat this as a separately installed third-party dependency, not as an official Apple API guarantee.

## Safe interim workflow

Until a native backup/export feature is implemented:

1. Stop OpenWorkSpace processes that may write to its SQLite databases.
2. Ensure each database has closed cleanly. Preserve the entire workspace directory, including any SQLite sidecar files that remain.
3. Include the separate evidence journals and the encrypted `keys` directory. Do not assume that backing up the two databases alone preserves the workspace.
4. Create a dated snapshot in a staging directory that is **not** the live workspace.
5. Encrypt the snapshot locally before uploading it to a provider. Do not upload raw identity key files, unencrypted databases, or evidence journals to a shared cloud folder.
6. Copy the encrypted snapshot to the destination. Prefer a non-destructive copy operation over a mirror/sync operation that may delete older destination files.
7. Verify the uploaded object against the local snapshot using a supported checksum or authenticated encryption verification.
8. Keep at least one independent offline or separately administered copy.
9. Periodically restore a copy into a new, empty directory and verify that the databases open and the encrypted identity keys can be decrypted.

Example only, after configuring and testing an encrypted rclone remote named `vault:`:

```bash
rclone copy ./encrypted-snapshots vault:OpenWorkSpace/snapshots
rclone check ./encrypted-snapshots vault:OpenWorkSpace/snapshots --one-way
```

Do not point a cloud sync client at the live `.openworkspace` directory. Do not use `rclone sync` as a default backup operation: mirroring can propagate deletions and mistakes. Confirm the meaning of every command and destination before running it.

### Encryption and credential handling

- Prefer client-side encryption before data leaves the device.
- If using rclone's `crypt` backend, protect the rclone configuration file. rclone documents that its default obscuring of the crypt password is not secure storage. Enable configuration encryption and keep recovery material offline.
- Keep OAuth tokens, service-account files, Apple credentials, and provider configuration outside the repository and outside issue reports.
- Never commit credentials or put them in manifests, prompts, logs, or ordinary task payloads.
- Loss of the encryption password or recovery material can make backups permanently unreadable. Maintain a tested recovery copy separate from the cloud account.
- Cloud sync is not the same as backup, and backup is not the same as archival retention.

## Required native backup acceptance criteria

A future OpenWorkSpace backup feature must not be called complete until it can:

1. Produce a consistent SQLite snapshot using SQLite's backup API or a documented quiescence procedure.
2. Include all configured runtime databases, key files, evidence journals, and an explicit inventory of excluded paths.
3. Encrypt data client-side before provider upload, using a reviewed authenticated encryption format and a memory-safe streaming design for large workspaces.
4. Record format version, creation time, source workspace identifier, file sizes, and cryptographic digests in a signed or authenticated manifest.
5. Reject path traversal, symlinks, unexpected file types, duplicate archive paths, truncated files, and oversized restore inputs.
6. Verify the entire backup before writing any restored data.
7. Restore only into a new or explicitly empty target by default. Never overwrite an existing workspace silently.
8. Verify restored SQLite integrity, evidence-chain validity where journals are present, and key decryptability without exposing private key material.
9. Support interrupted transfer, retry, duplicate upload, and provider-side version retention without silently deleting prior snapshots.
10. Include automated round-trip, corruption, wrong-passphrase, interrupted-write, path-traversal, and cross-platform tests.

## Roadmap

1. **Portable local backup format:** consistent SQLite snapshots, explicit file inventory, client-side encryption, integrity verification, safe restore.
2. **Filesystem storage adapter:** write and verify backup objects in a user-selected local or removable directory.
3. **External transfer adapter:** optional rclone integration using argument arrays, no shell interpolation, explicit remote allow-list, non-destructive copy by default, dry-run, and post-upload verification.
4. **Provider qualification:** test Google Drive, iCloud Drive, OneDrive, Dropbox, WebDAV/Nextcloud, and S3-compatible destinations independently. Publish backend-specific limitations and recovery steps.
5. **Retention and cold storage:** configurable retention, immutable/versioned destinations where supported, independent copies, and scheduled restore drills.

Until these milestones are implemented and tested, the supported statement is: **OpenWorkSpace stores its current metadata locally; cloud backup and long-term recovery remain user-managed external workflows.**
