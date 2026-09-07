# Brand World to Artifact System

**Status:** Proposed product architecture  
**Date:** 2026-09-04  
**Scope:** Guided Brand ingestion, governed World population, version-resolved artifact creation,
delivery, and learning.

## Product goal

Give a founder or brand team a natural way to express what they know, preserve those inputs as
attributed evidence, turn reviewed knowledge into a living Brand World, and use the correct scoped
versions of that knowledge to create familiar marketing deliverables.

The product loop is:

```text
conversation + notes + documents + operational sources
  -> attributed evidence and content
  -> World proposals
  -> reviewed Brand World
  -> version-resolved artifact context
  -> artifact proposal
  -> evaluation and approval
  -> rendered/published deliverable
  -> observed outcome
  -> reviewable learning proposal
```

The customer buys useful artifacts and a faster, more reliable workflow. The World model,
reasoning operators, provenance, versioning, and governance are the infrastructure that makes the
artifacts dependable.

## Documents

| Document | Purpose |
| --- | --- |
| [System map](00-system-map.md) | Modules, connections, boundaries, and current implementation status |
| [Ingestion and elicitation](01-ingestion-and-elicitation.md) | Chat, notes, documents, extraction, follow-up questions, and ontology-gap handling |
| [World and context](02-world-and-context.md) | Canonical records, identity, revisions, branches, applicability, and frozen context manifests |
| [Artifact production](03-artifact-production.md) | Profiles, composers, evaluation, approval, canonical artifacts, and dependency tracking |
| [Delivery and learning](04-delivery-and-learning.md) | Rendering, publishing, measurement, outcomes, and controlled learning |
| [Build plan](05-build-plan.md) | Package topology, vertical slices, quality gates, operations, and enterprise hardening |
| [`module-catalog.yaml`](module-catalog.yaml) | Machine-readable module ownership, status, inputs, outputs, and dependencies |

## Core architectural position

Do not give a generation agent an unbounded list of entities. Compile an immutable context for one
artifact request. That context identifies the exact revisions, evidence, authority, assumptions,
conflicts, omissions, permissions, and Creative Field version that govern the artifact.

Do not use one "artifact adapter" for reasoning, generation, formatting, and publication. Preserve
four distinct boundaries:

1. **Artifact profile:** declares what the deliverable requires.
2. **Artifact composer:** produces a provider-neutral semantic proposal.
3. **Artifact renderer:** translates an approved version into a file or platform representation.
4. **Delivery adapter:** performs an authorized external action and records a receipt.

## Non-negotiable invariants

- Raw employee input is attributed evidence, not Brand truth.
- A textual mention is not automatically a canonical entity.
- Population of a Brand World is separate from extension of the shared ontology.
- Entity identity is stable; changing conditions live in immutable state or definition revisions.
- A branch represents an alternative interpretation or scenario, not ordinary revision history.
- "Latest" never means "applicable" or "most authoritative."
- Every material artifact field resolves to exact source and semantic records.
- Generated output remains a proposal until authorized review.
- Rendering cannot add strategy or unsupported claims.
- Performance correlation does not become causal learning without an explicit experiment policy.
- Canonical data remains provider-neutral; indexes and provider payloads are rebuildable projections.

## Recommended first commercial slice

```text
guided founder/brand-team interview
  -> reviewed Brand World seed
  -> campaign relationship frame
  -> approved campaign brief
  -> message matrix
  -> small social campaign pack
  -> evidence and creative evaluation
  -> PDF/HTML/image outputs
```

This is intentionally narrower than a universal marketing platform. It is sufficient to test
onboarding, knowledge quality, artifact usefulness, review speed, and willingness to pay.

