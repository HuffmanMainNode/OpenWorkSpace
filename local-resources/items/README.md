# Local Resource Items

Add your own local resource metadata files here. This directory is ignored by Git except for this README, preventing accidental publication of local-only resource records.

Each JSON file should conform to `../../specifications/resource.schema.json`.

Nothing in this directory is automatically loaded or executed. Register a record explicitly with:

```bash
openworkspace resource-register local-resources/items/<resource-file>.json
```

To share a public resource with the project, submit a separate proposal under `contributions/inbox/`. Do not unignore or commit private records.
