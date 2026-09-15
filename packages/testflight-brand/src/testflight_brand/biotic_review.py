"""Human-sovereign review package for Biotic's proposed v3 Brand World."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from testflight_semantic import (
    ClaimKind,
    DecisionAlternative,
    DecisionStatus,
    WorldClaim,
    WorldDecision,
    WorldEvidence,
    WorldSource,
)

from .biotic_migration import BioticMigrationResult

_TARGET_BRANCH = "client-approved-v3"
_CREATED_AT = datetime(2026, 8, 31, tzinfo=UTC)


class ReviewRecommendation(StrEnum):
    VERIFY_SOURCE_RECORD = "verify_source_record"
    REVIEW_AS_SOURCE_ATTRIBUTED_FACT = "review_as_source_attributed_fact"
    HOLD_UNLESS_CLIENT_ADOPTS = "hold_unless_client_adopts"
    REVIEW_SEMANTIC_REFERENT = "review_semantic_referent"
    REVIEW_TYPED_RELATION_OR_STATE = "review_typed_relation_or_state"


class AuthorityReviewItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str = Field(min_length=1)
    semantic_kind: str = Field(min_length=1)
    recommendation: ReviewRecommendation
    evidence_ids: tuple[str, ...] = ()
    required_review: tuple[str, ...] = Field(min_length=1)


class BioticAuthorityReviewProposal(BaseModel):
    """A review queue, not an approval and not a writable canonical branch."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    proposal_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    source_branch_id: str = Field(min_length=1)
    target_branch_id: str = Field(min_length=1)
    source_snapshot_hash: str = Field(min_length=1)
    review_status: str = "awaiting_authorized_human"
    records_are_accepted: bool = False
    review_items: tuple[AuthorityReviewItem, ...] = Field(min_length=1)
    decision_template: WorldDecision


def build_biotic_authority_review_proposal(
    migration: BioticMigrationResult,
) -> BioticAuthorityReviewProposal:
    """Create an explicit FDE/client review queue without applying a decision."""

    review_items = tuple(_review_item(record) for record in migration.change_set.records)
    candidate_ids = tuple(item.record_id for item in review_items)
    decision = WorldDecision(
        id="decision:biotic:client-approved-branch-population",
        type_id="world://semantic/decision/brand-world-branch-review",
        workspace_id=migration.change_set.workspace_id,
        module_id="world://ontology/module/brand-world/governance-decisions",
        branch_id=_TARGET_BRANCH,
        created_at=_CREATED_AT,
        created_by="operator:biotic-authority-review-package@1",
        question=(
            "Which source-attributed public-research records should an authorized client actor "
            "adopt, reject, or keep held in the client-approved Brand World branch?"
        ),
        alternatives=(
            DecisionAlternative(
                id="review-record-by-record",
                label="Review record by record",
                rationale="Preserves epistemic type and requires an explicit disposition per item.",
            ),
            DecisionAlternative(
                id="hold-entire-package",
                label="Hold the entire package",
                rationale="Leaves public research separate from approved Brand meaning.",
            ),
        ),
        selected_alternative_id=None,
        status=DecisionStatus.PROPOSED,
        rationale=None,
        affected_record_ids=candidate_ids,
    )
    return BioticAuthorityReviewProposal(
        proposal_id="proposal:biotic-client-approved-branch-review",
        workspace_id=migration.change_set.workspace_id,
        source_branch_id=migration.change_set.branch_id,
        target_branch_id=_TARGET_BRANCH,
        source_snapshot_hash=migration.ledger.snapshot_hash,
        review_items=review_items,
        decision_template=decision,
    )


def _review_item(record: object) -> AuthorityReviewItem:
    evidence_ids = tuple(getattr(record, "evidence_ids", ()))
    if isinstance(record, (WorldSource, WorldEvidence)):
        recommendation = ReviewRecommendation.VERIFY_SOURCE_RECORD
    elif isinstance(record, WorldClaim) and record.claim_kind in {
        ClaimKind.INTERPRETATION,
        ClaimKind.HYPOTHESIS,
        ClaimKind.PROPOSAL,
    }:
        recommendation = ReviewRecommendation.HOLD_UNLESS_CLIENT_ADOPTS
    elif isinstance(record, WorldClaim):
        recommendation = ReviewRecommendation.REVIEW_AS_SOURCE_ATTRIBUTED_FACT
    elif getattr(record, "kind", None) == "entity":
        recommendation = ReviewRecommendation.REVIEW_SEMANTIC_REFERENT
    else:
        recommendation = ReviewRecommendation.REVIEW_TYPED_RELATION_OR_STATE
    return AuthorityReviewItem(
        record_id=record.id,
        semantic_kind=record.kind,
        recommendation=recommendation,
        evidence_ids=evidence_ids,
        required_review=(
            "Select adopt, reject, or hold.",
            "Record reviewer identity, authority grant, rationale, and review time.",
            "Preserve the record's epistemic kind; approval must not turn belief into fact.",
        ),
    )


__all__ = [
    "AuthorityReviewItem",
    "BioticAuthorityReviewProposal",
    "ReviewRecommendation",
    "build_biotic_authority_review_proposal",
]
