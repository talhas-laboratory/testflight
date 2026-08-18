# Reasoning-operator workspace design

## Decision

Create a repository-owned workspace pack at
`workspaces/reasoning-operators/` and project it into a dedicated Cognee
dataset named `testflight_reasoning_operators` on the home server.

The canonical operator contracts remain in `reasoning/operators/`. The
workspace does not copy or fork those YAML files. Its manifest references the
catalog, records the workspace policy/topology, and defines the metadata and
certification probes. A population command reads the canonical files,
materializes bounded documents with provenance, and performs an idempotent
Cognee add/cognify run. The server's `.data/cognee` remains ignored runtime
state and is never committed.

## Alternatives considered

1. **Tracked duplicate operator files in the workspace.** Easy to browse, but
   creates two sources of truth and makes drift likely. Rejected.
2. **Cognee-only workspace.** Fast to create, but not reproducible or
   reviewable from Git and loses the portable contract when the server is
   rebuilt. Rejected.
3. **Manifest-backed workspace plus Cognee projection.** Keeps contracts
   reviewable, lets agents use the files without Cognee, and makes the server
   dataset rebuildable. Recommended.

## Workspace contract

The workspace has:

- a stable `workspace_id` and dataset name;
- explicit mission, in-scope intents, and exclusions;
- a parent catalog with task-view children for selection, execution,
  evaluation, and maintenance;
- canonical source references and a metadata registry;
- deterministic retrieval policy: child-first, lexical/BM25 first, bounded
  hybrid only for in-domain lexical no-hit, graph traversal only for explicit
  path queries, and honest `NO_HITS`;
- proposal-only mutation and deny-unless-authorized action policy; and
- exact, intent, adversarial, and no-hit certification probes.

Every source record carries the container-population metadata contract:
`module`, `unit`, `task_view`, `tool`, `doc_type`, `evidence_tier`,
`experience_type`, `difficulty`, `canonical`, `last_verified_at`, and
`source_url`.

## Population flow

```text
reasoning/operators/*.yaml
  -> manifest and metadata validation
  -> bounded Cognee DataItems (operator id + source URL + workspace id)
  -> cognee.add(dataset_name=testflight_reasoning_operators)
  -> cognee.cognify(dataset)
  -> exact/intent/adversarial/no-hit smoke probes
```

The command supports `--dry-run` and `--validate-only`. It never prints
credential values. If a model/provider/embedding route is unavailable, the
workspace remains a valid tracked pack and the population status is held with
the diagnostic preserved; no semantic fallback is fabricated.

## Acceptance gates

- all 16 catalog operators resolve from the workspace manifest;
- metadata keys are present and non-empty for every source;
- canonical source hashes are recorded in the local population report;
- Cognee dataset creation is idempotent for the same operator/version/source
  identity;
- an exact operator lookup resolves to its source;
- an in-domain intent query routes to the operator task view;
- index/config documents are not accepted as final answers for semantic queries;
- an out-of-domain query returns `NO_HITS`; and
- `make check` passes before commit.

## Boundary

This workspace is a knowledge-container projection, not a new reasoning
runtime or Bridge behavior. Provider-specific extraction remains behind the
existing Cognee adapter. A later Bridge adapter may consume the same
`workspace_id`, operator ids, and provenance contract without changing the
canonical files.
