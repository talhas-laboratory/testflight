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
Cognee's UUID-only `DataPoint.id` is derived deterministically from the workspace and canonical
semantic ID; the original IDs remain explicit fields and edge metadata. The canonical ontology
and policies live under `domains/brand/`, while accepted evidence and assertions live in the SQLite
semantic repository.

### World v3 exact graph projection

`testflight_adapter_cognee.world_v3_projection` is the canonical v3 graph seam. It maps every
current World record into a typed node and every declared reference into a typed edge. N-ary
relations and events remain relation/event nodes with participant-role edges; claims retain their
subject, object, perspective, evidence, opposing-evidence and contradiction links. Provenance,
authority, context, derivation, time, lifecycle and raw typed payload are retained as node data.

It is deterministic and never calls `cognify`: language-model extraction is inappropriate for an
exact ontology projection. Missing-but-declared targets become reference-only nodes so the graph
cannot silently lose a relationship.

Each typed projection node indexes only its deterministic label and semantic retrieval text. The
reader queries those V3 indexes directly, then enforces dataset, workspace, branch, lifecycle, and
module scope before returning candidate record IDs. Graph traversal has separate edge-count and
hop limits, and relation-family filters apply before canonical relation edges leave the adapter.
Dataset identity participates in node identity so two revisioned staging projections cannot
overwrite one another's unchanged nodes.

`WorldService.approve` writes the accepted history and one `world_projection_outbox` job in the
same SQLite transaction. `WorldV3ProjectionWorker` is the sole Cognee/Ladybug writer: it claims a
job, reconstructs the accepted branch snapshot, validates graph completeness, writes a revisioned
staging graph and manifest, then advances the branch's active projection head only after success.
Run one worker process with:

```bash
uv run python scripts/run_world_v3_projection_worker.py \
  --world-db .data/world.sqlite3
```

The Biotic public-research V3 bundle is still proposal-only. It can be rendered as a clearly
labelled preview with `lifecycle_scope=("proposed",)`, but it will not be automatically projected
by the approval outbox until authorised acceptance.

### Creative Field child projection

`testflight_adapter_cognee.creative_field_projection` provides the same boundary for the
project-scoped moodboard/Creative Field graph. `build_creative_field_projection` is pure and
deterministic: it hashes canonical records, emits namespaced IDs, source-bearing documents and
bounded relationship edges, and preserves project scope, field version, lifecycle, authority,
evidence and license rights. It requires an explicit `*_staging` dataset so the generated graph
cannot be mistaken for canonical state.

Use `scripts/project_creative_field.py` for credential-free dry-runs, drift checks and atomic
manifest rebuilds. `populate_creative_field_projection` is the explicit, separately authorized
Cognee population seam; it is intentionally not called by the dry-run or certification paths.
