# ADR 0008: Replace the active Brand World through a governed v3 migration

## Status

Accepted for phased implementation — 2026-09-14  
Authority: user:talha

## Context

The first Brand World prototypes proved that typed knowledge, evidence, relationships, and
progressive exploration are useful, but they also mixed ontology, navigation systems, dossiers,
and application projections. The resulting model was difficult for an agent to traverse without
receiving either too little grounding or an undifferentiated collection of records.

The extracted ideal-system conversation and the Biotic case study require a more general platform:
an FDE can construct a detailed, approved Brand world for any client; a context compiler can expose
only the task-relevant portion; and specialist agents can reason without treating projection labels,
model output, or public observations as accepted Brand commitments.

## Decision

Adopt the Brand World v3 modular migration design in
`docs/plans/2026-09-14-brand-world-v3-modular-migration-design.md`.

The implementation will:

- retain the provider-neutral semantic kernel and replace the active Brand organization through an
  evolutionary migration rather than an in-place patch or a greenfield rewrite;
- make v3 the only destination for new accepted Brand knowledge after cutover;
- keep v1/v2 readable only as explicit migration and audit inputs, with no active fallback or
  dual-write path;
- separate canonical semantic records from the eight-system navigation projection;
- compose Brand meaning from independently versioned modules over the shared World grammar;
- require explicit proposals, authority grants, and decisions for normative promotion;
- make routes, sufficiency evaluations, immutable context packets, and replay traces first-class;
  and
- use the Biotic newsletter as the golden vertical before broader application cutover.

This acceptance authorizes implementation of the architecture. It does not approve migrated Biotic
interpretations or client commitments. Those require their own scoped human review decisions.

## Consequences

- Active consumers must migrate to v3 contracts before legacy code can leave the dependency graph.
- Migration is measurable: every legacy object receives one disposition and retained lineage.
- The World service is the only promotion boundary; repositories cannot turn proposals into truth.
- Context compilation is read-only and fails explicitly on missing authority, stale evidence,
  unresolved conflict, or insufficient budget.
- The eight familiar systems remain useful in the interface but cannot own or change meaning.
- A second brand must run through the same grammar and compiler without shared-code changes before
  the platform is considered complete.

## Rejected alternatives

- **Patch v1/v2 in place:** rejected because mixed semantic levels and projection assumptions would
  remain active.
- **Greenfield rewrite:** rejected because it would discard tested evidence, authority, time,
  branch, dependency, and adapter contracts.
- **Permanent compatibility layer:** rejected because aliases and fallback reads would keep legacy
  semantics inside agent reasoning.

## Evidence and formation

- `docs/research/ideal-brand-system-conversation/01-ideal-system-substrate.md`
- `docs/research/ideal-brand-system-conversation/03-semantic-intelligence-architecture.md`
- `docs/research/ideal-brand-system-conversation/04-technical-and-agent-architecture.md`
- `docs/research/ideal-brand-system-conversation/08-current-vs-ideal-base-product.md`
- `docs/plans/2026-09-14-brand-world-grounding-dossier-design.md`

Formation operator: `world://operator/concept-lab/formation-projection@1`  
Guardrails: `world://operator/guardrail/boundary-conflation@1`,
`world://operator/guardrail/ontology-conflation@1`  
Evaluator result: accepted design formation; runtime phase gates remain independently verifiable.

## Context runtime cleanup verification — 2026-09-15

The compiler runtime now separates canonical resolution, projection discovery, process transport,
and orchestration; uses independent disclosure, compiler-stage, semantic-candidate, graph-edge,
and graph-hop budgets; filters projection candidates by dataset and World scope; and searches typed
V3 projection indexes rather than unrelated document chunks. The TypeScript World record contract
is a closed discriminated union matching the canonical Python models. The obsolete compatibility
compiler has been removed.

Operators applied:

- `world://operator/guardrail/boundary-conflation@1`: pass — projection candidates remain
  non-canonical until snapshot-pinned hydration.
- `world://operator/guardrail/retrieval-reasoning-conflation@1`: pass — retrieval returns bounded
  candidates and paths, not answers or asserted inferred edges.
- `world://operator/guardrail/configuration-runtime@1`: partial — configuration and budgets are
  explicit and locally tested; a configured live Cognee deployment is not certified by this check.
- `world://operator/guardrail/evaluation-schema@1`: pass for schema and invariant gates —
  `make check` passes with 257 Python tests and all TypeScript package tests.
