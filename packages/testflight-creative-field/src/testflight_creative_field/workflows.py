"""Proposal-producing observation and interpretation workflows.

These workflows prepare bounded context, call a provider-neutral operator executor and validate
the returned proposal. They never infer meaning locally and never promote a proposal to canonical
state; persistence is the caller's responsibility.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from .models import (
    ArtifactStatus,
    BoardRevision,
    FieldDimension,
    InterpretationAlternative,
    LifecycleStatus,
    ObservedFeature,
    ReferenceAsset,
    ReferenceContribution,
    ReferenceInterpretation,
    SourceLicenseRecord,
    TransferPolarity,
    UserAnnotation,
)

OBSERVE_OPERATOR_ID = "world://operator/creative/observation-extraction"
INTERPRET_OPERATOR_ID = "world://operator/creative/reference-interpretation"


@dataclass(frozen=True, slots=True)
class OperatorExecution:
    """Normalized result expected from any runtime/provider adapter."""

    status: str
    output: Any = None
    receipt: Mapping[str, Any] = field(default_factory=dict)
    errors: tuple[str, ...] = ()
    hold_reason: str | None = None


class OperatorExecutor(Protocol):
    """Small seam implemented by the TypeScript runtime bridge, a fake, or a human reviewer."""

    def execute(self, request: Mapping[str, Any]) -> OperatorExecution: ...


@dataclass(frozen=True, slots=True)
class WorkflowResult:
    """Typed workflow result; non-success outcomes retain no fabricated records."""

    status: ArtifactStatus
    records: tuple[Any, ...] = ()
    errors: tuple[str, ...] = ()
    hold_reason: str | None = None
    receipt: Mapping[str, Any] = field(default_factory=dict)


def _artifact_status(status: str) -> ArtifactStatus:
    return {
        "proposal": ArtifactStatus.SUCCESS,
        "success": ArtifactStatus.SUCCESS,
        "partial": ArtifactStatus.PARTIAL,
        "hold": ArtifactStatus.HELD,
        "ask": ArtifactStatus.HELD,
        "branch": ArtifactStatus.PARTIAL,
        "no_hit": ArtifactStatus.UNAVAILABLE,
        "unavailable": ArtifactStatus.UNAVAILABLE,
        "failed": ArtifactStatus.FAILED,
    }.get(status, ArtifactStatus.FAILED)


def _non_success(execution: OperatorExecution) -> WorkflowResult:
    return WorkflowResult(
        status=_artifact_status(execution.status),
        errors=execution.errors,
        hold_reason=execution.hold_reason,
        receipt=execution.receipt,
    )


def _as_strings(value: Any) -> tuple[str, ...]:
    return (
        tuple(item for item in value if isinstance(item, str) and item.strip())
        if isinstance(value, list | tuple)
        else ()
    )


def _allowed_for_analysis(license_record: SourceLicenseRecord) -> bool:
    if not license_record.permitted_use:
        return False
    allowed = {item.lower() for item in license_record.permitted_use}
    return bool(
        allowed
        & {
            "analysis",
            "analysis_only",
            "analysis_and_reference",
            "reference",
            "generation",
            "production",
        }
    )


class ReferenceObservationWorkflow:
    """Observe one bounded asset and return typed ObservedFeature proposals."""

    def run(
        self,
        *,
        asset: ReferenceAsset,
        board: BoardRevision,
        annotations: Iterable[UserAnnotation],
        license_record: SourceLicenseRecord,
        dimensions: Sequence[FieldDimension],
        project_purpose: str,
        derivation_id: str,
        executor: OperatorExecutor,
        configuration: Mapping[str, Any] | None = None,
    ) -> WorkflowResult:
        if asset.project_id != board.project_id:
            return WorkflowResult(
                status=ArtifactStatus.HELD,
                errors=("asset and board project scope differ",),
                hold_reason="scope_mismatch",
            )
        if not _allowed_for_analysis(license_record):
            return WorkflowResult(
                status=ArtifactStatus.HELD,
                errors=("source is not cleared for analysis",),
                hold_reason="rights_missing",
            )
        board_placement = tuple(
            item.model_dump(mode="json")
            for item in board.placements
            if item.asset_id == asset.asset_id
        )
        annotation_payload = tuple(
            {
                "annotation_id": item.annotation_id,
                "target_id": item.target_id,
                "text": item.text,
                "desired_transfer": item.desired_transfer,
                "anti_association": item.anti_association,
            }
            for item in annotations
            if item.project_id == asset.project_id
            and item.target_id in {asset.asset_id, board.moodboard_id}
        )
        request = {
            "operator_id": OBSERVE_OPERATOR_ID,
            "operator_version": 1,
            "operation_key": f"observe:{asset.asset_id}:{derivation_id}",
            "modality": asset.media_type,
            "project_id": asset.project_id,
            "input": {
                "project_purpose": project_purpose,
                "asset": asset.model_dump(mode="json"),
                "placement": board_placement,
                "annotations": annotation_payload,
                "dimensions": [item.model_dump(mode="json") for item in dimensions],
                "content_is_untrusted": True,
            },
            "disclosure_refs": [license_record.license_record_id, asset.source_id],
            "configuration": dict(configuration or {}),
        }
        execution = executor.execute(request)
        if (
            _artifact_status(execution.status) is not ArtifactStatus.SUCCESS
            and _artifact_status(execution.status) is not ArtifactStatus.PARTIAL
        ):
            return _non_success(execution)
        if not isinstance(execution.output, Mapping):
            return WorkflowResult(
                status=ArtifactStatus.FAILED,
                errors=("observation operator returned a non-object",),
                receipt=execution.receipt,
            )
        raw_features = execution.output.get("observed_features", execution.output.get("features"))
        if not isinstance(raw_features, list):
            return WorkflowResult(
                status=ArtifactStatus.FAILED,
                errors=("observation output is missing observed_features",),
                receipt=execution.receipt,
            )
        records: list[ObservedFeature] = []
        for position, raw in enumerate(raw_features, start=1):
            if not isinstance(raw, Mapping):
                return WorkflowResult(
                    status=ArtifactStatus.FAILED,
                    errors=("observation feature is not an object",),
                    receipt=execution.receipt,
                )
            anchors = _as_strings(raw.get("bounded_anchors", raw.get("anchors")))
            if not anchors:
                return WorkflowResult(
                    status=ArtifactStatus.HELD,
                    errors=(f"observation feature {position} has no exact evidence anchor",),
                    hold_reason="evidence_anchor_missing",
                    receipt=execution.receipt,
                )
            label = raw.get("label")
            dimension_id = raw.get("dimension_id")
            if (
                not isinstance(label, str)
                or not label.strip()
                or not isinstance(dimension_id, str)
                or not dimension_id.strip()
            ):
                return WorkflowResult(
                    status=ArtifactStatus.FAILED,
                    errors=(f"observation feature {position} has invalid identity",),
                    receipt=execution.receipt,
                )
            records.append(
                ObservedFeature(
                    feature_id=str(raw.get("feature_id") or f"{derivation_id}:feature:{position}"),
                    observation_id=str(raw.get("observation_id") or f"{derivation_id}:observation"),
                    project_id=asset.project_id,
                    reference_asset_id=asset.asset_id,
                    dimension_id=dimension_id,
                    label=label,
                    value=raw.get("value"),
                    bounded_anchors=anchors,
                    observation_status=LifecycleStatus.PROPOSED,
                    uncertainty=raw.get("uncertainty")
                    if isinstance(raw.get("uncertainty"), str)
                    else None,
                    source_ids=(asset.source_id,),
                    derivation_id=derivation_id,
                )
            )
        return WorkflowResult(
            status=ArtifactStatus.PARTIAL
            if _artifact_status(execution.status) is ArtifactStatus.PARTIAL
            else ArtifactStatus.SUCCESS,
            records=tuple(records),
            receipt=execution.receipt,
        )


class ReferenceInterpretationWorkflow:
    """Interpret observations for one project while retaining alternatives and anti-transfer."""

    def run(
        self,
        *,
        asset: ReferenceAsset,
        observations: Sequence[ObservedFeature],
        annotations: Iterable[UserAnnotation],
        project_purpose: str,
        derivation_id: str,
        executor: OperatorExecutor,
        configuration: Mapping[str, Any] | None = None,
    ) -> WorkflowResult:
        if not observations:
            return WorkflowResult(
                status=ArtifactStatus.UNAVAILABLE,
                errors=("interpretation requires at least one observation",),
                hold_reason="no_observations",
            )
        if any(
            item.project_id != asset.project_id or item.reference_asset_id != asset.asset_id
            for item in observations
        ):
            return WorkflowResult(
                status=ArtifactStatus.HELD,
                errors=("observation scope does not match asset",),
                hold_reason="scope_mismatch",
            )
        annotation_payload = tuple(
            item.model_dump(mode="json")
            for item in annotations
            if item.project_id == asset.project_id and item.target_id in {asset.asset_id}
        )
        request = {
            "operator_id": INTERPRET_OPERATOR_ID,
            "operator_version": 1,
            "operation_key": f"interpret:{asset.asset_id}:{derivation_id}",
            "modality": asset.media_type,
            "project_id": asset.project_id,
            "input": {
                "project_purpose": project_purpose,
                "asset_id": asset.asset_id,
                "observations": [item.model_dump(mode="json") for item in observations],
                "annotations": annotation_payload,
                "content_is_untrusted": True,
            },
            "disclosure_refs": [
                asset.source_id,
                *[anchor for item in observations for anchor in item.bounded_anchors],
            ],
            "configuration": dict(configuration or {}),
        }
        execution = executor.execute(request)
        if (
            _artifact_status(execution.status) is not ArtifactStatus.SUCCESS
            and _artifact_status(execution.status) is not ArtifactStatus.PARTIAL
        ):
            return _non_success(execution)
        if not isinstance(execution.output, Mapping):
            return WorkflowResult(
                status=ArtifactStatus.FAILED,
                errors=("interpretation operator returned a non-object",),
                receipt=execution.receipt,
            )
        raw = execution.output
        evidence_refs = _as_strings(raw.get("evidence_refs"))
        if not evidence_refs:
            return WorkflowResult(
                status=ArtifactStatus.HELD,
                errors=("interpretation has no evidence references",),
                hold_reason="evidence_missing",
                receipt=execution.receipt,
            )
        proposed_role = raw.get("proposed_role", raw.get("role"))
        authority = raw.get("authority", "operator-proposal")
        if (
            not isinstance(proposed_role, str)
            or not proposed_role.strip()
            or not isinstance(authority, str)
            or not authority.strip()
        ):
            return WorkflowResult(
                status=ArtifactStatus.FAILED,
                errors=("interpretation role or authority is invalid",),
                receipt=execution.receipt,
            )
        raw_contributions = raw.get("dimension_contributions", raw.get("contributions", []))
        if not isinstance(raw_contributions, list):
            return WorkflowResult(
                status=ArtifactStatus.FAILED,
                errors=("dimension_contributions must be a list",),
                receipt=execution.receipt,
            )
        contributions: list[ReferenceContribution] = []
        for position, item in enumerate(raw_contributions, start=1):
            if not isinstance(item, Mapping):
                return WorkflowResult(
                    status=ArtifactStatus.FAILED,
                    errors=(f"contribution {position} is not an object",),
                    receipt=execution.receipt,
                )
            dimension_id = item.get("dimension_id")
            role = item.get("role")
            transfer = item.get("transfer_instruction", item.get("transfer"))
            anti_transfer = item.get("anti_transfer_instruction", item.get("anti_transfer"))
            if not all(
                isinstance(value, str) and value.strip()
                for value in (dimension_id, role, transfer, anti_transfer)
            ):
                return WorkflowResult(
                    status=ArtifactStatus.FAILED,
                    errors=(f"contribution {position} is incomplete",),
                    receipt=execution.receipt,
                )
            contribution_evidence = _as_strings(item.get("evidence_refs")) or evidence_refs
            try:
                contributions.append(
                    ReferenceContribution(
                        contribution_id=str(
                            item.get("contribution_id")
                            or f"{derivation_id}:contribution:{position}"
                        ),
                        interpretation_id=f"{derivation_id}:interpretation",
                        reference_asset_id=asset.asset_id,
                        dimension_id=dimension_id,
                        role=role,
                        transfer_instruction=transfer,
                        anti_transfer_instruction=anti_transfer,
                        polarity=TransferPolarity(str(item.get("polarity", "contextual"))),
                        weight=float(item.get("weight", 0.5)),
                        evidence_refs=contribution_evidence,
                        derivation_id=derivation_id,
                    )
                )
            except (TypeError, ValueError) as error:
                return WorkflowResult(
                    status=ArtifactStatus.FAILED,
                    errors=(f"contribution {position} is invalid: {error}",),
                    receipt=execution.receipt,
                )
        alternatives = tuple(
            InterpretationAlternative(
                alternative_id=str(
                    item.get("alternative_id") or f"{derivation_id}:alternative:{position}"
                ),
                interpretation_id=f"{derivation_id}:interpretation",
                proposition=item["proposition"],
                rationale=item["rationale"],
                evidence_refs=_as_strings(item.get("evidence_refs")),
            )
            for position, item in enumerate(raw.get("alternatives", []), start=1)
            if isinstance(item, Mapping)
            and isinstance(item.get("proposition"), str)
            and isinstance(item.get("rationale"), str)
        )
        interpretation = ReferenceInterpretation(
            interpretation_id=f"{derivation_id}:interpretation",
            project_id=asset.project_id,
            reference_asset_id=asset.asset_id,
            observation_ids=tuple(item.observation_id for item in observations),
            proposed_role=proposed_role,
            dimension_contributions=tuple(contributions),
            carry_forward=_as_strings(raw.get("carry_forward")),
            anti_transfer=_as_strings(raw.get("anti_transfer")),
            alternatives=alternatives,
            questions=_as_strings(raw.get("questions")),
            evidence_refs=evidence_refs,
            authority=authority,
            derivation_id=derivation_id,
        )
        return WorkflowResult(
            status=ArtifactStatus.PARTIAL
            if _artifact_status(execution.status) is ArtifactStatus.PARTIAL
            else ArtifactStatus.SUCCESS,
            records=(interpretation, *contributions),
            receipt=execution.receipt,
        )


__all__ = [
    "INTERPRET_OPERATOR_ID",
    "OBSERVE_OPERATOR_ID",
    "OperatorExecution",
    "OperatorExecutor",
    "ReferenceInterpretationWorkflow",
    "ReferenceObservationWorkflow",
    "WorkflowResult",
]
