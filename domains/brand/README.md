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

The current `ontology/brand-system.yaml` version 1.0.0 is a prototype and migration source. Its
definitions remain immutable: the researched ontology must retain, deprecate, or replace them with
new IDs through an explicit migration rather than silently changing their meaning.

Ten vocabulary and evaluation clusters remain research-driven, and the physical encoding of the
shared Context contract is provisional until its fixture gate passes. Do not ingest a real Brand
corpus into canonical state until the constitutional schema and ontology certification gates are
met.
