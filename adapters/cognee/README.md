# Cognee adapter

This boundary translates Testflight semantic occurrences into Cognee's graph and memory APIs.
The upstream dependency is optional and loaded lazily so unrelated experiments do not pay its
installation or startup cost.

Install it with `uv sync --all-packages --extra cognee`.

## Entity and relationship environment

The portable semantic layer is configured with `EntityDefinition` and
`RelationshipDefinition` objects. An LLM returns the strict `ExtractionResult` contract; the
validator then requires every entity and relationship quote to appear verbatim in the source,
computes offsets, preserves `source_id`, and assigns stable UUIDs from provenance. Repeated
mentions remain occurrence-level records for now.

```python
from testflight_adapter_cognee import (
    EntityDefinition,
    EntityMatch,
    ExtractionResult,
    MatchType,
    RelationshipDefinition,
    validate_extraction,
    validation_to_datapoints,
)

definition = EntityDefinition(
    name="Idea",
    definition="A distinct proposal or design direction.",
    relationships=(
        RelationshipDefinition(
            name="supports",
            source_entity="Idea",
            target_entity="Idea",
            definition="The source supports the target with rationale or evidence.",
        ),
    ),
)
validated = validate_extraction(
    "A graph is a durable memory layer.",
    definition,
    ExtractionResult(
        matches=[
            EntityMatch(
                quote="graph",
                normalized_content="graph",
                match_type=MatchType.EXPLICIT,
            )
        ]
    ),
    source_id="design-note-1",
)
data_points = validation_to_datapoints(validated)
```

`validation_to_datapoints` and `relationship_custom_edges` are the Cognee-specific persistence
boundary. They are intentionally separate from extraction so a different graph backend can be
added without changing the semantic contract. Relationship records keep evidence as retrievable
nodes; direct endpoint edges can be passed as Cognee `custom_edges` when writing the batch.

### Brand projection

The system-theoretic Brand domain has a separate projection boundary in
`testflight_adapter_cognee.brand_projection`. It defines lazy Cognee DataPoint classes for a
Brand system, Brand components, and first-class Brand assertions. Assertions are projected only
after canonical acceptance. Keep assertion nodes for evidence and provenance, and use
`brand_assertion_custom_edges` only for bounded endpoint traversal; the edge metadata retains
perspective, epistemic status, evidence confidence, and structural weight as separate dimensions.
The canonical ontology and policies live under `domains/brand/`, while accepted evidence and
assertions live in the SQLite semantic repository.
