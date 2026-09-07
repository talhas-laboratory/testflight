# Testflight Product workspace design

**Status:** accepted for implementation  
**Date:** 2026-09-04

## Decision

Create a canonical, repository-tracked `Testflight Product` workspace with isolated child
containers for product definition, decisions, experience design, architecture, customers and
market, marketing and growth, finance and commercial concerns, and operations and governance.
The Git repository is the source of truth. Any search, graph, cache, or Cognee state is a
rebuildable projection and is never edited as canonical knowledge.

The product workspace describes Testflight itself. It is isolated from customer, brand, project,
and research workspaces. Cross-workspace use requires an explicit, provenance-bearing bridge.
Product design rules may govern how Testflight renders a customer workspace, but they do not
become evidence about that customer's brand.

## Architecture

The parent contains shared identity, ontology, module registration, routing, permissions,
evidence policy, and extension rules. A child exists only when its knowledge has a distinct
retrieval route, authority, evidence policy, privacy boundary, version lifecycle, refresh cadence,
or enough volume to degrade parent precision.

Every child contains `AGENT_INDEX.md`, `AGENT_CONFIG.yaml`, `WORKSPACE.yaml`, a source manifest,
resource registry, module contract, and certification probes. Retrieval routes to the smallest
child first, uses exact or BM25 lookup before bounded same-child hybrid search, and returns an
honest no-hit for unsupported questions. Graph traversal is reserved for explicit relationship
queries and is limited to two hops.

## Design-language enforcement

The experience-design child owns the semantic design contract. The code-consumable projection is
`packages/testflight-design-language`. User-facing implementations consume semantic tokens and
shared interaction rules from that package. Application-specific expression is permitted through
documented semantic aliases; unreviewed raw values or copied client-brand semantics are not.

The initial product character is **editorial intelligence with operational clarity**: calm,
evidence-forward, spatially composed, precise about state and authority, and restrained in motion
and decoration. Brand Intake may be warmer, Brand Lab denser, and Creative Studio more expressive,
while retaining the same hierarchy, status language, accessibility baseline, and interaction
grammar.

## Change lifecycle

Material additions begin as proposals with evidence, author, scope, and affected modules. An
authorized decision promotes a proposal to accepted state and records supersession rather than
overwriting history. Runtime projections are rebuilt from the accepted canonical revision.

Validation reports schema, invariants, semantic quality, usefulness, and unresolved risk
separately. Structural validity alone never certifies retrieval or product quality.

