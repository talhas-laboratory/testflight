# ADR 0007: Establish a Concept Lab Formation Workspace

## Status

Accepted for v1 implementation — 2026-09-08

Authority: user direction in the Concept Lab planning conversation.

## Context

Testflight already has portable semantic primitives, isolated knowledge workspaces, bounded context
compilation, reasoning operators, provider-neutral workflows, and a product workspace that owns
accepted product definition and decisions. It lacks a durable place to develop abstract theories
from conversations and knowledge, translate them into technical proposals, and trace a technical
proposal back to the theory and source material that formed it.

Without a separate boundary, speculative theory could be mistaken for accepted product truth,
brand/customer facts could cross into product definition without authority, or Codex-specific
instructions could become an unversioned store of domain knowledge.

## Decision

Create a sovereign, provider-neutral Concept Lab workspace and a repo-local `concept-lab` Codex
skill.

The workspace owns source-anchored conceptual interpretation, theory branches, formation history,
and reverse traces. It begins with a `relational-content` proof child. The skill owns only
activation, specialized language, mode routing, and progressive instruction loading; it does not
own evolving theory or persistent runtime state.

The Lab supports five explicit modes:

1. explore;
2. distill source material into concept fragments;
3. formalize fragments into theory branches and relations;
4. form a selected theory into an ontology, traversal, agent-composition, workflow, schema, or
   technical-language proposal;
5. trace a technical proposal back through its formal and theoretical derivation to source anchors.

Concept Lab and Testflight Product remain sovereign. Testflight Product owns product capabilities,
architecture, research, user-facing experience, and acceptance decisions. The Lab and Product
exchange immutable inquiry and formation packets through explicit source-bearing bridges. Bridge
registration is not traversal permission; cross-workspace traversal remains disabled unless a
separate grant authorizes it.

Every formation packet is proposal-only and must declare `canonical_write: false`. A human with
appropriate authority must explicitly promote a packet into an owning Product module, even after
automated evaluation passes.

## Semantic planes

The implementation must preserve these distinct planes:

```text
source material
  -> interpretation
  -> theoretical branch
  -> formal proposal
  -> technical projection
  -> accepted product state
  -> runtime execution
```

No transition implies acceptance, persistence, publication, execution, or authority. Reverse
tracing must report a missing link rather than invent an explanatory path.

## Consequences

- Add a small Concept Lab domain contract, a canonical workspace, four portable transformational
  operators, a narrow Product bridge, deterministic fixtures, and the repo-local Codex skill.
- Reuse existing Evidence, Context, WorldBranch, Derivation, AuthorityGrant, ContentUnit,
  KnowledgeContainer, and FederationBridge primitives rather than duplicate them.
- Use the Biotic relational-content strategy as a proof case only. It remains founder-directed
  strategy and does not become customer evidence, scientific truth, or universal ontology.
- Keep v1 repository-native: no UI, model provider, database, live Cognee population, persistent
  enter/exit runtime, external workflow endpoint, or automatic Product mutation.

## Rejected alternatives

### Put the Lab inside Testflight Product

Rejected because speculative theory needs a different source authority, lifecycle, and retrieval
boundary from accepted product records.

### Encode the Lab as a large Codex prompt or skill only

Rejected because versioned discussion-derived knowledge, branches, and derivations would become
opaque and would not be safely retrievable or reviewable.

### Share one mutable graph across Lab and Product

Rejected because reachability would blur permission, theories could silently become product facts,
and each workspace would lose an independent lifecycle.

### Build a UI or executable agent runtime first

Rejected because the v1 contracts, transformations, and proof case can be validated without adding
provider or operational complexity.

## Related artifacts

- `docs/plans/2026-09-08-concept-lab-v1-implementation-plan.md`
- `docs/workboards/concept-lab-v1/`
- `reasoning/README.md`
- `packages/testflight-semantic/src/testflight_semantic/federation.py`
- `workspaces/testflight-product/AGENT_INDEX.md`
