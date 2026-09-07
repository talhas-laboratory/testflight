import asyncio
from pathlib import Path

import pytest
from testflight_adapter_langgraph import LangGraphAdapter, LangGraphWorkflowCompiler
from testflight_core import Capability, HealthState
from testflight_workflows import load_workflow


def test_descriptor_and_dependency_free_probe() -> None:
    adapter = LangGraphAdapter()

    assert adapter.descriptor.capabilities == {Capability.ORCHESTRATION}
    assert adapter.health().state in {HealthState.AVAILABLE, HealthState.UNAVAILABLE}


def test_workflow_compiler_keeps_optional_dependency_at_boundary() -> None:
    root = Path(__file__).parents[3]
    workflow = load_workflow(root / "workflows/examples/evidence-synthesis.yaml")

    async def runner(_step, _state):
        return {}

    if LangGraphAdapter().health().state is HealthState.UNAVAILABLE:
        with pytest.raises(RuntimeError, match="LangGraph is not installed"):
            LangGraphWorkflowCompiler().compile(workflow, runner)


def test_workflow_compiler_executes_graph_and_preserves_prior_state() -> None:
    if LangGraphAdapter().health().state is HealthState.UNAVAILABLE:
        pytest.skip("LangGraph optional extra is unavailable")
    root = Path(__file__).parents[3]
    workflow = load_workflow(root / "workflows/examples/evidence-synthesis.yaml")

    async def runner(step, state):
        return {"seen": sorted(state.get("step_outcomes", {})), "step": step.id}

    graph = LangGraphWorkflowCompiler().compile(workflow, runner)
    state = asyncio.run(graph.ainvoke({"inputs": {}, "step_outcomes": {}, "halt_status": None}))

    assert set(state["step_outcomes"]) == {
        "retrieve",
        "evaluate_records",
        "synthesize",
        "dispatch",
    }
    assert state["step_outcomes"]["dispatch"]["seen"] == [
        "evaluate_records",
        "retrieve",
        "synthesize",
    ]
