# ADR 0003: Keep Brand semantics canonical and project to Cognee

## Status

Accepted — 2026-08-19

## Decision

Represent the system-theoretic Brand model in provider-neutral packages and versioned YAML
ontology/policy files. Persist immutable evidence and accepted assertions in the append-oriented
SQLite semantic adapter. Treat Cognee as a rebuildable projection: assertion nodes retain evidence
and provenance, while optional direct graph edges retain relationship metadata for bounded
traversal.

Definitions, mentions, occurrences, canonical components, assertions, state snapshots, and
provider records remain distinct. Intended, expressed, experienced, reported, observed, inferred,
and hypothesized perspectives are not merged. Relationship dimensions (structural weight,
evidence confidence, source authority, salience, and valence) remain separate from truth and are
not aggregated unless an explicitly versioned policy enables it.

## Consequences

- Cognee can be replaced or rebuilt without losing canonical evidence or accepted semantics.
- The same semantic core can feed Cognee, another graph/vector backend, LangGraph, or DeepSeek
  Harness adapters.
- Projection and retrieval work is more explicit because it must resolve back to canonical IDs and
  evidence spans.
- A later projection can be cut over side-by-side after certification; generated `.data` files and
  SQLite databases stay outside Git.

## Rejected alternative

A Cognee-first custom graph was rejected as the canonical model because it would couple ontology,
evidence lifecycle, acceptance policy, and provider storage too early.
