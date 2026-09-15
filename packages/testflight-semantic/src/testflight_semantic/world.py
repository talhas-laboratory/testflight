"""Constitutional Brand World v3 records.

These contracts deliberately model different semantic behaviors separately. They are not a
storage schema, UI payload, or provider representation.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .time import TemporalInterval


class WorldLifecycle(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    CHALLENGED = "challenged"
    SUPERSEDED = "superseded"
    REVOKED = "revoked"
    ARCHIVED = "archived"


class ClaimKind(StrEnum):
    OBSERVATION = "observation"
    INTERPRETATION = "interpretation"
    HYPOTHESIS = "hypothesis"
    PROPOSAL = "proposal"
    FACTUAL_ASSERTION = "factual_assertion"
    NORMATIVE_COMMITMENT = "normative_commitment"


class SourceContentPolicy(StrEnum):
    RETAINED = "retained"
    BOUNDED_EXCERPT = "bounded_excerpt"
    LIVE_REFERENCE_ONLY = "live_reference_only"
    PROHIBITED = "prohibited"


class DecisionStatus(StrEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class WorldRecord(BaseModel):
    """Lineage shared by every canonical v3 record.

    Domain-specific information belongs to the specialized record classes below. In particular,
    this envelope intentionally has no generic ``meaning`` or arbitrary metadata field.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    type_id: str = Field(min_length=1)
    schema_version: str = Field(default="3.0.0", min_length=1)
    record_version: int = Field(default=1, ge=1)
    workspace_id: str = Field(min_length=1)
    module_id: str = Field(min_length=1)
    branch_id: str = Field(default="main", min_length=1)
    lifecycle_status: WorldLifecycle = WorldLifecycle.PROPOSED
    valid_time: TemporalInterval | None = None
    known_time: TemporalInterval | None = None
    context_refs: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    derivation_ref: str | None = None
    authority_ref: str | None = None
    created_at: datetime
    created_by: str = Field(min_length=1)
    supersedes_ref: str | None = None


class WorldEntity(WorldRecord):
    kind: Literal["entity"] = "entity"
    canonical_label: str = Field(min_length=1)
    aliases: tuple[str, ...] = ()
    definition: str = Field(min_length=1)


class WorldState(WorldRecord):
    kind: Literal["state"] = "state"
    subject_ids: tuple[str, ...] = Field(min_length=1)
    state_value: str = Field(min_length=1)
    state_schema_id: str = Field(min_length=1)
    described_by_claim_ids: tuple[str, ...] = ()


class EventParticipant(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)


class WorldEvent(WorldRecord):
    kind: Literal["event"] = "event"
    event_type_id: str = Field(min_length=1)
    participants: tuple[EventParticipant, ...] = Field(min_length=1)
    occurred_at: TemporalInterval = Field(default_factory=TemporalInterval)
    evidence_ids: tuple[str, ...] = ()


class RelationParticipant(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role_id: str = Field(min_length=1)
    record_id: str = Field(min_length=1)


class WorldRelation(WorldRecord):
    kind: Literal["relation"] = "relation"
    relation_type_id: str = Field(min_length=1)
    participants: tuple[RelationParticipant, ...] = Field(min_length=2)
    evidence_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def require_distinct_participant_roles(self) -> WorldRelation:
        roles = [participant.role_id for participant in self.participants]
        if len(roles) != len(set(roles)):
            raise ValueError("WorldRelation participant role IDs must be unique")
        return self


class WorldClaim(WorldRecord):
    kind: Literal["claim"] = "claim"
    claim_kind: ClaimKind
    subject_id: str = Field(min_length=1)
    predicate_id: str = Field(min_length=1)
    object_id: str | None = None
    object_value: str | None = None
    perspective_id: str | None = None
    evidence_ids: tuple[str, ...] = ()
    opposing_evidence_ids: tuple[str, ...] = ()
    contradiction_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    permitted_task_types: tuple[str, ...] = ()

    @model_validator(mode="after")
    def require_one_object_form(self) -> WorldClaim:
        if (self.object_id is None) == (self.object_value is None):
            raise ValueError("WorldClaim requires exactly one of object_id or object_value")
        if set(self.evidence_ids) & set(self.opposing_evidence_ids):
            raise ValueError("evidence cannot both support and oppose one claim")
        return self


class WorldSource(WorldRecord):
    kind: Literal["source"] = "source"
    locator: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content_policy: SourceContentPolicy
    captured_at: datetime
    content_hash: str | None = None


class WorldEvidence(WorldRecord):
    kind: Literal["evidence"] = "evidence"
    source_id: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    excerpt: str | None = None
    measurement: str | None = None
    limitations: tuple[str, ...] = ()
    integrity_hash: str | None = None

    @model_validator(mode="after")
    def require_bounded_evidence_content(self) -> WorldEvidence:
        if self.excerpt is None and self.measurement is None:
            raise ValueError("WorldEvidence requires an excerpt or measurement")
        return self


class DecisionAlternative(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    rationale: str | None = None


class WorldDecision(WorldRecord):
    kind: Literal["decision"] = "decision"
    question: str = Field(min_length=1)
    alternatives: tuple[DecisionAlternative, ...] = Field(min_length=1)
    selected_alternative_id: str | None = None
    status: DecisionStatus = DecisionStatus.PROPOSED
    rationale: str | None = None
    evidence_ids: tuple[str, ...] = ()
    affected_record_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_selection_and_authority(self) -> WorldDecision:
        alternative_ids = {alternative.id for alternative in self.alternatives}
        if self.selected_alternative_id and self.selected_alternative_id not in alternative_ids:
            raise ValueError("selected_alternative_id must identify a declared alternative")
        if self.status is DecisionStatus.APPROVED:
            if not self.selected_alternative_id:
                raise ValueError("approved decision requires selected_alternative_id")
            if not self.authority_ref:
                raise ValueError("approved decision requires authority_ref")
        return self


WorldRecordType = (
    WorldEntity
    | WorldState
    | WorldEvent
    | WorldRelation
    | WorldClaim
    | WorldSource
    | WorldEvidence
    | WorldDecision
)


def record_kind(value: WorldRecordType) -> str:
    """Return a stable semantic kind without exposing a storage or UI label."""

    return value.kind


__all__ = [
    "ClaimKind",
    "DecisionAlternative",
    "DecisionStatus",
    "EventParticipant",
    "RelationParticipant",
    "SourceContentPolicy",
    "WorldClaim",
    "WorldDecision",
    "WorldEntity",
    "WorldEvent",
    "WorldEvidence",
    "WorldLifecycle",
    "WorldRecord",
    "WorldRecordType",
    "WorldRelation",
    "WorldSource",
    "WorldState",
    "record_kind",
]
