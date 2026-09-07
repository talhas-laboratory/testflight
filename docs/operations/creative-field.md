# Creative Field operations

The Creative Field is a project-scoped child projection over the canonical SQLite creative
records. Moodboard bytes remain in the content-addressed evidence store; the Creative Field
records, review decisions, bindings, packets and evaluations remain append-only canonical data.
Cognee is derived retrieval state and may always be discarded and rebuilt.

## Safe local workflow

Export the canonical project records as a JSON list of `{record_type, payload}` objects, then run a
credential-free dry-run:

```bash
uv run --all-packages python scripts/project_creative_field.py \
  --records-file /path/to/project-records.json \
  --child-workspace-id world://workspace/example/creative-field \
  --parent-workspace-id world://workspace/example \
  --project-id project:example \
  --dataset-name testflight_creative_field_example_staging \
  --dry-run
```

Rebuild a derived manifest atomically and compare it with the previous one for drift:

```bash
uv run --all-packages python scripts/project_creative_field.py ... \
  --rebuild /explicit/runtime/path/creative-field/manifest.json
```

The command rejects non-staging dataset names and cross-project records. It never edits the
canonical export or SQLite store. Generated manifests and Cognee state belong under `.data/` (or
the runtime root declared by the server workspace), not in Git.

## Cognee population

After the child pack and retrieval probes are certified, an explicitly authorized server job may
call `populate_creative_field_projection(...)` from the Cognee adapter. It uses incremental source
documents, retains the child/project/field/evidence/rights metadata, and runs only against an
isolated `*_staging` dataset. Switch an active dataset reference only after certification; never
promote Cognee output into canonical records.

## Routing and recovery

Resolve project, workspace, permissions, branch and valid time before retrieval. Route to this
child first, use exact ID lookup or lexical/BM25 retrieval, and use bounded same-child hybrid
retrieval only after an in-domain lexical no-hit. Graph traversal is reserved for explicit paths
and is limited to two hops. A no-hit, held proposal or rights failure is returned honestly.

To recover from projection drift or provider failure, keep the canonical SQLite records and blob
store, discard only the derived manifest/index, rebuild into a new staging dataset, run
`uv run --all-packages python scripts/certify_creative_field.py`, then promote the new derived reference. No
provider credentials or client material are required for the synthetic certification path.
