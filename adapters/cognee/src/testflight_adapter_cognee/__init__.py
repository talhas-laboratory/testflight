"""Cognee adapter with lazy upstream loading."""

from importlib.util import find_spec

from testflight_core import AdapterDescriptor, Capability, HealthReport, HealthState

from .brand_projection import (
    brand_assertion_custom_edges,
    brand_assertion_to_datapoint,
    brand_component_to_datapoint,
    brand_records_to_datapoints,
    brand_system_to_datapoint,
)
from .creative_field_projection import (
    CreativeFieldProjectionManifest,
    CreativeProjectionDocument,
    bounded_creative_field_traversal,
    build_creative_field_projection,
    compare_projection_drift,
    creative_field_projection_to_datapoints,
    populate_creative_field_projection,
    read_projection_manifest,
    write_projection_manifest,
)
from .datapoints import (
    entity_occurrence_to_datapoint,
    relationship_custom_edges,
    relationship_occurrence_to_datapoint,
    validation_to_datapoints,
)
from .definitions import DefinitionExample, EntityDefinition, RelationshipDefinition
from .extractor import SemanticExtractor
from .models import EntityMatch, ExtractionResult, MatchType, RelationshipMatch
from .prompt import compile_extraction_prompt
from .validation import (
    EntityOccurrence,
    RelationshipOccurrence,
    ValidationRejection,
    ValidationResult,
    validate_extraction,
)
from .world_v3_projection import (
    WorldV3ProjectionManifest,
    WorldV3ProjectionNode,
    bounded_world_v3_traversal,
    build_world_v3_projection,
    compare_world_v3_projection_drift,
    populate_world_v3_projection,
    world_v3_projection_to_datapoints,
    write_world_v3_projection_manifest,
)
from .world_v3_runtime import WorldV3ProjectionWorker


class CogneeAdapter:
    """Owns all Cognee-specific behavior exposed to Testflight."""

    descriptor = AdapterDescriptor(
        name="cognee",
        upstream="https://github.com/topoteretes/cognee",
        capabilities=frozenset({Capability.MEMORY}),
    )

    def health(self) -> HealthReport:
        if find_spec("cognee") is None:
            return HealthReport(
                HealthState.UNAVAILABLE,
                "Cognee is not installed; enable the adapter's 'cognee' extra.",
            )
        return HealthReport(HealthState.AVAILABLE, "Cognee is importable.")


__all__ = [
    "CogneeAdapter",
    "brand_assertion_custom_edges",
    "brand_assertion_to_datapoint",
    "brand_component_to_datapoint",
    "brand_records_to_datapoints",
    "brand_system_to_datapoint",
    "CreativeFieldProjectionManifest",
    "CreativeProjectionDocument",
    "bounded_creative_field_traversal",
    "build_creative_field_projection",
    "compare_projection_drift",
    "creative_field_projection_to_datapoints",
    "populate_creative_field_projection",
    "read_projection_manifest",
    "write_projection_manifest",
    "DefinitionExample",
    "EntityDefinition",
    "EntityMatch",
    "EntityOccurrence",
    "ExtractionResult",
    "MatchType",
    "RelationshipDefinition",
    "RelationshipMatch",
    "RelationshipOccurrence",
    "SemanticExtractor",
    "ValidationRejection",
    "ValidationResult",
    "compile_extraction_prompt",
    "entity_occurrence_to_datapoint",
    "relationship_custom_edges",
    "relationship_occurrence_to_datapoint",
    "validate_extraction",
    "validation_to_datapoints",
    "WorldV3ProjectionManifest",
    "WorldV3ProjectionNode",
    "WorldV3ProjectionWorker",
    "bounded_world_v3_traversal",
    "build_world_v3_projection",
    "compare_world_v3_projection_drift",
    "populate_world_v3_projection",
    "world_v3_projection_to_datapoints",
    "write_world_v3_projection_manifest",
]
