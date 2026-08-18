# Semantic entity and relationship environment

Status: approved initial design

## Scope

This layer makes entity and relationship extraction a reusable environment rather than a
hard-coded classifier. It is the first semantic substrate for the Cognee adapter; consolidation,
temporal history, and ontology alignment remain later phases.

## Contracts

- `EntityDefinition` and `RelationshipDefinition` hold names, definitions, inclusion/exclusion
  rules, boundary and inference rules, and examples.
- `ExtractionResult` is the structured model returned by an LLM. An `EntityMatch` contains an
  exact quote, normalized content, match type, and optional confidence. A `RelationshipMatch`
  contains two endpoint quotes, a relationship type, and exact supporting evidence.
- `validate_extraction` is deterministic. It rejects unsupported or duplicate quotes, computes
  character offsets itself, preserves the caller's `source_id`, and derives stable UUIDs from
  provenance. LLM-provided offsets are not accepted.
- `EntityOccurrence` and `RelationshipOccurrence` preserve repeated mentions separately. This
  occurrence-first approach avoids premature merging and leaves room for later canonical entity
  and `EntityVersion` layers.

## Persistence boundary

`datapoints.py` is the only module that imports Cognee. It converts validated occurrences to
custom `DataPoint` subclasses and exposes optional `custom_edges` records for direct endpoint
edges. A relationship is also retained as an evidence-bearing node so retrieval can explain why
an edge exists.

## Extraction flow

1. Select a definition from configuration.
2. Compile the definition into a provider-neutral prompt.
3. Ask the configured structured-output provider for `ExtractionResult`.
4. Validate every quote against the original chunk and attach provenance.
5. Persist the resulting DataPoints and optional custom edges.

The extractor accepts a chunk's text and `source_id`; chunking and document identity remain
upstream concerns. This keeps the same contracts usable for Cognee's ingestion pipeline,
LangGraph nodes, or an offline test fixture.

## Deliberate limitations

The initial layer does not merge aliases, infer historical versions, or claim that a semantic
relationship is true beyond the supplied evidence. Those concerns require corpus-level evidence
and will be added as explicit downstream stages.
