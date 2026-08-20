from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from testflight_semantic import (
    Assertion,
    AssertionStatus,
    AuthorityGrant,
    BindingMode,
    BoundSemantics,
    CandidateKind,
    CandidateSignals,
    Capability,
    ChangeType,
    Context,
    Deontic,
    DependencyEffect,
    DependencyRule,
    DerivationRecord,
    DerivationResult,
    EntityLifecycle,
    FreshnessState,
    FreshnessStatus,
    IdentityScope,
    Perspective,
    RepresentationBinding,
    RepresentationEvaluation,
    RepresentationProfile,
    RepresentationRule,
    SemanticEntity,
    TemporalInterval,
    ValidationMethod,
    classify_candidate,
    resolve_profile_order,
    selector_matches,
    validate_derivation_graph,
)


def test_classification_uses_constitutional_order_and_holds_without_evidence() -> None:
    assert (
        classify_candidate(
            CandidateSignals(
                is_temporally_bounded_occurrence=True,
                is_proposition=True,
                evidence_ref="source:1",
            )
        ).semantic_kind
        is CandidateKind.EVENT
    )
    assert (
        classify_candidate(
            CandidateSignals(is_proposition=True, evidence_ref="source:1")
        ).semantic_kind
        is CandidateKind.ASSERTION
    )
    held = classify_candidate(CandidateSignals(has_persistent_identity=True))
    assert held.semantic_kind is None
    assert held.status.value == "hold"


def test_context_id_is_stable_and_content_addressed() -> None:
    first = Context(
        brand_id="brand:acme",
        audience_ids=("audience:builders",),
        dimensions={"market": "EU", "purpose": "positioning"},
    )
    second = Context(
        dimensions={"purpose": "positioning", "market": "EU"},
        audience_ids=("audience:builders",),
        brand_id="brand:acme",
    )
    changed = Context(
        brand_id="brand:acme",
        audience_ids=("audience:builders",),
        dimensions={"market": "US", "purpose": "positioning"},
    )

    assert first.context_id == second.context_id
    assert first.context_id != changed.context_id
    with pytest.raises(ValueError, match="does not match"):
        Context(brand_id="brand:acme", context_id="world://context/wrong")


