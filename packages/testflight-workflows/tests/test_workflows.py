from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from testflight_workflows import (
    HandlerRegistry,
    ResultStatus,
    StepResult,
    WorkflowCatalog,
    WorkflowDefinition,
    WorkflowEngine,
    WorkflowPrincipal,
    WorkflowRuntimeError,
    WorkflowValidationError,
    load_workflow,
    render_prompt,
    validate_workflow,
    workflow_json_schema,
)

ROOT = Path(__file__).parents[3]
EXAMPLE = ROOT / "workflows/examples/evidence-synthesis.yaml"


class RecordingHandler:
    def __init__(self, function):
        self.function = function
        self.calls = []

    async def execute(self, context):
        self.calls.append(context)
        return self.function(context)


def handlers():
    registry = HandlerRegistry()
    retrieve = RecordingHandler(
        lambda context: StepResult(
            status=ResultStatus.SUCCESS,
            output={"items": [{"id": "evidence:1"}, {"id": "evidence:2"}]},
        )
    )
    evaluate = RecordingHandler(
        lambda context: StepResult(
            status=ResultStatus.SUCCESS,
            output={"id": context.arguments["record"]["id"], "accepted": True},
        )
    )
    synthesize = RecordingHandler(
        lambda context: StepResult(
            status=ResultStatus.SUCCESS,
            output={
                "claim": context.arguments["question"],
                "evidence": context.arguments["evidence"],
            },
        )
    )
    dispatch = RecordingHandler(
        lambda context: StepResult(
            status=ResultStatus.SUCCESS,
            output={"dispatched": True, "claim": context.arguments["proposal"]["claim"]},
        )
    )
    registry.register("knowledge.retrieve", retrieve)
    registry.register("reasoning.evaluate_evidence", evaluate)
    registry.register("reasoning.synthesize_proposal", synthesize)
    registry.register("action.dispatch_proposal", dispatch)
    return registry, (retrieve, evaluate, synthesize, dispatch)


def test_example_loads_and_compiles_parallel_safe_stages():
    workflow = load_workflow(EXAMPLE)
    plan = validate_workflow(workflow)
    assert [stage.step_ids for stage in plan.stages] == [
        ("retrieve",),
        ("evaluate_records",),
        ("synthesize",),
        ("dispatch",),
    ]
    assert all(step.instruction is not None for step in workflow.steps)
    assert workflow_json_schema()["title"] == "WorkflowDefinition"
    evaluate = next(step for step in workflow.steps if step.id == "evaluate_records")
    assert evaluate.instruction is not None
    assert evaluate.instruction.prompt is not None
    rendered = render_prompt(
        evaluate.instruction.prompt,
        inputs={"question": "ignored"},
        arguments={"question": "What changed?", "record": {"id": "evidence:1"}},
    )
    assert 'Research question: "What changed?"' in rendered.user
    assert '"id": "evidence:1"' in rendered.user


def test_prompt_renderer_allows_nested_json_values_after_substitution():
    workflow = load_workflow(EXAMPLE)
    evaluate = next(step for step in workflow.steps if step.id == "evaluate_records")
    assert evaluate.instruction is not None
    assert evaluate.instruction.prompt is not None
    rendered = render_prompt(
        evaluate.instruction.prompt,
        inputs={"question": "ignored"},
        arguments={
            "question": "What changed?",
            "record": {"id": "evidence:1", "metadata": {"nested": True}},
        },
    )
    assert '"nested": true' in rendered.user


def test_compiler_groups_independent_steps_for_parallel_execution():
    payload = load_workflow(EXAMPLE).model_dump(mode="json")
    payload["steps"].append(
        {
            "id": "parallel_probe",
            "kind": "transform",
            "handler": "reasoning.synthesize_proposal",
            "description": "An independent transform.",
            "arguments": {"question": "$inputs.question", "evidence": []},
            "capabilities": ["proposal.write"],
        }
    )
    workflow = WorkflowDefinition.model_validate(payload)
    plan = validate_workflow(workflow)
    assert plan.stages[0].step_ids == ("parallel_probe", "retrieve")


def test_catalog_exposes_only_authorized_workflows():
    workflow = load_workflow(EXAMPLE)
    catalog = WorkflowCatalog([workflow])
    denied = WorkflowPrincipal(id="agent:other", roles=("other",))
    allowed = WorkflowPrincipal(id="agent:testflight-research")
    assert catalog.discover(denied) == ()
    descriptor = catalog.discover(allowed)[0]
    assert descriptor["id"] == workflow.id
    assert descriptor["side_effects"]["external_action"] is True


