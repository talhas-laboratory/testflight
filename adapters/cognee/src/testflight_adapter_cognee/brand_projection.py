"""Cognee projection for accepted Brand records."""

from functools import lru_cache
from typing import Any

from testflight_brand import BrandAssertion, BrandComponent, BrandSystem


@lru_cache(maxsize=1)
def _brand_datapoint_classes() -> tuple[type[Any], type[Any], type[Any]]:
    try:
        from cognee.infrastructure.engine import DataPoint
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Cognee is required to build Brand DataPoints; install the adapter's 'cognee' extra"
        ) from error

    class BrandSystemDataPoint(DataPoint):
        brand_id: str
        workspace_id: str
        label: str
        ontology_version: str
        metadata: dict = {"index_fields": ["label", "brand_id"]}

    class BrandComponentDataPoint(DataPoint):
        component_id: str
        brand_id: str
        definition_id: str
        label: str
        perspective: str
        version: int
        metadata: dict = {"index_fields": ["label", "definition_id", "perspective"]}

    class BrandAssertionDataPoint(DataPoint):
        assertion_id: str
        workspace_id: str
        brand_id: str
        subject_id: str
        predicate: str
        object_id: str
        relationship_definition_id: str
        perspective: str
        epistemic_status: str
        evidence_ids: list[str]
        contradiction_ids: list[str]
        structural_weight: float | None = None
        evidence_confidence: float | None = None
        source_authority: float | None = None
        salience: float | None = None
        valence: float | None = None
        weight_policy_id: str | None = None
        status: str
        metadata: dict = {
            "index_fields": [
                "predicate",
                "relationship_definition_id",
                "perspective",
                "epistemic_status",
            ]
        }

    return BrandSystemDataPoint, BrandComponentDataPoint, BrandAssertionDataPoint


def brand_system_to_datapoint(system: BrandSystem) -> Any:
    system_class, _, _ = _brand_datapoint_classes()
    return system_class(
        id=system.brand_id,
        brand_id=system.brand_id,
        workspace_id=system.workspace_id,
        label=system.label,
        ontology_version=system.ontology_version,
    )


def brand_component_to_datapoint(component: BrandComponent) -> Any:
    _, component_class, _ = _brand_datapoint_classes()
    return component_class(
        id=component.component_id,
        component_id=component.component_id,
        brand_id=component.brand_id,
        definition_id=component.definition_id,
        label=component.label,
        perspective=component.perspective.value,
        version=component.version,
    )


def brand_assertion_to_datapoint(assertion: BrandAssertion) -> Any:
    _, _, assertion_class = _brand_datapoint_classes()
    return assertion_class(
        id=assertion.assertion_id,
        assertion_id=assertion.assertion_id,
        workspace_id=assertion.workspace_id,
        brand_id=assertion.brand_id,
        subject_id=assertion.subject_id,
        predicate=assertion.predicate,
        object_id=assertion.object_id,
        relationship_definition_id=assertion.relationship_definition_id,
        perspective=assertion.perspective.value,
        epistemic_status=assertion.epistemic_status.value,
        evidence_ids=list(assertion.evidence_ids),
        contradiction_ids=list(assertion.contradiction_ids),
        structural_weight=assertion.structural_weight,
        evidence_confidence=assertion.evidence_confidence,
        source_authority=assertion.source_authority,
        salience=assertion.salience,
        valence=assertion.valence,
        weight_policy_id=assertion.weight_policy_id,
        status=assertion.status,
    )


def brand_records_to_datapoints(records: list[Any]) -> list[Any]:
    """Convert accepted Brand records while keeping Cognee imports lazy."""

    points: list[Any] = []
    for record in records:
        if isinstance(record, BrandSystem):
            points.append(brand_system_to_datapoint(record))
        elif isinstance(record, BrandComponent):
            points.append(brand_component_to_datapoint(record))
        elif isinstance(record, BrandAssertion):
            if record.status != "accepted":
                raise ValueError("only accepted Brand assertions may be projected")
            points.append(brand_assertion_to_datapoint(record))
        else:
            raise TypeError(f"unsupported Brand record: {type(record).__name__}")
    return points


def brand_assertion_custom_edges(
    assertions: list[BrandAssertion],
) -> list[tuple[str, str, str, dict[str, Any]]]:
    """Build direct traversal edges while retaining assertion nodes for evidence."""

    return [
        (
            assertion.subject_id,
            assertion.object_id,
            assertion.predicate,
            {
                "assertion_id": assertion.assertion_id,
                "relationship_definition_id": assertion.relationship_definition_id,
                "perspective": assertion.perspective.value,
                "epistemic_status": assertion.epistemic_status.value,
                "structural_weight": assertion.structural_weight,
                "evidence_confidence": assertion.evidence_confidence,
            },
        )
        for assertion in assertions
        if assertion.status == "accepted"
    ]


__all__ = [
    "brand_assertion_custom_edges",
    "brand_assertion_to_datapoint",
    "brand_component_to_datapoint",
    "brand_records_to_datapoints",
    "brand_system_to_datapoint",
]
