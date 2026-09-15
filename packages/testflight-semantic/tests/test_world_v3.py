from datetime import UTC, datetime

import pytest
from testflight_semantic import (
    ClaimKind,
    DecisionAlternative,
    RelationParticipant,
    WorldClaim,
    WorldDecision,
    WorldDecisionStatus,
    WorldEntity,
    WorldLifecycle,
    WorldRelation,
    record_kind,
)

NOW = datetime(2026, 9, 14, tzinfo=UTC)


def record_base(record_id: str, type_id: str) -> dict[str, object]:
    return {
        "id": record_id,
        "type_id": type_id,
        "workspace_id": "world://workspace/brand/biotic",
        "module_id": "world://ontology/module/brand-world/identity",
        "created_at": NOW,
        "created_by": "user:talha",
    }


def test_world_entity_has_a_typed_envelope_without_generic_meaning() -> None:
    entity = WorldEntity(
        **record_base("entity:biotic", "world://ontology/brand-world/type/Brand"),
        canonical_label="Biotic",
        definition="An identity-bearing brand.",
        lifecycle_status=WorldLifecycle.ACCEPTED,
    )

    assert record_kind(entity) == "entity"
    assert "meaning" not in entity.model_dump()


def test_world_claim_separates_proposition_from_entity_and_requires_one_object_form() -> None:
    claim = WorldClaim(
        **record_base("claim:biotic-purpose", "world://semantic/claim"),
        claim_kind=ClaimKind.NORMATIVE_COMMITMENT,
        subject_id="entity:biotic",
        predicate_id="world://ontology/brand-world/relation/has-purpose",
        object_value="Make daily care feel considered and approachable.",
    )

    assert record_kind(claim) == "claim"
    with pytest.raises(ValueError, match="exactly one"):
        WorldClaim(
            **record_base("claim:invalid", "world://semantic/claim"),
            claim_kind=ClaimKind.OBSERVATION,
            subject_id="entity:biotic",
            predicate_id="observed-as",
            object_id="entity:other",
            object_value="Both forms are invalid.",
        )


def test_world_relation_preserves_named_roles_and_rejects_role_flattening() -> None:
    relation = WorldRelation(
        **record_base("relation:biotic-offering", "world://semantic/relation"),
        relation_type_id="world://ontology/brand-world/relation/offers",
        participants=(
            RelationParticipant(role_id="brand", record_id="entity:biotic"),
            RelationParticipant(role_id="offering", record_id="entity:biotic-deodorant"),
        ),
    )

    assert relation.participants[0].role_id == "brand"
    with pytest.raises(ValueError, match="role IDs must be unique"):
        WorldRelation(
            **record_base("relation:invalid", "world://semantic/relation"),
            relation_type_id="related-to",
            participants=(
                RelationParticipant(role_id="participant", record_id="entity:biotic"),
                RelationParticipant(role_id="participant", record_id="entity:other"),
            ),
        )


def test_approved_decision_requires_selection_and_authority() -> None:
    base = {
        **record_base("decision:positioning", "world://semantic/decision"),
        "question": "Which positioning direction should govern the newsletter?",
        "alternatives": (
            DecisionAlternative(id="alternative:a", label="Care ritual"),
            DecisionAlternative(id="alternative:b", label="Product attribute"),
        ),
    }
    with pytest.raises(ValueError, match="authority_ref"):
        WorldDecision(
            **base,
            status=WorldDecisionStatus.APPROVED,
            selected_alternative_id="alternative:a",
        )

    decision = WorldDecision(
        **base,
        status=WorldDecisionStatus.APPROVED,
        selected_alternative_id="alternative:a",
        authority_ref="grant:biotic-founder-identity",
    )
    assert decision.status is WorldDecisionStatus.APPROVED
