"""Deterministic compilation of bounded, branch-aware world views."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from .branches import BranchConflict, BranchDelta, WorldBranch, resolve_branch_records
from .learning import ExperimentPlan, HypothesisRecord, LearningUpdate, ObservedOutcome
from .perspectives import PerspectiveProfile
from .relationship_frames import RelationshipFrame
from .states import StateSnapshot


class WorldViewStatus(StrEnum):
    HIT = "hit"
    PARTIAL = "partial"
    NO_HIT = "no_hit"
    HOLD = "hold"


class WorldViewRequest(BaseModel):
    """The bounded semantic selection request before retrieval/model synthesis."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    task_type: str = Field(min_length=1)
    perspective_ids: tuple[str, ...] = ()
    permitted_record_ids: tuple[str, ...] = ()
    max_records: int = Field(default=40, ge=1, le=200)


class ResolvedWorldView(BaseModel):
    """A model-free receipt of semantic records selected for one task."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    view_id: str = Field(min_length=1)
    status: WorldViewStatus
    request_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    state_ids: tuple[str, ...] = ()
    perspective_ids: tuple[str, ...] = ()
    relationship_frame_ids: tuple[str, ...] = ()
    hypothesis_ids: tuple[str, ...] = ()
    experiment_ids: tuple[str, ...] = ()
    observed_outcome_ids: tuple[str, ...] = ()
    learning_update_ids: tuple[str, ...] = ()
    evidence_link_ids: tuple[str, ...] = ()
    unresolved_conflict_ids: tuple[str, ...] = ()
    selected_record_ids: tuple[str, ...] = ()
    omissions: tuple[str, ...] = ()
    route_receipt: tuple[str, ...] = ()
    derivation_id: str | None = None


def compile_world_view(
    request: WorldViewRequest,
    *,
    branches: tuple[WorldBranch, ...],
    deltas: tuple[BranchDelta, ...],
    states: tuple[StateSnapshot, ...],
    perspectives: tuple[PerspectiveProfile, ...],
    relationship_frames: tuple[RelationshipFrame, ...],
    hypotheses: tuple[HypothesisRecord, ...] = (),
    experiments: tuple[ExperimentPlan, ...] = (),
    observed_outcomes: tuple[ObservedOutcome, ...] = (),
    learning_updates: tuple[LearningUpdate, ...] = (),
    conflicts: tuple[BranchConflict, ...] = (),
) -> ResolvedWorldView:
    """Select exact-context records and resolve branch deltas before model use.

    This is intentionally conservative: it uses exact context IDs. Broader
    applicability expansion belongs to a retrieval adapter with a recorded
    policy, not to this compiler.
    """

    base_record_ids = tuple(
        [state.state_id for state in states if state.context_id == request.context_id]
        + [
            perspective.perspective_id
            for perspective in perspectives
            if perspective.context_id == request.context_id
        ]
        + [
            frame.frame_id
            for frame in relationship_frames
            if frame.context_id == request.context_id
        ]
        + [
            hypothesis.hypothesis_id
            for hypothesis in hypotheses
            if hypothesis.context_id == request.context_id
            and hypothesis.branch_id == request.branch_id
        ]
        + [
            experiment.experiment_id
            for experiment in experiments
            if experiment.context_id == request.context_id
            and experiment.branch_id == request.branch_id
        ]
    )
    try:
        branch_record_ids = resolve_branch_records(
            branch_id=request.branch_id,
            branches=branches,
            deltas=deltas,
            base_record_ids=base_record_ids,
        )
    except ValueError as exc:
        return ResolvedWorldView(
            view_id=f"world-view:{request.request_id}",
            status=WorldViewStatus.HOLD,
            request_id=request.request_id,
            workspace_id=request.workspace_id,
            context_id=request.context_id,
            branch_id=request.branch_id,
            omissions=(str(exc),),
            route_receipt=("branch resolution held before retrieval",),
        )

    allowed = set(request.permitted_record_ids) if request.permitted_record_ids else None
    requested_perspectives = set(request.perspective_ids)
    perspective_record_ids = {perspective.perspective_id for perspective in perspectives}
    selected = [
        record_id
        for record_id in branch_record_ids
        if (allowed is None or record_id in allowed)
        and (record_id not in perspective_record_ids or record_id in requested_perspectives)
    ]
    selected = selected[: request.max_records]
    state_ids = tuple(state.state_id for state in states if state.state_id in selected)
    perspective_ids = tuple(
        perspective.perspective_id
        for perspective in perspectives
        if perspective.perspective_id in selected
        and (not requested_perspectives or perspective.perspective_id in requested_perspectives)
    )
    frame_ids = tuple(frame.frame_id for frame in relationship_frames if frame.frame_id in selected)
    hypothesis_ids = tuple(
        hypothesis.hypothesis_id
        for hypothesis in hypotheses
        if hypothesis.hypothesis_id in selected
    )
    experiment_ids = tuple(
        experiment.experiment_id
        for experiment in experiments
        if experiment.experiment_id in selected
    )
    outcome_ids = tuple(
        outcome.outcome_id
        for outcome in observed_outcomes
        if outcome.context_id == request.context_id and outcome.experiment_id in experiment_ids
    )
    learning_ids = tuple(
        learning.learning_id
        for learning in learning_updates
        if learning.context_id == request.context_id
        and learning.hypothesis_id in hypothesis_ids
        and set(learning.outcome_ids).issubset(outcome_ids)
    )
    selected = [*selected, *outcome_ids, *learning_ids][: request.max_records]
    state_evidence_link_ids = tuple(
        dict.fromkeys(
            link_id
            for state in states
            if state.state_id in state_ids
            for link_id in state.evidence_link_ids
        )
    )
    frame_evidence_link_ids = tuple(
        link_id
        for frame in relationship_frames
        if frame.frame_id in frame_ids
        for link_id in frame.evidence_link_ids
        if link_id not in state_evidence_link_ids
    )
    hypothesis_evidence_link_ids = tuple(
        link_id
        for hypothesis in hypotheses
        if hypothesis.hypothesis_id in hypothesis_ids
        for link_id in (
            *hypothesis.input_evidence_link_ids,
            *hypothesis.supporting_evidence_link_ids,
            *hypothesis.opposing_evidence_link_ids,
        )
        if link_id not in state_evidence_link_ids + frame_evidence_link_ids
    )
    outcome_evidence_link_ids = tuple(
        link_id
        for outcome in observed_outcomes
        if outcome.outcome_id in outcome_ids
        for link_id in outcome.evidence_link_ids
        if link_id
        not in state_evidence_link_ids + frame_evidence_link_ids + hypothesis_evidence_link_ids
    )
    evidence_link_ids = (
        state_evidence_link_ids
        + frame_evidence_link_ids
        + hypothesis_evidence_link_ids
        + outcome_evidence_link_ids
    )
    unresolved = tuple(
        conflict.conflict_id
        for conflict in conflicts
        if conflict.branch_id == request.branch_id and conflict.context_id == request.context_id
    )
    omissions: list[str] = []
    if requested_perspectives - set(perspective_ids):
        omissions.append(
            "one or more requested perspectives are unavailable in this branch/context"
        )
    if len(branch_record_ids) > request.max_records:
        omissions.append("record budget reached; additional branch records were omitted")
    if not selected:
        status = WorldViewStatus.NO_HIT
        omissions.append("no canonical records match the requested context and branch")
    elif omissions or unresolved:
        status = WorldViewStatus.PARTIAL
    else:
        status = WorldViewStatus.HIT
    return ResolvedWorldView(
        view_id=f"world-view:{request.request_id}",
        status=status,
        request_id=request.request_id,
        workspace_id=request.workspace_id,
        context_id=request.context_id,
        branch_id=request.branch_id,
        state_ids=state_ids,
        perspective_ids=perspective_ids,
        relationship_frame_ids=frame_ids,
        hypothesis_ids=hypothesis_ids,
        experiment_ids=experiment_ids,
        observed_outcome_ids=outcome_ids,
        learning_update_ids=learning_ids,
        evidence_link_ids=evidence_link_ids,
        unresolved_conflict_ids=unresolved,
        selected_record_ids=tuple(selected),
        omissions=tuple(omissions),
        route_receipt=(
            "exact context selection",
            "branch overlay resolved before model synthesis",
            "record budget enforced",
        ),
    )


__all__ = [
    "ResolvedWorldView",
    "WorldViewRequest",
    "WorldViewStatus",
    "compile_world_view",
]
