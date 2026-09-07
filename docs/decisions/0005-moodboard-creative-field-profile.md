# ADR 0005: Add the Moodboard / Creative Field Application Profile

## Status

Accepted for implementation planning and the first vertical slice — 2026-09-03

## Context

The Testflight repository already provides a provider-neutral semantic kernel, evidence envelopes,
context and branch records, derivation receipts, Brand ontology modules, bounded world-view
resolution, visual-language resolution, a local SQLite adapter, and rebuildable Cognee projections.

The approved Moodboard / Creative Field profile on the home server defines a multimodal creative
workspace, but the repository does not yet define how a board connects to Brand-world entities,
artifact workflows, or replaceable model providers.

Without an explicit boundary, implementation could accidentally:

- make a collage or embedding the semantic truth;
- copy Brand records into a second creative database;
- promote model interpretations without review;
- treat a visual-language profile as a complete multimodal field;
- send an entire board or client world to an external provider;
- let a target adapter rewrite canonical state.

## Decision

Implement Moodboard / Creative Field as a creative-domain application profile over the existing
Testflight kernel.

The profile has three linked objects:

```text
Moodboard       = project-scoped evidence-bearing curation surface
Creative Field  = reviewed, versioned semantic configuration derived from the board
Field Connector = task projection, target translation, invocation and evaluation boundary
```

The first-class lifecycle is:

```text
ReferenceAsset
  -> ReferenceObservationProposal
  -> ReferenceInterpretationProposal
  -> CreativeFieldProposal
  -> CreativeFieldVersion
  -> FieldProjection
  -> GenerationPacket
  -> CreativeOutput / CreativeEvaluation
```

All derived transitions are public, versioned handoffs. Model output is a proposal by default.
User review or an explicit authority grant is required before a Creative Field version becomes
active or a provider invocation occurs.

`CreativeProject` is the default scope. `ProjectBinding` connects it to a Brand workspace,
`FieldBinding` connects a field version to Brand/Product/Offering/Audience/Campaign/Channel/
Occasion entities, and `CreativeContextPacket` combines an exact `ResolvedWorldView` with a
target-neutral `FieldProjection` for an artifact workflow.

The canonical source is local evidence plus append-only events and semantic records. Runtime
assets/databases remain outside Git. SQLite is the first persistence adapter; Cognee, vector
indexes, thumbnails, packets and UI snapshots are rebuildable projections.

Operator contracts live in `reasoning/operators/creative-field/`. Client-specific operator packs
configure general transformations unless a procedure genuinely differs. Provider adapters expose
capabilities and redacted execution receipts; semantic interpretation has no deterministic fallback.

## Consequences

- `testflight-semantic` remains the shared kernel and does not absorb creative-domain meaning.
- `testflight-brand` remains the Brand ontology/binding source; field records reference it by ID.
- A new `testflight-creative-field` package owns creative records and deterministic lifecycle logic.
- A new provider-neutral operator runtime can serve Creative Field and later context workflows.
- `testflight-context-intelligence` composes world and field packets but does not form fields.
- Brand Lab remains read-only; a separate Creative Studio owns review commands and creative views.
- Each external disclosure is purpose-bound, permission-filtered and recorded.
- Audio/video support requires preprocessing or a capable provider; the first slice is image/text.

## Rejected alternatives

- A standalone Moodboard knowledge engine was rejected because it duplicates the semantic kernel.
- Extending only the existing visual-language resolver was rejected because the field includes
  temporal, rhetorical, symbolic, structural, interaction and other non-visual dimensions.
- Directly inserting board interpretations into Brand assertions was rejected because evidence,
  interpretation, reviewed state and operational context have different authority.
- One global taste profile was rejected because the strong product requirement is project scope.
- Selecting field versions by embedding similarity was rejected because governing versions require
  explicit scope, time, authority and precedence.

## Related decisions

- ADR 0001 — upstream integration policy.
- ADR 0003 — Brand canonical model and Cognee projection.
- ADR 0004 — Brand Ontology Constitution v0.1.
- `docs/plans/2026-09-03-moodboard-creative-field-implementation-plan.md`.
- Home-server design: `/home/talha/repos/mindscape/docs/product-profiles/moodboard-creative-field/architecture/SYSTEM_DESIGN.md`.
