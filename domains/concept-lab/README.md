# Concept Lab domain

This directory is the provider-neutral contract source for Concept Lab v1. It defines the smallest
set of records needed to turn bounded source material into explicit conceptual proposals, and to
trace a proposal back to its source anchors. It does not implement a model, store, retrieval path,
workflow, UI, or authority to change another workspace.

Concept Lab records remain speculative unless their own lifecycle says otherwise. In particular, a
theory branch is not a customer fact, a scientific claim, an accepted product decision, or runtime
instruction. The Biotic relational-content case is a proof case, not a universal ontology.

## Contract boundary

The domain composes, rather than redefines, these owned primitives:

| Primitive | Owning contract | Concept Lab use |
| --- | --- | --- |
| Evidence, Context, WorldBranch, Derivation, AuthorityGrant | `packages/testflight-semantic` | stable source, scope, branch, lineage, and authority references |
| ContentUnit | `packages/testflight-content` | normalized source-material reference when available |
| KnowledgeContainer, FederationBridge | `packages/testflight-semantic/federation.py` | later workspace and guarded bridge composition |

See [manifest.yaml](manifest.yaml), [vocabulary.yaml](vocabulary.yaml), and
[contracts.yaml](contracts.yaml). ADR 0007 and the controlling implementation plan establish the
ownership and safety boundary.

## Semantic route

```text
source anchor -> ConceptFragment -> ConceptDefinition / ConceptRelation -> TheoryBranch
  -> FormationPacket -> proposed technical artifact
  <- ReverseTrace <- TransformationRun and Derivation references
```

Each arrow is a new, revisioned proposal record. It does not imply truth, acceptance, persistence,
publication, traversal permission, or execution.
