"""Overlay branches for interpretations and scenarios without world copies."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BranchKind(StrEnum):
    INTERPRETATION = "interpretation"
    HYPOTHESIS = "hypothesis"
    SCENARIO = "scenario"
    COUNTERFACTUAL = "counterfactual"
    AGENT_BELIEF = "agent_belief"


class BranchStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    HELD = "held"
    MERGED = "merged"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class BranchDeltaKind(StrEnum):
    ADD = "add"
    EXCLUDE = "exclude"
    REPLACE = "replace"
    RETRACT = "retract"


class WorldBranch(BaseModel):
    """A compact alternative over a parent branch's records."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    branch_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    parent_branch_id: str | None = None
    branch_kind: BranchKind
    label: str = Field(min_length=1)
    assumption_ids: tuple[str, ...] = ()
    created_by: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    status: BranchStatus = BranchStatus.DRAFT
    visibility_policy_id: str | None = None
    derivation_id: str | None = None

    @model_validator(mode="after")
    def reject_self_parent(self) -> "WorldBranch":
        if self.parent_branch_id == self.branch_id:
            raise ValueError("WorldBranch cannot be its own parent")
        return self


class BranchDelta(BaseModel):
    """A branch-local addition, exclusion, replacement, or retraction."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    delta_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    kind: BranchDeltaKind
    target_record_id: str = Field(min_length=1)
    replacement_record_id: str | None = None
    rationale: str = Field(min_length=1)
    derivation_id: str | None = None

    @model_validator(mode="after")
    def require_replacement_only_when_needed(self) -> "BranchDelta":
        if self.kind is BranchDeltaKind.REPLACE and not self.replacement_record_id:
            raise ValueError("replace delta requires replacement_record_id")
        if self.kind is not BranchDeltaKind.REPLACE and self.replacement_record_id:
            raise ValueError("only replace delta may set replacement_record_id")
        if self.replacement_record_id == self.target_record_id:
            raise ValueError("replacement record must differ from target record")
        return self


class BranchConflict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    conflict_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    record_ids: tuple[str, ...] = Field(min_length=2)
    context_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    derivation_id: str | None = None


class MergeAssessment(BaseModel):
    """An assessment is not a merge operation and cannot mutate a parent."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assessment_id: str = Field(min_length=1)
    source_branch_id: str = Field(min_length=1)
    target_branch_id: str = Field(min_length=1)
    accepted_delta_ids: tuple[str, ...] = ()
    rejected_delta_ids: tuple[str, ...] = ()
    unresolved_conflict_ids: tuple[str, ...] = ()
    authority_grant_id: str | None = None
    derivation_id: str | None = None

    @model_validator(mode="after")
    def reject_overlapping_assessment(self) -> "MergeAssessment":
        if self.source_branch_id == self.target_branch_id:
            raise ValueError("MergeAssessment source and target branches must differ")
        accepted = set(self.accepted_delta_ids)
        rejected = set(self.rejected_delta_ids)
        if accepted & rejected:
            raise ValueError("a delta cannot be both accepted and rejected")
        return self


def resolve_branch_records(
    *,
    branch_id: str,
    branches: tuple[WorldBranch, ...],
    deltas: tuple[BranchDelta, ...],
    base_record_ids: tuple[str, ...],
) -> tuple[str, ...]:
    """Resolve a branch overlay deterministically without hiding conflicts.

    Returned IDs are a view only. This function never writes a merge and does
    not infer branch ancestry from string prefixes.
    """

    indexed = {branch.branch_id: branch for branch in branches}
    if branch_id not in indexed:
        raise ValueError(f"unknown branch: {branch_id}")
    lineage: list[str] = []
    current = indexed[branch_id]
    visited: set[str] = set()
    while True:
        if current.branch_id in visited:
            raise ValueError("branch hierarchy contains a cycle")
        visited.add(current.branch_id)
        lineage.append(current.branch_id)
        if current.parent_branch_id is None:
            break
        try:
            current = indexed[current.parent_branch_id]
        except KeyError as exc:
            raise ValueError("branch parent is unknown") from exc

    resolved = list(dict.fromkeys(base_record_ids))
    for branch in reversed(lineage):
        for delta in (item for item in deltas if item.branch_id == branch):
            if delta.kind is BranchDeltaKind.ADD:
                if delta.target_record_id not in resolved:
                    resolved.append(delta.target_record_id)
            elif delta.kind in {BranchDeltaKind.EXCLUDE, BranchDeltaKind.RETRACT}:
                resolved = [
                    record_id for record_id in resolved if record_id != delta.target_record_id
                ]
            else:
                resolved = [
                    delta.replacement_record_id
                    if record_id == delta.target_record_id
                    else record_id
                    for record_id in resolved
                ]
                if (
                    delta.target_record_id not in resolved
                    and delta.replacement_record_id not in resolved
                ):
                    resolved.append(delta.replacement_record_id)
    return tuple(record_id for record_id in resolved if record_id is not None)


__all__ = [
    "BranchConflict",
    "BranchDelta",
    "BranchDeltaKind",
    "BranchKind",
    "BranchStatus",
    "MergeAssessment",
    "WorldBranch",
    "resolve_branch_records",
]
