# Brand World Explorer

## Decision

Build a local, read-only Explorer over canonical Brand workspace files. The
Explorer is a browser interface; it does not become the system of record and it
does not read Cognee's generated projection as its baseline.

## Boundaries

The server compiles `WORKSPACE.yaml`, inventory, relationship, context,
evidence, source, workflow, intelligence, and visual-language files into a
versioned JSON snapshot. The snapshot includes a deterministic source hash and
cross-reference diagnostics.

The user interface presents these distinct states:

1. Canonical stored knowledge.
2. Deterministically planned context.
3. Live retrieval results, only when a Cognee adapter is connected.
4. Agent packet and later generation trace, only when they exist.

The initial implementation provides (1) and (2), and explicitly reports live
retrieval as unavailable rather than fabricating a result.

## First release

- Brand map grouped by ontology type, with search, context and perspective
  filters.
- Exact entity inspector: stored record, scope, evidence, sources,
  relationships, limitations and held hypotheses.
- Visual-language profile/revision/reference browser.
- Agent View: a deterministic workflow simulation with planned entities,
  missing inputs, agent instructions and an honest retrieval boundary.

## Future adapters

Cognee and the context-intelligence runtime attach through dedicated read-only
adapters. They return source anchors, ranking/exclusion rationale, trace IDs
and status. They must never overwrite a canonical entity or be displayed as if
they were canonical knowledge.

## Validation

The compiler verifies that entity, relationship, evidence, source, context and
visual-reference links resolve. User-facing diagnostics remain visible. Tests
separately cover snapshot structure, reference integrity, deterministic planning
and no-live-retrieval behavior.

## Reasoning record

- `world://operator/guardrail/retrieval-reasoning-conflation@1`: planned,
  retrieved and used context remain separately represented.
- `world://operator/guardrail/evaluation-schema@1`: schema/reference integrity
  and usefulness of the UI are tested as separate dimensions.
