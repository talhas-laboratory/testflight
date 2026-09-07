"""Provider-result normalization for creative evaluation and feedback proposals."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .models import ArtifactStatus, CreativeEvaluation, FeedbackRecord
from .workflows import OperatorExecution

OUTPUT_EVALUATION_OPERATOR_ID = "world://operator/creative/output-evaluation"


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    status: ArtifactStatus
    evaluation: CreativeEvaluation | None = None
    feedback: tuple[FeedbackRecord, ...] = ()
    errors: tuple[str, ...] = ()
    hold_reason: str | None = None
    receipt: Mapping[str, Any] = field(default_factory=dict)


def _status(value: str) -> ArtifactStatus:
    return {
        "proposal": ArtifactStatus.SUCCESS,
        "success": ArtifactStatus.SUCCESS,
        "partial": ArtifactStatus.PARTIAL,
        "branch": ArtifactStatus.PARTIAL,
        "hold": ArtifactStatus.HELD,
        "ask": ArtifactStatus.HELD,
        "no_hit": ArtifactStatus.UNAVAILABLE,
        "failed": ArtifactStatus.FAILED,
    }.get(value, ArtifactStatus.FAILED)


class CreativeEvaluationWorkflow:
    """Normalize an independently produced evaluation; never score locally or mutate state."""

    def run(
        self,
        *,
        execution: OperatorExecution,
        output_id: str,
        request_id: str,
        field_version_id: str,
        projection_id: str,
        derivation_id: str,
        actor_id: str,
        created_at: str,
    ) -> EvaluationResult:
        status = _status(execution.status)
        if status not in {ArtifactStatus.SUCCESS, ArtifactStatus.PARTIAL}:
            return EvaluationResult(
                status=status,
                errors=execution.errors,
                hold_reason=execution.hold_reason,
                receipt=execution.receipt,
            )
        if not isinstance(execution.output, Mapping):
            return EvaluationResult(
                status=ArtifactStatus.FAILED,
                errors=("evaluation operator returned a non-object",),
                receipt=execution.receipt,
            )
        raw = execution.output
        required = ("field_fidelity", "task_fitness", "execution_quality")
        if any(not isinstance(raw.get(key), dict) for key in required):
            return EvaluationResult(
                status=ArtifactStatus.FAILED,
                errors=(
                    "evaluation must separate field_fidelity, task_fitness and execution_quality",
                ),
                receipt=execution.receipt,
            )
        try:
            evaluation = CreativeEvaluation(
                evaluation_id=str(raw.get("evaluation_id") or f"{derivation_id}:evaluation"),
                output_id=output_id,
                request_id=request_id,
                field_version_id=field_version_id,
                projection_id=projection_id,
                field_fidelity=raw["field_fidelity"],
                exclusion_findings=_strings(raw.get("exclusion_findings")),
                task_fitness=raw["task_fitness"],
                execution_quality=raw["execution_quality"],
                target_limitations=_strings(raw.get("target_limitations")),
                disagreements=_strings(raw.get("disagreements")),
                feedback_proposal_ids=tuple(
                    f"{derivation_id}:feedback:{position}"
                    for position, item in enumerate(raw.get("feedback", []), start=1)
                    if isinstance(item, Mapping) and isinstance(item.get("instruction"), str)
                ),
                receipt=dict(execution.receipt),
                derivation_id=derivation_id,
                status=status,
            )
        except (TypeError, ValueError, KeyError) as error:
            return EvaluationResult(
                status=ArtifactStatus.FAILED,
                errors=(f"evaluation output is invalid: {error}",),
                receipt=execution.receipt,
            )
        feedback: list[FeedbackRecord] = []
        raw_feedback = raw.get("feedback", [])
        if isinstance(raw_feedback, list):
            for position, item in enumerate(raw_feedback, start=1):
                if not isinstance(item, Mapping) or not isinstance(item.get("instruction"), str):
                    continue
                feedback.append(
                    FeedbackRecord(
                        feedback_id=f"{derivation_id}:feedback:{position}",
                        target_id=str(item.get("target_id") or projection_id),
                        category=str(item.get("category") or "evaluation"),
                        instruction=item["instruction"],
                        actor_id=actor_id,
                        created_at=created_at,
                        proposed_change=item.get("proposed_change")
                        if isinstance(item.get("proposed_change"), dict)
                        else {},
                        derivation_id=derivation_id,
                    )
                )
        return EvaluationResult(
            status=status,
            evaluation=evaluation,
            feedback=tuple(feedback),
            receipt=execution.receipt,
        )


def _strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item.strip())


__all__ = ["CreativeEvaluationWorkflow", "EvaluationResult", "OUTPUT_EVALUATION_OPERATOR_ID"]
