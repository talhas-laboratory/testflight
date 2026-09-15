# Brand domain

This directory is the canonical, provider-neutral ontology and policy source for the Brand
system. It defines semantic types and relationship meanings; it does not contain Cognee
DataPoints, generated indexes, source evidence, or model output.

The first version keeps intended, expressed, experienced, reported, observed, inferred, and
hypothesized perspectives distinct. Relationship dimensions are stored separately from truth,
and aggregate traversal strength is disabled until a versioned policy is calibrated.

## Constitutional status

The controlling research and implementation design is the
[Brand Ontology Constitution v0.1](../../docs/plans/2026-08-20-brand-ontology-constitution-v0.1-design.md),
accepted by [ADR 0004](../../docs/decisions/0004-brand-ontology-constitution.md). It defines the
meta-model, classification rules, portfolio topology, representation and dependency architecture,
time, identity, authority, provenance, governance, and certification boundaries.

`ontology/brand-system.yaml` version 1.0.0 and `ontology-v2/` are legacy migration sources. They
are readable for audit and deterministic migration accounting only. Existing legacy consumers
remain read-only until their release is explicitly migrated; no *new v3* authoring, projection, or
runtime path may depend on them. Their definitions remain immutable: a replacement must retain,
deprecate, or replace them with new IDs through an explicit migration rather than silently changing
their meaning.

`ontology-v3/` is the candidate next release. It defines eight modular domains over the shared
World record grammar: Entity, State, Event, Relation, Claim, Source, Evidence, Decision, Context,
Derivation, Authority, Version, Branch, and Dependency. Its `eight-systems` manifest is a
read-oriented navigation projection—not the canonical grammar—so Experience and Perception retain
their semantic form as relationship frames and scoped claims rather than becoming ambiguous top-
level record types. Candidate does not mean accepted: changes pass through explicit proposal,
approval, rejection, and history contracts before they become canonical records.

Before a legacy workspace is migrated, run
`uv run --package testflight-brand python scripts/inventory_legacy_brand_workspace.py <workspace>`.
It emits a hash-bound, machine-readable inventory of the workspace records, fields, endpoints,
evidence/context references, source artifacts, and repository consumers. It does not write or
transform legacy content.

Ten vocabulary and evaluation clusters remain research-driven, and the physical encoding of the
shared Context contract is provisional until its fixture gate passes. Do not ingest a real Brand
corpus into canonical state until the constitutional schema and ontology certification gates are
met.
