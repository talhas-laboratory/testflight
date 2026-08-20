# ADR 0004: Establish the Brand Ontology Constitution v0.1

## Status

Accepted for research and implementation planning — 2026-08-20  
Context physical encoding remains provisional.

## Context

The initial Brand prototype established a provider-neutral canonical model and a rebuildable Cognee
projection. Before populating it with real Brand knowledge, the project needs a stable language for
deciding what is an entity, assertion, event, context, definition, representation rule, dependency,
evidence record, or runtime state.

Without that constitution, early research terminology or model output could silently become the
ontology, and representation, dependency, identity, time, and provider concerns could be conflated.

## Decision

Adopt the detailed
[Brand Ontology Constitution v0.1](../plans/2026-08-20-brand-ontology-constitution-v0.1-design.md)
as the controlling design for ontology research and implementation planning.

The constitution:

- uses a small semantic kernel led by `SemanticEntity`, `Assertion`, `Event`, and `Context`;
- keeps evidence/observations epistemic and policies/rules/definitions in governance;
- treats `BrandSystem` as an analytical boundary and makes v0.1 portfolio-aware;
- makes Assertions canonical while permitting direct graph edges as derived projections;
- separates accepted truth from contextual applicability;
- uses generic representation bindings, profiles, facets, and manifestation rules;
- supports instance-, type-, and relation-derived dependencies with hybrid materialization;
- separates `DependencyRule`, `DependencyEdge`, and `StalenessMarker`;
- adopts scoped authority, universal derivation receipts, bitemporal resolution, immutable versions,
  and scenario branches; and
- certifies the ontology separately from Cognee or any other projection/retrieval implementation.

Forty of the original fifty decision clusters are provisionally settled. Ten remain explicitly
research-driven. The semantic role of Context is accepted, while the recommended immutable,
content-addressed physical representation must pass fixtures before becoming canonical.

## Consequences

- Ontology research can proceed without allowing literature terminology to redefine the kernel.
- The current `brand-system.yaml` 1.0.0 remains a prototype and migration source; it is not silently
  overwritten.
- More schemas and fixtures are required before real ingestion, especially for Context, authority,
  provenance, representation, dependencies, and bitemporal state.
- Cognee remains replaceable and rebuildable from canonical records.
- Models may propose and evaluate ontology changes but cannot promote them without scoped authority.
- Open or ambiguous outcomes remain first-class instead of being repaired with invented facts.

## Relationship to ADR 0003

This decision refines and extends ADR 0003. It does not replace the decision to keep Brand semantics
provider-neutral and project them into Cognee.

## Rejected alternatives

- Treating all research concepts as equal meta-model primitives was rejected because it conflates
  domain types, epistemic records, and governance objects.
- Encoding canonical facts only as graph edges was rejected because it loses n-ary context,
  evidence, perspective, time, and provenance.
- Coupling dependencies directly to relation definitions was rejected because semantic meaning and
  operational impact policy evolve independently.
- Using one score or status for representation compliance, freshness, conflict, and semantic
  preservation was rejected because those dimensions can disagree.

