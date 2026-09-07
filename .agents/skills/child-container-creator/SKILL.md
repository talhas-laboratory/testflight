---
name: child-container-creator
description: Create and register an isolated child knowledge container when a domain needs distinct retrieval, permissions, versioning, evidence, or refresh behavior. Use for parent/child workspace topology and Cognee-ready projections; do not use for an ordinary content folder.
---

# Child Container Creator

Create a provider-neutral canonical child container first, then prepare its rebuildable retrieval
projection. Never make generated `.data/` state the source of truth.

## Decide whether a child is warranted

Create a child only when the knowledge has at least one materially distinct boundary: retrieval
route, permission set, update lifecycle, versioning model, evidence policy, or sufficient volume to
harm parent precision. Otherwise keep the content in the parent.

## Modes

- **Scaffold:** create the canonical child pack and parent registration plan. This is the default.
- **Populate:** add evidence-bearing source records and build a staging projection. Read
  [references/contract.md](references/contract.md) before populating.
- **Certify:** run structural, invariant, semantic, retrieval, adversarial, and no-hit checks before
  production exposure. Read [references/contract.md](references/contract.md).

## Workflow

1. Inspect the parent `AGENT_INDEX.md`, `AGENT_CONFIG.yaml`, `WORKSPACE.yaml`, and resource
   registry. Preserve its identity, metadata vocabulary, and source-of-truth policy.
2. Define the child's mission, included intents, exclusions, parent ID, child ID, explicit staging
   dataset, retrieval route, source authority, refresh cadence, and quality gates.
3. Dry-run the deterministic scaffold helper. Use an absolute parent path:

   ```bash
   python3 scripts/scaffold_child_container.py \
     --parent-dir /absolute/path/to/parent \
     --slug visual-language \
     --label "Visual language" \
     --mission "Resolve versioned visual direction for bounded brand workflows" \
     --parent-workspace-id world://workspace/brand/example \
     --route visual-language
   ```

4. Inspect the reported target and required parent updates. Re-run with `--apply` only when the
   scope is correct. The helper refuses to overwrite an existing child.
5. Update the parent's topology and resource registry after inspecting their actual schemas. Do
   not let a generic script guess or rewrite the parent format.
6. Add canonical sources with the required metadata and provenance. Keep binary assets outside
   Cognee and reference them by stable URI and content hash.
7. Validate the child structurally:

   ```bash
   python3 scripts/validate_child_container.py /absolute/path/to/child
   ```

8. For retrieval, route child-first, use exact or BM25 first, use bounded same-child hybrid only
   for an in-domain lexical no-hit, and use graph traversal only for explicit path queries with at
   most two hops.
9. Treat `no_hit`, `partial`, `hold`, `branch`, and `ask` as valid. Retrieval supplies evidence;
   downstream reasoning interprets it.
10. Run `--certify` only after sources and all probe classes exist. Populate or mutate a live
    external store only when the user explicitly authorizes that action.

## Required invariants

- Bind every source, index, cache, receipt, and dataset to the child workspace ID.
- Use an isolated explicit staging dataset during construction.
- Preserve source URL, verification time, evidence tier, authority, scope, and valid time.
- Reject navigation/config documents as final answers for ordinary domain queries.
- Never broaden an out-of-domain no-hit into parent-wide semantic search.
- Report structural validity, invariants, semantic quality, retrieval quality, and usefulness
  separately.

When this repository's reasoning operators are available, apply
`configuration-runtime@1`, `workspace-isolation@1`, `retrieval-reasoning-conflation@1`, and
`evaluation-schema@1`, and record their evaluator outcomes in material persisted receipts.

