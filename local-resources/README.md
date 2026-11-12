# Local Resource Workspace

Use this directory for resource records and notes that belong to your local clone. It is intentionally separate from the public catalog and community contribution inbox.

## Local-only items

Place local resource metadata under `items/`:

```text
local-resources/
  README.md
  items/
    README.md
    my-tool.json
    my-reference.json
```

Use the resource record contract at `specifications/resource.schema.json`. These files are local working material. Git ignores new files in `items/` by default so private notes, internal paths, and local-only resources are not accidentally published.

## Registering a local record

The current CLI can register a resource record into the local SQLite catalog:

```bash
openworkspace resource-register local-resources/items/my-tool.json
openworkspace resource-list
```

Registration records metadata only. It does not download, install, authorize, or execute the referenced tool.

## Sharing a resource publicly

If you want to propose a resource for the shared OpenWorkSpace catalog, create a separate metadata-first proposal under `contributions/inbox/<contribution-id>/` and submit a pull request. Do not remove the local ignore rule or commit private local records. See `contributions/README.md`.

## Safety

- Do not store secrets, credentials, personal data, private source code, or proprietary material here.
- Treat every local record and linked project as untrusted until independently reviewed.
- Keep local-only records separate from public contribution proposals.
- A local trust-state field is metadata, not an OS permission or execution control.
