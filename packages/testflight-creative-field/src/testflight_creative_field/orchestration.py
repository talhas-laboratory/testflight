"""Provider-neutral orchestration for a project-scoped Creative Field run.

The coordinator deliberately stops at a reviewable field proposal. It composes the existing
typed workflows, persists only validated records, and keeps provider transport outside the domain
package.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .lifecycle import CreativeFieldLifecycle
from .models import (
    ArtifactStatus,
    BoardRevision,
    CreativeFieldProposal,
    CreativeFieldVersion,
    FieldDimension,
    ObservedFeature,
    ReferenceAsset,
    ReferenceContribution,
    ReferenceInterpretation,
    SourceLicenseRecord,
    UserAnnotation,
)
from .ports import CreativeRecordRepository
from .workflows import (
    OperatorExecutor,
    ReferenceInterpretationWorkflow,
    ReferenceObservationWorkflow,
    WorkflowResult,
)

_SUCCESSFUL_STATUSES = {ArtifactStatus.SUCCESS, ArtifactStatus.PARTIAL}


@dataclass(frozen=True, slots=True)
class CreativeFieldStageResult:
    """Inspectable outcome for one stage or one reference."""

    stage: str
    subject_id: str | None
    status: ArtifactStatus
    record_ids: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    hold_reason: str | None = None
    receipt: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CreativeFieldRunResult:
    """Result of a synchronous proposal-producing run."""

    run_id: str
    project_id: str
    moodboard_id: str
    board_revision_id: str | None
    status: ArtifactStatus
    stages: tuple[CreativeFieldStageResult, ...] = ()
    proposal: CreativeFieldProposal | None = None
    errors: tuple[str, ...] = ()
    hold_reason: str | None = None

    @property
    def proposal_id(self) -> str | None:
        return self.proposal.proposal_id if self.proposal else None


class CreativeFieldRunCoordinator:
    """Compose board evidence through observation, interpretation and field synthesis.

    The coordinator has no model-provider dependency. An application supplies an
    :class:`OperatorExecutor` implementation and a canonical repository. Every stage remains
    proposal-only; review and version promotion are separate lifecycle operations.
    """

    def __init__(
        self,
        *,
        repository: CreativeRecordRepository,
        project_id: str,
        project_purpose: str,
        dimensions: Sequence[FieldDimension],
        executor: OperatorExecutor,
        field_id: str | None = None,
        operator_configuration: Mapping[str, Any] | None = None,
    ) -> None:
        if not project_id.strip():
            raise ValueError("project_id is required")
        if not project_purpose.strip():
            raise ValueError("project_purpose is required")
        self.repository = repository
        self.project_id = project_id
        self.project_purpose = project_purpose
        self.dimensions = tuple(dimensions)
        self.executor = executor
        self.field_id = field_id or f"field:{project_id.removeprefix('project:')}"
        self.operator_configuration = dict(operator_configuration or {})
        self._observation = ReferenceObservationWorkflow()
        self._interpretation = ReferenceInterpretationWorkflow()
        self._lifecycle = CreativeFieldLifecycle()

    def run(
        self,
        *,
        run_id: str,
        moodboard_id: str,
        derivation_id: str | None = None,
        parent_version: CreativeFieldVersion | None = None,
    ) -> CreativeFieldRunResult:
        """Run the latest board revision and persist validated proposal records.

        Missing rights or records are held before an executor call. If any reference stage is
        held, unavailable, or failed, valid upstream records remain persisted but synthesis is not
        attempted; this prevents a partial board from masquerading as a complete field.
        """

        if not run_id.strip():
            raise ValueError("run_id is required")
        if not moodboard_id.strip():
            raise ValueError("moodboard_id is required")
        base_derivation = derivation_id or f"derivation:creative-field:{run_id}"
        stages: list[CreativeFieldStageResult] = []
        revisions = tuple(self.repository.replay_board(moodboard_id))
        if not revisions:
            return CreativeFieldRunResult(
                run_id=run_id,
                project_id=self.project_id,
                moodboard_id=moodboard_id,
                board_revision_id=None,
                status=ArtifactStatus.UNAVAILABLE,
                stages=(
                    CreativeFieldStageResult(
                        stage="board",
                        subject_id=moodboard_id,
                        status=ArtifactStatus.UNAVAILABLE,
                        errors=("moodboard has no persisted board revision",),
                        hold_reason="board_empty",
                    ),
                ),
                errors=("moodboard has no persisted board revision",),
                hold_reason="board_empty",
            )

        board = max(revisions, key=lambda item: item.revision)
        if board.project_id != self.project_id:
            return self._held_result(
                run_id=run_id,
                moodboard_id=moodboard_id,
                board=board,
                stage="board",
                error="board project scope differs",
                hold_reason="scope_mismatch",
            )

        annotations = tuple(self.repository.list(UserAnnotation, project_id=self.project_id))
        interpretations: list[ReferenceInterpretation] = []
        contributions: list[ReferenceContribution] = []
        blocked_statuses: list[ArtifactStatus] = []

        for asset_id in board.reference_asset_ids:
            asset = self.repository.get(ReferenceAsset, asset_id)
            if asset is None:
                stage = self._blocked_stage(
                    stage="observation",
                    subject_id=asset_id,
                    status=ArtifactStatus.HELD,
                    error="reference asset is missing from canonical storage",
                    hold_reason="asset_missing",
                )
                stages.append(stage)
                blocked_statuses.append(stage.status)
                continue
            if asset.project_id != self.project_id:
                stage = self._blocked_stage(
                    stage="observation",
                    subject_id=asset.asset_id,
                    status=ArtifactStatus.HELD,
                    error="reference asset project scope differs",
                    hold_reason="scope_mismatch",
                )
                stages.append(stage)
                blocked_statuses.append(stage.status)
                continue
            license_record = self._license_for(asset)
            if license_record is None:
                stage = self._blocked_stage(
                    stage="observation",
                    subject_id=asset.asset_id,
                    status=ArtifactStatus.HELD,
                    error="reference source is not cleared for analysis",
                    hold_reason="rights_missing",
                )
                stages.append(stage)
                blocked_statuses.append(stage.status)
                continue

            observation_derivation = f"{base_derivation}:observe:{asset.asset_id}"
            try:
                observed = self._observation.run(
                    asset=asset,
                    board=board,
                    annotations=annotations,
                    license_record=license_record,
                    dimensions=self.dimensions,
                    project_purpose=self.project_purpose,
                    derivation_id=observation_derivation,
                    executor=self.executor,
                    configuration=self.operator_configuration,
                )
            except Exception as error:  # noqa: BLE001 - normalize executor boundary failures.
                stage = self._blocked_stage(
                    stage="observation",
                    subject_id=asset.asset_id,
                    status=ArtifactStatus.FAILED,
                    error=f"observation executor failed: {error}",
                )
                stages.append(stage)
                blocked_statuses.append(stage.status)
                continue
            observation_stage = self._workflow_stage("observation", asset.asset_id, observed)
            if observation_stage.status in _SUCCESSFUL_STATUSES and observed.records:
                try:
                    self.repository.append_many(observed.records)
                except Exception as error:  # noqa: BLE001 - persistence is a workflow boundary.
                    observation_stage = self._blocked_stage(
                        stage="observation",
                        subject_id=asset.asset_id,
                        status=ArtifactStatus.FAILED,
                        error=f"observation persistence failed: {error}",
                        receipt=observed.receipt,
                    )
            stages.append(observation_stage)
            if observation_stage.status not in _SUCCESSFUL_STATUSES:
                blocked_statuses.append(observation_stage.status)
                continue
            observed_features = tuple(
                item for item in observed.records if isinstance(item, ObservedFeature)
            )
            if not observed_features:
                stage = self._blocked_stage(
                    stage="interpretation",
                    subject_id=asset.asset_id,
                    status=ArtifactStatus.HELD,
                    error="observation returned no typed features",
                    hold_reason="observations_missing",
                )
                stages.append(stage)
                blocked_statuses.append(stage.status)
                continue

            interpretation_derivation = f"{base_derivation}:interpret:{asset.asset_id}"
            try:
                interpreted = self._interpretation.run(
                    asset=asset,
                    observations=observed_features,
                    annotations=annotations,
                    project_purpose=self.project_purpose,
                    derivation_id=interpretation_derivation,
                    executor=self.executor,
                    configuration=self.operator_configuration,
                )
            except Exception as error:  # noqa: BLE001 - normalize executor boundary failures.
                stage = self._blocked_stage(
                    stage="interpretation",
                    subject_id=asset.asset_id,
                    status=ArtifactStatus.FAILED,
                    error=f"interpretation executor failed: {error}",
                )
                stages.append(stage)
                blocked_statuses.append(stage.status)
                continue
            interpretation_stage = self._workflow_stage(
                "interpretation", asset.asset_id, interpreted
            )
            if interpretation_stage.status in _SUCCESSFUL_STATUSES and interpreted.records:
                try:
                    self.repository.append_many(interpreted.records)
                except Exception as error:  # noqa: BLE001 - persistence is a workflow boundary.
                    interpretation_stage = self._blocked_stage(
                        stage="interpretation",
                        subject_id=asset.asset_id,
                        status=ArtifactStatus.FAILED,
                        error=f"interpretation persistence failed: {error}",
                        receipt=interpreted.receipt,
                    )
            stages.append(interpretation_stage)
            if interpretation_stage.status not in _SUCCESSFUL_STATUSES:
                blocked_statuses.append(interpretation_stage.status)
                continue
            if not interpreted.records or not isinstance(
                interpreted.records[0], ReferenceInterpretation
            ):
                stage = self._blocked_stage(
                    stage="interpretation",
                    subject_id=asset.asset_id,
                    status=ArtifactStatus.FAILED,
                    error="interpretation returned no typed interpretation",
                    receipt=interpreted.receipt,
                )
                stages.append(stage)
                blocked_statuses.append(stage.status)
                continue
            interpretations.append(interpreted.records[0])
            contributions.extend(
                item for item in interpreted.records[1:] if isinstance(item, ReferenceContribution)
            )

        if blocked_statuses:
            status = self._blocked_status(blocked_statuses)
            errors = tuple(error for stage in stages for error in stage.errors)
            return CreativeFieldRunResult(
                run_id=run_id,
                project_id=self.project_id,
                moodboard_id=moodboard_id,
                board_revision_id=board.board_revision_id,
                status=status,
                stages=tuple(stages),
                errors=errors,
                hold_reason=self._hold_reason(stages),
            )
        if not interpretations or not contributions:
            stage = self._blocked_stage(
                stage="synthesis",
                subject_id=self.field_id,
                status=ArtifactStatus.UNAVAILABLE,
                error="no typed interpretations or contributions are available",
                hold_reason="no_contributions",
            )
            stages.append(stage)
            return CreativeFieldRunResult(
                run_id=run_id,
                project_id=self.project_id,
                moodboard_id=moodboard_id,
                board_revision_id=board.board_revision_id,
                status=stage.status,
                stages=tuple(stages),
                errors=stage.errors,
                hold_reason=stage.hold_reason,
            )

        synthesis_derivation = f"{base_derivation}:synthesize"
        try:
            synthesis = self._lifecycle.synthesize(
                project_id=self.project_id,
                field_id=self.field_id,
                interpretations=tuple(interpretations),
                contributions=tuple(contributions),
                dimensions=self.dimensions,
                project_purpose=self.project_purpose,
                derivation_id=synthesis_derivation,
                executor=self.executor,
                parent_version=parent_version,
                configuration=self.operator_configuration,
            )
        except Exception as error:  # noqa: BLE001 - normalize executor boundary failures.
            stage = self._blocked_stage(
                stage="synthesis",
                subject_id=self.field_id,
                status=ArtifactStatus.FAILED,
                error=f"field synthesis executor failed: {error}",
            )
            stages.append(stage)
            return CreativeFieldRunResult(
                run_id=run_id,
                project_id=self.project_id,
                moodboard_id=moodboard_id,
                board_revision_id=board.board_revision_id,
                status=stage.status,
                stages=tuple(stages),
                errors=stage.errors,
            )
        synthesis_stage = self._workflow_stage("synthesis", self.field_id, synthesis)
        if synthesis_stage.status in _SUCCESSFUL_STATUSES and synthesis.proposal is not None:
            try:
                self.repository.append(synthesis.proposal)
            except Exception as error:  # noqa: BLE001 - persistence is a workflow boundary.
                synthesis_stage = self._blocked_stage(
                    stage="synthesis",
                    subject_id=self.field_id,
                    status=ArtifactStatus.FAILED,
                    error=f"field proposal persistence failed: {error}",
                    receipt=synthesis.receipt,
                )
        stages.append(synthesis_stage)
        errors = tuple(error for stage in stages for error in stage.errors)
        if synthesis_stage.status not in _SUCCESSFUL_STATUSES or synthesis.proposal is None:
            return CreativeFieldRunResult(
                run_id=run_id,
                project_id=self.project_id,
                moodboard_id=moodboard_id,
                board_revision_id=board.board_revision_id,
                status=synthesis_stage.status,
                stages=tuple(stages),
                errors=errors,
                hold_reason=synthesis_stage.hold_reason,
            )
        return CreativeFieldRunResult(
            run_id=run_id,
            project_id=self.project_id,
            moodboard_id=moodboard_id,
            board_revision_id=board.board_revision_id,
            status=(
                ArtifactStatus.PARTIAL
                if any(stage.status is ArtifactStatus.PARTIAL for stage in stages)
                else ArtifactStatus.SUCCESS
            ),
            stages=tuple(stages),
            proposal=synthesis.proposal,
            errors=errors,
        )

    def _license_for(self, asset: ReferenceAsset) -> SourceLicenseRecord | None:
        if not asset.license_record_id:
            return None
        license_record = self.repository.get(SourceLicenseRecord, asset.license_record_id)
        if license_record is None or license_record.source_id != asset.source_id:
            return None
        return license_record

    @staticmethod
    def _record_ids(records: Sequence[Any]) -> tuple[str, ...]:
        fields = (
            "feature_id",
            "interpretation_id",
            "contribution_id",
            "proposal_id",
        )
        ids: list[str] = []
        for record in records:
            for field_name in fields:
                record_id = getattr(record, field_name, None)
                if isinstance(record_id, str):
                    ids.append(record_id)
                    break
        return tuple(ids)

    def _workflow_stage(
        self, stage: str, subject_id: str, result: WorkflowResult | Any
    ) -> CreativeFieldStageResult:
        return CreativeFieldStageResult(
            stage=stage,
            subject_id=subject_id,
            status=result.status,
            record_ids=self._record_ids(result.records)
            if hasattr(result, "records")
            else ((result.proposal.proposal_id,) if result.proposal else ()),
            errors=result.errors,
            hold_reason=result.hold_reason,
            receipt=result.receipt,
        )

    @staticmethod
    def _blocked_stage(
        *,
        stage: str,
        subject_id: str | None,
        status: ArtifactStatus,
        error: str,
        hold_reason: str | None = None,
        receipt: Mapping[str, Any] | None = None,
    ) -> CreativeFieldStageResult:
        return CreativeFieldStageResult(
            stage=stage,
            subject_id=subject_id,
            status=status,
            errors=(error,),
            hold_reason=hold_reason,
            receipt=receipt or {},
        )

    def _held_result(
        self,
        *,
        run_id: str,
        moodboard_id: str,
        board: BoardRevision,
        stage: str,
        error: str,
        hold_reason: str,
    ) -> CreativeFieldRunResult:
        stage_result = self._blocked_stage(
            stage=stage,
            subject_id=moodboard_id,
            status=ArtifactStatus.HELD,
            error=error,
            hold_reason=hold_reason,
        )
        return CreativeFieldRunResult(
            run_id=run_id,
            project_id=self.project_id,
            moodboard_id=moodboard_id,
            board_revision_id=board.board_revision_id,
            status=stage_result.status,
            stages=(stage_result,),
            errors=stage_result.errors,
            hold_reason=stage_result.hold_reason,
        )

    @staticmethod
    def _blocked_status(statuses: Sequence[ArtifactStatus]) -> ArtifactStatus:
        if ArtifactStatus.FAILED in statuses:
            return ArtifactStatus.FAILED
        if ArtifactStatus.HELD in statuses:
            return ArtifactStatus.HELD
        if ArtifactStatus.UNAVAILABLE in statuses:
            return ArtifactStatus.UNAVAILABLE
        return ArtifactStatus.PARTIAL

    @staticmethod
    def _hold_reason(stages: Sequence[CreativeFieldStageResult]) -> str | None:
        return next((stage.hold_reason for stage in stages if stage.hold_reason), None)


__all__ = [
    "CreativeFieldRunCoordinator",
    "CreativeFieldRunResult",
    "CreativeFieldStageResult",
]
