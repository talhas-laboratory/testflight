"""Provider-neutral Brand World v3 service contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator
from testflight_semantic import (
    Capability,
    WorldDecision,
    WorldEvidence,
    WorldRecordType,
    WorldSource,
)


class ProposalStatus(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ReviewDisposition(StrEnum):
    READY = "ready"
    CHANGES_REQUESTED = "changes_requested"
    HOLD = "hold"


class DiffOperation(StrEnum):
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"


class MergeChoice(StrEnum):
    USE_SOURCE = "use_source"
    KEEP_TARGET = "keep_target"


class ProjectionJobStatus(StrEnum):
    """Lifecycle of a rebuild request for a non-canonical graph projection."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class WorldChangeSet(BaseModel):
    """A bounded candidate change, pending promotion by an approved decision."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    proposal_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    branch_id: str = Field(default="main", min_length=1)
    proposed_by: str = Field(min_length=1)
    proposed_at: datetime
    records: tuple[WorldRecordType, ...] = Field(min_length=1)
    rationale: str = Field(min_length=1)
    status: ProposalStatus = ProposalStatus.PROPOSED
    review_decision_id: str | None = None
    rejection_rationale: str | None = None

    @model_validator(mode="after")
    def require_one_scope_and_review_consistency(self) -> WorldChangeSet:
        if any(record.workspace_id != self.workspace_id for record in self.records):
            raise ValueError("every change-set record must share workspace_id")
        if any(record.branch_id != self.branch_id for record in self.records):
            raise ValueError("every change-set record must share branch_id")
        record_ids = [record.id for record in self.records]
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("a change set cannot contain multiple versions of one record")
        if self.status is ProposalStatus.PROPOSED and (
            self.review_decision_id or self.rejection_rationale
        ):
            raise ValueError("proposed change sets cannot carry a review disposition")
        if self.status is ProposalStatus.ACCEPTED and not self.review_decision_id:
            raise ValueError("accepted change sets require review_decision_id")
        if self.status is ProposalStatus.REJECTED and not self.rejection_rationale:
            raise ValueError("rejected change sets require rejection_rationale")
        return self


class WorldHistoryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str = Field(min_length=1)
    record_version: int = Field(ge=1)
    proposal_id: str = Field(min_length=1)
    recorded_at: datetime
    record: WorldRecordType

    @model_validator(mode="after")
    def match_embedded_record(self) -> WorldHistoryEntry:
        if self.record.id != self.record_id:
            raise ValueError("history record_id must match the embedded record")
        if self.record.record_version != self.record_version:
            raise ValueError("history record_version must match the embedded record")
        return self


class WorldRecordRef(BaseModel):
    """Unambiguous reference to one accepted record version."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    workspace_id: str = Field(min_length=1)
    branch_id: str = Field(default="main", min_length=1)
    record_id: str = Field(min_length=1)
    record_version: int | None = Field(default=None, ge=1)


class WorldSnapshotLeaf(BaseModel):
    """One canonical record commitment inside a resolved snapshot."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str = Field(min_length=1)
    record_version: int = Field(ge=1)
    canonical_record_hash: str = Field(min_length=64, max_length=64)


class WorldSnapshot(BaseModel):
    """Canonical accepted records reconstructed at one recorded-time point."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    workspace_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    recorded_at: datetime | None = None
    records: tuple[WorldRecordType, ...]
    leaves: tuple[WorldSnapshotLeaf, ...] = ()
    snapshot_root: str | None = None
    result_kind: Literal["canonical_snapshot"] = "canonical_snapshot"


class WorldReview(BaseModel):
    """Append-only human or agent review; it does not promote a proposal."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    review_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    reviewer_id: str = Field(min_length=1)
    reviewed_at: datetime
    disposition: ReviewDisposition
    findings: tuple[str, ...] = Field(min_length=1)


class WorldFieldChange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    operation: DiffOperation
    before: JsonValue = None
    after: JsonValue = None


class WorldRecordDiff(BaseModel):
    """An analytical comparison; never a canonical World record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    left: WorldRecordRef
    right: WorldRecordRef
    changes: tuple[WorldFieldChange, ...]
    result_kind: Literal["analytical_diff"] = "analytical_diff"


class WorldEvidenceBundle(BaseModel):
    """Resolved evidence and sources for one accepted canonical record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    target: WorldRecordRef
    evidence: tuple[WorldEvidence, ...]
    sources: tuple[WorldSource, ...]
    unresolved_evidence_ids: tuple[str, ...] = ()
    unresolved_source_ids: tuple[str, ...] = ()
    result_kind: Literal["analytical_evidence_read"] = "analytical_evidence_read"


class WorldSearchHit(BaseModel):
    """Deterministic lexical match over accepted canonical records."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    record: WorldRecordType
    matched_fields: tuple[str, ...] = Field(min_length=1)
    score: int = Field(ge=1)
    result_kind: Literal["analytical_search_hit"] = "analytical_search_hit"


class BranchConflictResolution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str = Field(min_length=1)
    choice: MergeChoice
    rationale: str = Field(min_length=1)


class WorldRepositoryError(RuntimeError):
    """Raised by a repository implementation without leaking storage semantics."""


class WorldProposalError(ValueError):
    """Raised when a domain transition cannot be performed."""


class ApprovalReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    proposal_id: str = Field(min_length=1)
    decision_id: str = Field(min_length=1)
    authority_grant_id: str = Field(min_length=1)
    authority_capability: Capability
    accepted_record_ids: tuple[str, ...] = Field(min_length=1)
    accepted_at: datetime


class WorldProjectionJob(BaseModel):
    """An idempotent request to rebuild one exact World snapshot.

    This is operational state only.  It deliberately records the source revision and
    scope, but contains no mutable copy of the World records themselves.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    job_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    source_proposal_id: str = Field(min_length=1)
    source_revision: str = Field(min_length=1)
    source_snapshot_root: str = Field(min_length=64, max_length=64)
    status: ProjectionJobStatus = ProjectionJobStatus.PENDING
    attempts: int = Field(default=0, ge=0)
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime


def validate_approval_decision(decision: WorldDecision, change_set: WorldChangeSet) -> None:
    """Ensure approval remains explicit and cannot be inferred from access or a status flag."""

    if decision.workspace_id != change_set.workspace_id:
        raise WorldProposalError("approval decision workspace does not match change set")
    if decision.branch_id != change_set.branch_id:
        raise WorldProposalError("approval decision branch does not match change set")
    if decision.status.value != "approved":
        raise WorldProposalError("change sets require an approved WorldDecision")
    if not decision.authority_ref:
        raise WorldProposalError("approved WorldDecision requires authority_ref")


__all__ = [
    "ApprovalReceipt",
    "DiffOperation",
    "BranchConflictResolution",
    "MergeChoice",
    "ProposalStatus",
    "ProjectionJobStatus",
    "ReviewDisposition",
    "WorldChangeSet",
    "WorldEvidenceBundle",
    "WorldFieldChange",
    "WorldHistoryEntry",
    "WorldProposalError",
    "WorldProjectionJob",
    "WorldRecordDiff",
    "WorldRecordRef",
    "WorldRepositoryError",
    "WorldReview",
    "WorldSearchHit",
    "WorldSnapshot",
    "WorldSnapshotLeaf",
    "validate_approval_decision",
]