def test_runtime_executes_loop_and_workflow_level_authority():
    workflow = load_workflow(EXAMPLE)
    registry, recorded = handlers()
    engine = WorkflowEngine(catalog=WorkflowCatalog([workflow]), handlers=registry)
    principal = WorkflowPrincipal(id="agent:testflight-research")
    result = asyncio.run(
        engine.execute(
            principal=principal,
            workflow_id=workflow.id,
            workflow_version=1,
            run_id="run:one",
            inputs={"question": "What changed?", "request_id": "request:one"},
        )
    )
    assert result.status is ResultStatus.SUCCESS
    assert len(recorded[1].calls) == 2
    assert result.outputs["dispatch"]["dispatched"] is True
    assert recorded[3].calls[0].authority.external_action is True
    assert recorded[3].calls[0].knowledge.container_ids == (
        "world://workspace/testflight-product/research-learning",
    )


def test_action_idempotency_replays_across_runs():
    workflow = load_workflow(EXAMPLE)
    registry, recorded = handlers()
    engine = WorkflowEngine(catalog=WorkflowCatalog([workflow]), handlers=registry)
    principal = WorkflowPrincipal(id="agent:testflight-research")

    async def twice():
        for run_id in ("run:first", "run:second"):
            await engine.execute(
                principal=principal,
                workflow_id=workflow.id,
                workflow_version=1,
                run_id=run_id,
                inputs={"question": "What changed?", "request_id": "same-request"},
            )

    asyncio.run(twice())
    assert len(recorded[3].calls) == 1


def test_access_denial_happens_before_execution():
    workflow = load_workflow(EXAMPLE)
    registry, recorded = handlers()
    engine = WorkflowEngine(catalog=WorkflowCatalog([workflow]), handlers=registry)
    with pytest.raises(WorkflowRuntimeError, match="access is denied"):
        asyncio.run(
            engine.execute(
                principal=WorkflowPrincipal(id="agent:other"),
                workflow_id=workflow.id,
                workflow_version=1,
                run_id="run:denied",
                inputs={"question": "No", "request_id": "request:no"},
            )
        )
    assert all(not handler.calls for handler in recorded)


def test_false_condition_skips_handler_without_failing_run():
    payload = load_workflow(EXAMPLE).model_dump(mode="json")
    payload["steps"] = [
        {
            "id": "conditional",
            "kind": "transform",
            "handler": "reasoning.synthesize_proposal",
            "description": "Run only for a matching question.",
            "arguments": {"question": "$inputs.question", "evidence": []},
            "when": [{"ref": "$inputs.question", "operator": "equals", "value": "run me"}],
            "capabilities": ["proposal.write"],
        }
    ]
    payload["outputs_schema"] = {
        "type": "object",
        "additionalProperties": False,
        "properties": {},
    }
    payload["outputs"] = {}
    workflow = WorkflowDefinition.model_validate(payload)
    registry, recorded = handlers()
    engine = WorkflowEngine(catalog=WorkflowCatalog([workflow]), handlers=registry)
    result = asyncio.run(
        engine.execute(
            principal=WorkflowPrincipal(id="agent:testflight-research"),
            workflow_id=workflow.id,
            workflow_version=1,
            run_id="run:conditional",
            inputs={"question": "skip me", "request_id": "request:conditional"},
        )
    )
    assert result.status is ResultStatus.SUCCESS
    assert result.step_results["conditional"].status is ResultStatus.SKIPPED
    assert not recorded[2].calls


def test_validator_rejects_step_authority_escalation():
    payload = load_workflow(EXAMPLE).model_dump(mode="json")
    payload["steps"][0]["capabilities"] = ["knowledge.delete"]
    workflow = WorkflowDefinition.model_validate(payload)
    with pytest.raises(WorkflowValidationError, match="exceeds workflow envelope"):
        validate_workflow(workflow)


def test_validator_rejects_cycles():
    payload = load_workflow(EXAMPLE).model_dump(mode="json")
    payload["steps"][0]["needs"] = ["dispatch"]
    workflow = WorkflowDefinition.model_validate(payload)
    with pytest.raises(WorkflowValidationError, match="cycle"):
        validate_workflow(workflow)
