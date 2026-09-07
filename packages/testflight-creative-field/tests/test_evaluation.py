from testflight_creative_field import (
    ArtifactStatus,
    CreativeEvaluationWorkflow,
    OperatorExecution,
)


def test_evaluation_keeps_quality_dimensions_separate_and_returns_feedback_proposals() -> None:
    result = CreativeEvaluationWorkflow().run(
        execution=OperatorExecution(
            status="proposal",
            output={
                "field_fidelity": {"visual": "strong"},
                "exclusion_findings": [],
                "task_fitness": {"audience": "fit"},
                "execution_quality": {"resolution": "good"},
                "target_limitations": ["no temporal control"],
                "disagreements": ["reviewer:two differs"],
                "feedback": [
                    {
                        "category": "projection",
                        "instruction": "Make the tension explicit in the image crop.",
                        "target_id": "projection:one",
                    }
                ],
            },
            receipt={"operator": "evaluation"},
        ),
        output_id="output:one",
        request_id="request:one",
        field_version_id="field:one@1",
        projection_id="projection:one",
        derivation_id="derivation:evaluation",
        actor_id="actor:reviewer",
        created_at="2026-09-03T00:00:00Z",
    )
    assert result.status is ArtifactStatus.SUCCESS
    assert result.evaluation is not None
    assert set(result.evaluation.field_fidelity) == {"visual"}
    assert result.evaluation.task_fitness != result.evaluation.execution_quality
    assert result.evaluation.disagreements == ("reviewer:two differs",)
    assert result.feedback[0].target_id == "projection:one"


def test_invalid_or_failed_evaluation_never_falls_back_to_a_score() -> None:
    invalid = CreativeEvaluationWorkflow().run(
        execution=OperatorExecution(
            status="proposal",
            output={"field_fidelity": {"visual": "strong"}},
        ),
        output_id="output:one",
        request_id="request:one",
        field_version_id="field:one@1",
        projection_id="projection:one",
        derivation_id="derivation:invalid",
        actor_id="actor:reviewer",
        created_at="2026-09-03T00:00:00Z",
    )
    failed = CreativeEvaluationWorkflow().run(
        execution=OperatorExecution(status="failed", errors=("provider unavailable",)),
        output_id="output:one",
        request_id="request:one",
        field_version_id="field:one@1",
        projection_id="projection:one",
        derivation_id="derivation:failed",
        actor_id="actor:reviewer",
        created_at="2026-09-03T00:00:00Z",
    )
    assert invalid.status is ArtifactStatus.FAILED
    assert invalid.evaluation is None
    assert failed.status is ArtifactStatus.FAILED
