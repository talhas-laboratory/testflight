"""Deterministic loaders for small, provider-neutral Brand fixtures."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

from .models import BrandAssertion, BrandComponent, BrandSystem


class BrandFixture(BaseModel):
    """A complete synthetic Brand fixture before provider projection."""

    model_config = ConfigDict(extra="forbid")

    system: BrandSystem
    components: tuple[BrandComponent, ...] = ()
    assertions: tuple[BrandAssertion, ...] = ()


def load_brand_fixture(path: Path) -> BrandFixture:
    """Load and validate one YAML fixture without importing an upstream."""

    payload = yaml.safe_load(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"Brand fixture must be a mapping: {path}")
    system = BrandSystem.model_validate(
        {
            "brand_id": payload["brand_id"],
            "workspace_id": payload["workspace_id"],
            "label": payload["label"],
            "ontology_version": payload["ontology_version"],
        }
    )
    components = tuple(
        BrandComponent.model_validate(
            {
                "component_id": item.get("component_id", item.get("id")),
                "workspace_id": system.workspace_id,
                "brand_id": system.brand_id,
                "definition_id": item["definition_id"],
                "label": item["label"],
                "perspective": item["perspective"],
                "version": item.get("version", 1),
            }
        )
        for item in _component_payloads(payload)
    )
    assertions = tuple(
        BrandAssertion.model_validate(
            {
                **item,
                "workspace_id": item.get("workspace_id", system.workspace_id),
                "brand_id": item.get("brand_id", system.brand_id),
            }
        )
        for item in payload.get("assertions", [])
    )
    if any(assertion.workspace_id != system.workspace_id for assertion in assertions):
        raise ValueError("fixture assertion workspace_id does not match system")
    if any(assertion.brand_id != system.brand_id for assertion in assertions):
        raise ValueError("fixture assertion brand_id does not match system")
    return BrandFixture(system=system, components=components, assertions=assertions)


def validate_brand_fixture(fixture: BrandFixture, ontology: Any) -> None:
    """Check fixture identity, relation types, endpoints, and evidence invariants."""

    component_by_id = {component.component_id: component for component in fixture.components}
    if len(component_by_id) != len(fixture.components):
        raise ValueError("fixture contains duplicate component IDs")
    if any(component.brand_id != fixture.system.brand_id for component in fixture.components):
        raise ValueError("fixture component brand_id does not match system")

    assertion_by_id = {assertion.assertion_id: assertion for assertion in fixture.assertions}
    if len(assertion_by_id) != len(fixture.assertions):
        raise ValueError("fixture contains duplicate assertion IDs")
    known_ids = {fixture.system.brand_id, *component_by_id}
    for assertion in fixture.assertions:
        relation = ontology.relationship(assertion.relationship_definition_id)
        if assertion.subject_id not in known_ids or assertion.object_id not in known_ids:
            raise ValueError(f"assertion endpoint is not declared: {assertion.assertion_id}")
        if not assertion.evidence_ids:
            raise ValueError(f"assertion lacks evidence: {assertion.assertion_id}")
        if any(reference not in assertion_by_id for reference in assertion.contradiction_ids):
            raise ValueError(f"assertion contradiction is not declared: {assertion.assertion_id}")
        source_type = (
            "brand-system"
            if assertion.subject_id == fixture.system.brand_id
            else component_by_id[assertion.subject_id].definition_id
        )
        target_type = (
            "brand-system"
            if assertion.object_id == fixture.system.brand_id
            else component_by_id[assertion.object_id].definition_id
        )
        if source_type not in relation.source_types or target_type not in relation.target_types:
            raise ValueError(
                f"assertion endpoints violate {relation.id}: {source_type} -> {target_type}"
            )


def _component_payloads(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if "components" in payload:
        return list(payload["components"])
    legacy: list[dict[str, Any]] = []
    for key, perspective in (
        ("intended_components", "intended"),
        ("observed_perceptions", "observed"),
    ):
        legacy.extend(
            {**item, "perspective": item.get("perspective", perspective)}
            for item in payload.get(key, [])
        )
    return legacy


__all__ = ["BrandFixture", "load_brand_fixture", "validate_brand_fixture"]
