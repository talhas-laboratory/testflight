from datetime import UTC, datetime

import pytest
from testflight_semantic import (
    ChangeType,
    Context,
    DecisionRecord,
    DecisionStatus,
    DependencyCandidate,
    DependencyEffect,
    DependencyRule,
    FederationBridge,
    FederationPlanStatus,
    FederationRegistry,
    KnowledgeContainer,
    evaluate_dependency_rule,
)


def test_decision_records_keep_inputs_and_rejected_options_auditable() -> None:
    record = DecisionRecord(
        decision_id="decision:acme:positioning",
        workspace_id="world://workspace/brand/acme",
        decision_type_id="world://ontology/brand/type/StrategyDecision",
        context_id="world://context/acme",
        input_ids=("assertion:insight", "entity:product-definition"),
        selected_option_id="entity:positioning:confidence",
        rejected_option_ids=("entity:positioning:discount",),
        rationale="Selected after reviewing the scoped research observation.",
        authority_grant_id="grant:brand-strategy",
        derivation_id="derivation:decision:1",
        decided_at=datetime(2026, 8, 31, tzinfo=UTC),
        status=DecisionStatus.ACCEPTED,
    )

    assert record.selected_option_id not in record.rejected_option_ids
    with pytest.raises(ValueError, match="cannot also be rejected"):
        record.model_copy(
            update={"rejected_option_ids": ("entity:positioning:confidence",)}
        ).validate_options()


def test_federation_routes_to_the_smallest_permitted_child_then_explicit_bridge() -> None:
    parent = KnowledgeContainer(
        workspace_id="world://workspace/brand/acme",
        route="brand/acme",
        dataset_name="Acme brand world",
        owns_entity_ids=("brand:acme",),
    )
    child = KnowledgeContainer(
        workspace_id="world://workspace/brand/acme/offering/app",
        parent_workspace_id=parent.workspace_id,
        route="brand/acme/offering/app",
        dataset_name="Acme App child world",
        augments_entity_ids=("offering:acme:app",),
    )
    registry = FederationRegistry(
        containers=(parent, child),
        bridges=(
            FederationBridge(
                bridge_id="bridge:app-to-brand",
                source_workspace_id=child.workspace_id,
                target_workspace_id=parent.workspace_id,
                subject_id="offering:acme:app",
                predicate_id="world://ontology/federation/augments",
                object_id="brand:acme",
                context_id="world://context/acme",
                evidence_refs=("evidence:container-registration",),
                allow_traversal=True,
            ),
        ),
    )

    plan = registry.plan_child_first(
        root_workspace_id=parent.workspace_id,
        entity_ids=("offering:acme:app",),
        permitted_workspace_ids=frozenset((parent.workspace_id, child.workspace_id)),
    )

    assert plan.status is FederationPlanStatus.HIT
    assert plan.primary_workspace_id == child.workspace_id
    assert plan.supplemental_workspace_ids == (parent.workspace_id,)


def test_dependency_rules_only_propagate_across_matching_context_and_path() -> None:
    context = Context(
        brand_id="brand:acme",
        offering_id="offering:acme:app",
        audience_ids=("audience:new-runners",),
        channel_ids=("channel:instagram",),
        dimensions={"market": "DE"},
    )
    other_audience = Context(
        brand_id="brand:acme",
        offering_id="offering:acme:app",
        audience_ids=("audience:experienced-runners",),
        channel_ids=("channel:instagram",),
        dimensions={"market": "DE"},
    )
    rule = DependencyRule(
        rule_id="dependency:icp-to-asset",
        version="1.0.0",
        upstream_selector={"entity_type": "IdealCustomerProfile"},
        downstream_selector={
            "entity_type": "Asset",
            "relation_path": ("designed-for", "implements", "operationalizes", "governs"),
        },
        trigger_change_types=(ChangeType.ENTITY_REVISION,),
        effect=DependencyEffect.POTENTIALLY_STALE,
        max_depth=4,
    )
    upstream = DependencyCandidate(
        record_id="entity:icp:new-runners",
        entity_id="entity:icp:new-runners",
        entity_type="IdealCustomerProfile",
        context=context,
    )
    impacts = evaluate_dependency_rule(
        rule,
        upstream=upstream,
        downstream=(
            DependencyCandidate(
                record_id="asset:instagram:new-runners",
                entity_id="asset:instagram:new-runners",
                entity_type="Asset",
                context=context,
                relation_path=("designed-for", "implements", "operationalizes", "governs"),
            ),
            DependencyCandidate(
                record_id="asset:instagram:experienced-runners",
                entity_id="asset:instagram:experienced-runners",
                entity_type="Asset",
                context=other_audience,
                relation_path=("designed-for", "implements", "operationalizes", "governs"),
            ),
        ),
        change_type=ChangeType.ENTITY_REVISION,
        created_at=datetime(2026, 8, 31, tzinfo=UTC),
    )

    assert [impact.downstream_id for impact in impacts] == ["asset:instagram:new-runners"]
