"""Conversion from validated semantic occurrences to Cognee DataPoints.

Cognee is imported lazily here.  The rest of the semantic environment can run
and be tested without the optional upstream dependency.
"""

from functools import lru_cache
from typing import Any

from .validation import EntityOccurrence, RelationshipOccurrence, ValidationResult


@lru_cache(maxsize=1)
def _datapoint_classes() -> tuple[type[Any], type[Any]]:
    try:
        from cognee.infrastructure.engine import DataPoint
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Cognee is required to build DataPoints; install the adapter's cognee extra"
        ) from error

    class SemanticEntityOccurrence(DataPoint):
        entity_type: str
        quote: str
        normalized_content: str
        match_type: str
        source_id: str
        start: int
        end: int
        confidence: float | None = None
        metadata: dict = {
            "index_fields": ["normalized_content", "quote"],
            "identity_fields": ["entity_type", "source_id", "start", "end"],
        }

    class SemanticRelationship(DataPoint):
        relationship_type: str
        source_occurrence_id: str
        target_occurrence_id: str
        evidence_quote: str
        source_id: str
        start: int
        end: int
        confidence: float | None = None
        metadata: dict = {
            "index_fields": ["relationship_type", "evidence_quote"],
            "identity_fields": [
                "relationship_type",
                "source_occurrence_id",
                "target_occurrence_id",
                "source_id",
                "start",
                "end",
            ],
        }

    return SemanticEntityOccurrence, SemanticRelationship


def entity_occurrence_to_datapoint(occurrence: EntityOccurrence) -> Any:
    """Convert one occurrence while retaining its stable UUID as Cognee id."""

    entity_class, _ = _datapoint_classes()
    return entity_class(
        id=occurrence.occurrence_id,
        entity_type=occurrence.entity_type,
        quote=occurrence.quote,
        normalized_content=occurrence.normalized_content,
        match_type=occurrence.match_type.value,
        source_id=occurrence.source_id,
        start=occurrence.start,
        end=occurrence.end,
        confidence=occurrence.confidence,
    )


def relationship_occurrence_to_datapoint(relationship: RelationshipOccurrence) -> Any:
    """Convert one relationship record to an explicit Cognee graph node."""

    _, relationship_class = _datapoint_classes()
    return relationship_class(
        id=relationship.relationship_id,
        relationship_type=relationship.relationship_type,
        source_occurrence_id=str(relationship.source_occurrence_id),
        target_occurrence_id=str(relationship.target_occurrence_id),
        evidence_quote=relationship.evidence_quote,
        source_id=relationship.source_id,
        start=relationship.start,
        end=relationship.end,
        confidence=relationship.confidence,
    )


def validation_to_datapoints(result: ValidationResult) -> list[Any]:
    """Return entity and relationship DataPoints in one deterministic batch."""

    return [
        *(entity_occurrence_to_datapoint(occurrence) for occurrence in result.occurrences),
        *(
            relationship_occurrence_to_datapoint(relationship)
            for relationship in result.relationships
        ),
    ]


def relationship_custom_edges(
    result: ValidationResult,
) -> list[tuple[str, str, str, dict[str, str]]]:
    """Build Cognee ``custom_edges`` records for direct endpoint graph edges.

    The relationship DataPoint remains useful for evidence retrieval; these
    optional edges connect the two occurrence nodes directly when persisted with
    ``cognee.tasks.storage.add_data_points(..., custom_edges=...)``.
    """

    return [
        (
            str(relationship.source_occurrence_id),
            str(relationship.target_occurrence_id),
            relationship.relationship_type,
            {
                "evidence_quote": relationship.evidence_quote,
                "source_id": relationship.source_id,
            },
        )
        for relationship in result.relationships
    ]


__all__ = [
    "entity_occurrence_to_datapoint",
    "relationship_custom_edges",
    "relationship_occurrence_to_datapoint",
    "validation_to_datapoints",
]
