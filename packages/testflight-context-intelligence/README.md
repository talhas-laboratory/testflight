# Context intelligence engine

This package compiles a workflow-specific, evidence-grounded context packet for an agent. It has
no Cordis or Cognee imports. Runtime seams are the `IntelligenceModel` and `KnowledgeRetriever`
interfaces, so the same engine can later sit behind HTTP or MCP without changing its decisions or
packet contract.

The engine deliberately separates retrieval eligibility from semantic synthesis. A small
deterministic filter removes obvious boundary failures; the separately configured intelligence
model interprets and organizes the remaining evidence. It never writes to a knowledge store.

The package also provides a provider-neutral `JsonVisualLanguageResolver`. It composes immutable
visual-language revisions and reusable reference modules by explicit scope and valid time. Audience
segments are ordinary selectors within a brand workspace. The resolver returns typed partial,
needs-clarification, and no-hit outcomes, preserves gaps and rights, and never selects a version by
embedding similarity.

## Context Compiler v2

The v2 compiler owns `ContextRequestV2`, `RouteDefinition`, `SufficiencyPolicy`,
`RouteEvaluation`, immutable `ContextPacketV2`, and replayable `ContextRunTraceV2`. It traverses
foundation records before relations, evidence, and history, expanding only for a named
insufficiency. Its disclosure, compiler-stage, semantic-candidate, graph-edge, and graph-hop
budgets are independent, so changing search breadth cannot silently change reasoning depth.
Authority, lifecycle, branch,
perspective, context, valid-time, freshness, conflict, task-permission, and relation-family gates
produce explicit `ready`, `partial`, `no_hit`, `hold`, `stale`, or `unauthorized` results.

`decodeWorldV3WireBundle` is the strict provider-neutral wire boundary for canonical Python model JSON.
It converts snake_case transport fields to the TypeScript contracts while rejecting v1/v2,
malformed, unknown, or cross-scope records. The integration test reads the actual 56-record Biotic
public-research proposal and compiles a cited newsletter packet without writing to the World.

### Graph-guided V3 runtime

`WorldV3GraphContextRuntime` is the reusable runtime seam for the four-layer architecture:
canonical World truth, a rebuildable Cognee discovery projection, deterministic context policy, and
agent reasoning. It rejects unauthorized requests before any retrieval; pins one canonical accepted
snapshot root; lets a `WorldProjectionReader` return discovery candidates and labelled edges; then
hydrates and strictly decodes selected V3 records from the canonical World using that same root.
The existing compiler, rather than Cognee, applies lifecycle, evidence, conflict, disclosure, and
sufficiency gates.

The included Cognee process reader searches the typed V3 projection indexes directly and combines
those semantic candidates with its matching exact-graph manifest. It does not query generic
document chunks or ask an LLM to reinterpret canonical records. The staging dataset, World scope,
branch, lifecycle, and module scope are all checked on every candidate.

The manifest contributes only a bounded declared neighbourhood around semantic or explicit
record seeds. This makes semantic seeding and structural
expansion independently replaceable, and gives a no-hit query a useful exact-seed path without
turning the graph into an answer generator.

`canonical_relation` edges may nominate an explicit canonical relation record for hydration.
`canonical_reference`, `derived_similarity`, and `inferred_relation` edges may help navigation but
are never supplied as asserted World facts. Mixed or stale projection roots produce an explicit
`stale` packet and do not hydrate records. `SqliteProcessWorldV3SnapshotPin`,
`CogneeProcessWorldProjectionReader`, and `SqliteProcessWorldV3CanonicalHydrator` are optional
process adapters. They speak a small JSON process protocol, so Cognee and SQLite imports remain in
their owning Python adapters. Provider-neutral contracts and orchestration live in `runtime.ts`;
local transport implementations are isolated in `process-adapters.ts`.

The executable bridge for the Biotic newsletter workflow is
`scripts/compile-biotic-newsletter-world.mjs`. It has no provider dependency: it accepts an
objective on standard input, reads only the checked-in `public-research-v3` proposal branch, and
emits a bounded packet with the fixed newsletter principal, `world:read` grant, record IDs,
citations, trace, lifecycle status, omissions, and instructions. Run it through:

```bash
make biotic-newsletter-world-context
```

It is deliberately a read bridge, not a general write interface. The Python workflow handler
checks its workspace, branch, principal, and terminal status again before passing the packet to a
model-backed step.
