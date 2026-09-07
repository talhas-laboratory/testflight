from __future__ import annotations

import asyncio
from pathlib import Path

from testflight_adapter_langgraph import LangGraphWorkflowEngine
from testflight_adapter_sqlite_workflow_runtime import SqliteWorkflowRuntimeStore
from testflight_workflow_runtime import (
    EnvironmentTokenAuthenticator,
    WorkflowRuntimeService,
)
from testflight_workflows import (
    HandlerRegistry,
    ResultStatus,
    StepResult,
    WorkflowCatalog,
    WorkflowPrincipal,
    load_workflow,
)

ROOT = Path(__file__).parents[3]


class Handler:
    def __init__(self, function):
        self.function = function
        self.calls = 0

    async def execute(self, context):
        self.calls += 1
        return self.function(context)


def runtime(tmp_path):
    workflow = load_workflow(ROOT / "workflows/examples/evidence-synthesis.yaml")
    catalog = WorkflowCatalog([workflow])
    registry = HandlerRegistry()
    registry.register(
        "knowledge.retrieve",
        Handler(lambda _context: StepResult(status=ResultStatus.SUCCESS, output={"items": []})),
    )
    registry.register(
        "reasoning.evaluate_evidence",
        Handler(lambda _context: StepResult(status=ResultStatus.SUCCESS, output={})),
    )
    registry.register(
        "reasoning.synthesize_proposal",
        Handler(
            lambda context: StepResult(
                status=ResultStatus.SUCCESS, output={"claim": context.arguments["question"]}
            )
        ),
    )
    registry.register(
        "action.dispatch_proposal",
        Handler(lambda _context: StepResult(status=ResultStatus.SUCCESS, output={"ok": True})),
    )
    store = SqliteWorkflowRuntimeStore(tmp_path / "runs.sqlite3")
    engine = LangGraphWorkflowEngine(catalog=catalog, handlers=registry, idempotency=store)
    return WorkflowRuntimeService(catalog=catalog, engine=engine, run_store=store), workflow


def test_service_runs_and_hides_foreign_records(tmp_path):
    service, workflow = runtime(tmp_path)
    allowed = WorkflowPrincipal(
        id="agent:testflight-research", roles=("testflight-research-agent",)
    )
    foreign = WorkflowPrincipal(id="agent:two", roles=("testflight-research-agent",))

    async def exercise():
        record = await service.run_and_wait(
            principal=allowed,
            workflow_id=workflow.id,
            workflow_version=1,
            run_id="run:one",
            inputs={"question": "Question", "request_id": "request:one"},
        )
        assert record.result is not None
        assert record.result.status is ResultStatus.SUCCESS
        assert await service.get_run(foreign, "run:one") is None

    asyncio.run(exercise())


def test_workflow_is_assigned_only_to_the_declared_agent(tmp_path):
    service, workflow = runtime(tmp_path)
    assigned = WorkflowPrincipal(id="agent:testflight-research")
    same_role_but_unassigned = WorkflowPrincipal(
        id="agent:other", roles=("testflight-research-agent",)
    )

    assert service.discover(assigned)[0]["id"] == workflow.id
    assert service.discover(same_role_but_unassigned) == ()


def test_environment_authenticator_requires_bearer_token():
    principal = WorkflowPrincipal(id="agent:one", roles=("role:one",))
    authenticator = EnvironmentTokenAuthenticator((("secret", principal),))
    assert authenticator.authenticate("Bearer secret") == principal
    assert authenticator.authenticate("secret") is None
    assert authenticator.authenticate("Bearer wrong") is None