def test_temporal_interval_normalizes_utc_and_enforces_half_open_bounds() -> None:
    interval = TemporalInterval(
        from_time=datetime(2026, 1, 1, 1, tzinfo=UTC),
        to_time=datetime(2026, 1, 1, 2, tzinfo=UTC),
        from_semantics=BoundSemantics.KNOWN,
        to_semantics=BoundSemantics.KNOWN,
    )
    assert interval.from_time == datetime(2026, 1, 1, 1, tzinfo=UTC)
    assert interval.to_time > interval.from_time

    with pytest.raises(ValueError, match="to_time > from_time"):
        TemporalInterval(
            from_time=datetime(2026, 1, 2, tzinfo=UTC),
            to_time=datetime(2026, 1, 1, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        TemporalInterval(from_time=datetime(2026, 1, 1))


def test_entity_assertion_and_context_keep_semantic_boundaries() -> None:
    context = Context(brand_id="brand:acme")
    entity = SemanticEntity(
        entity_id="brand:acme",
        type_id="world://ontology/type/Brand",
        workspace_id="workspace:acme",
        identity_scope=IdentityScope.WORKSPACE,
        lifecycle_status=EntityLifecycle.ACCEPTED,
        canonical_label="Acme",
        definition_version="0.1.0",
    )
    assertion = Assertion(
        assertion_id="assertion:1",
        subject_id=entity.entity_id,
        predicate_id="world://ontology/relation/positioned-as",
        object_value="builder infrastructure",
        context_id=context.context_id,
        perspective=Perspective.INTENDED,
        status=AssertionStatus.PROPOSED,
        evidence_refs=("span:1",),
    )

    assert assertion.context_id == context.context_id
    assert entity.entity_id != assertion.assertion_id
    with pytest.raises(ValidationError, match="exactly one"):
        Assertion(
            assertion_id="assertion:invalid",
            subject_id="brand:acme",
            predicate_id="relation:uses",
            context_id=context.context_id,
            perspective=Perspective.OBSERVED,
        )


def test_authority_is_scoped_and_does_not_follow_workspace_membership() -> None:
    grant = AuthorityGrant(
        grant_id="grant:steward",
        principal_id="person:steward",
        capabilities=(Capability.PROMOTE,),
        object_selectors=("ontology:brand/*",),
        context_selector=("world://context/brand",),
        issued_by="authority:root",
        policy_version="authority-v1",
    )
    assert grant.allows(
        Capability.PROMOTE,
        "ontology:brand/Brand",
        context_id="world://context/brand",
    )
    assert not grant.allows(
        Capability.PROMOTE,
        "ontology:other/Thing",
        context_id="world://context/brand",
    )
    assert not grant.allows(
        Capability.ACCEPT,
        "ontology:brand/Brand",
        context_id="world://context/brand",
    )


def test_derivation_validation_rejects_orphans_and_cycles() -> None:
    first = DerivationRecord(
        derivation_id="derivation:1",
        output_ids=("entity:1",),
        input_ids=("source:1",),
        operation_id="extract:v1",
        actor_id="agent:extractor",
        ontology_version="0.1.0",
        reasoning_operators=("world://operator/guardrail/ontology-conflation@1",),
        occurred_at="2026-08-20T00:00:00Z",
        result=DerivationResult.PROPOSED,
    )
    second = first.model_copy(
        update={
            "derivation_id": "derivation:2",
            "output_ids": ("assertion:1",),
            "input_ids": ("entity:1",),
            "operation_id": "assert:v1",
        }
    )
    validate_derivation_graph((first, second), source_ids=frozenset({"source:1"}))

    with pytest.raises(ValueError, match="no source or derivation"):
        validate_derivation_graph((second,))

    cycle_a = first.model_copy(update={"input_ids": ("entity:2",)})
    cycle_b = second.model_copy(update={"output_ids": ("entity:2",), "input_ids": ("entity:1",)})
    with pytest.raises(ValueError, match="cycle"):
        validate_derivation_graph((cycle_a, cycle_b))


def test_representation_profiles_are_dag_ordered_and_evaluations_are_multidimensional() -> None:
    shared = RepresentationProfile(profile_id="profile:shared", version="1.0.0")
    brand = RepresentationProfile(
        profile_id="profile:brand",
        version="1.0.0",
        includes=(shared.profile_id,),
        rule_ids=("rule:yellow",),
    )
    ordered = resolve_profile_order(
        {shared.profile_id: shared, brand.profile_id: brand}, brand.profile_id
    )
    assert [profile.profile_id for profile in ordered] == ["profile:shared", "profile:brand"]

    with pytest.raises(ValueError, match="cycle"):
        resolve_profile_order(
            {
                "profile:a": RepresentationProfile(
                    profile_id="profile:a", version="1.0.0", includes=("profile:b",)
                ),
                "profile:b": RepresentationProfile(
                    profile_id="profile:b", version="1.0.0", includes=("profile:a",)
                ),
            },
            "profile:a",
        )

    rule = RepresentationRule(
        rule_id="rule:yellow",
        version="1.0.0",
        facet_id="visual",
        deontic=Deontic.SHOULD,
        constraint={"accent": "yellow"},
        rationale="Fixture rule",
        validation_method=ValidationMethod.DETERMINISTIC,
        severity="warning",
    )
    binding = RepresentationBinding(
        binding_id="binding:brand",
        entity_id="brand:acme",
        profile_id=brand.profile_id,
        profile_version=brand.version,
        context_id="world://context/brand",
        mode=BindingMode.ADAPTIVE,
    )
    evaluation = RepresentationEvaluation(
        manifestation_id="manifestation:1",
        compliance="partial",
        freshness=FreshnessStatus.POTENTIALLY_STALE,
        findings=("rule:yellow",),
        rule_ids=(rule.rule_id,),
        context_id=binding.context_id,
        derivation_id="derivation:manifestation",
    )
    assert evaluation.compliance.value == "partial"
    assert evaluation.freshness is FreshnessStatus.POTENTIALLY_STALE


def test_dependency_rule_edge_and_staleness_keep_distinct_meanings() -> None:
    rule = DependencyRule(
        rule_id="dependency:positioning-messaging",
        version="1.0.0",
        upstream_selector={"entity_type": "Positioning"},
        downstream_selector={"entity_type": "MessagingArtifact"},
        trigger_change_types=(ChangeType.ASSERTION_ACCEPTED,),
        effect=DependencyEffect.POTENTIALLY_STALE,
    )
    assert selector_matches(
        rule.upstream_selector, entity_id="positioning:1", entity_type="Positioning"
    )
    assert not selector_matches(rule.upstream_selector, entity_id="brand:1", entity_type="Brand")

    marker = FreshnessState.POTENTIALLY_STALE
    assert marker.value != "false"
