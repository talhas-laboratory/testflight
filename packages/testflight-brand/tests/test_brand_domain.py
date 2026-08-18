from pathlib import Path

from testflight_brand import (
    BrandAssertion,
    BrandComponent,
    BrandSystem,
    RelationshipWeightDimensions,
    RelationshipWeightPolicy,
    load_brand_fixture,
    load_brand_ontology,
)
from testflight_semantic import EpistemicStatus, Perspective

ROOT = Path(__file__).resolve().parents[3]


def test_brand_ontology_loads_and_validates() -> None:
    ontology, sources = load_brand_ontology(ROOT)

    assert ontology.id == "world://ontology/brand-system"
    assert ontology.version == "1.0.0"
    assert {item.id for item in ontology.component_types} >= {
        "identity",
        "expression",
        "perception",
    }
    assert ontology.relationship("has_component").family == "composition"
    assert len(sources) == 23


def test_brand_system_keeps_components_and_assertions_distinct() -> None:
    brand = BrandSystem(
        brand_id="brand:example",
        workspace_id="world://workspace/brand/example",
        label="Example Brand",
        ontology_version="1.0.0",
    )
    component = BrandComponent(
        component_id="component:promise",
        workspace_id=brand.workspace_id,
        brand_id=brand.brand_id,
        definition_id="identity",
        label="reliable progress",
        perspective=Perspective.INTENDED,
    )
    assertion = BrandAssertion(
        assertion_id="assertion:1",
        workspace_id=brand.workspace_id,
        brand_id=brand.brand_id,
        subject_id=brand.brand_id,
        predicate="has_component",
        object_id=component.component_id,
        relationship_definition_id="has_component",
        perspective=Perspective.INTENDED,
        epistemic_status=EpistemicStatus.NORMATIVE,
        recorded_at="2026-08-18T00:00:00Z",
        structural_weight=0.8,
        evidence_confidence=0.95,
        source_authority=1.0,
    )

    assert component.component_id != assertion.assertion_id
    assert assertion.predicate == "has_component"
    assert assertion.evidence_confidence != assertion.structural_weight


def test_weight_policy_does_not_create_truth_score_by_default() -> None:
    dimensions = RelationshipWeightDimensions(
        structural_weight=0.8,
        evidence_confidence=0.9,
        source_authority=1.0,
        salience=0.6,
    )

    assert RelationshipWeightPolicy().derive_effective_strength(dimensions) is None
    assert (
        RelationshipWeightPolicy(aggregate_enabled=True).derive_effective_strength(dimensions)
        == 0.825
    )


def test_minimal_fixture_contains_distinct_intended_and_observed_assertions() -> None:
    fixture = load_brand_fixture(ROOT / "domains/brand/fixtures/minimal-brand/brand.yaml")

    assert fixture.system.brand_id == "brand:example"
    assert len(fixture.components) == 3
    assert {assertion.perspective for assertion in fixture.assertions} == {
        Perspective.INTENDED,
        Perspective.OBSERVED,
    }
    assert any(assertion.contradiction_ids for assertion in fixture.assertions)
