"""Translate portable workflow graphs into executable LangGraph state graphs."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime
from typing import Annotated, Any, TypedDict

from testflight_workflows import (
    ErrorPolicy,
    ResultStatus,
    StepReceipt,
    StepResult,
    WorkflowDefinition,
    WorkflowEngine,
    WorkflowGrant,
    WorkflowPrincipal,
    WorkflowRunResult,
    WorkflowStep,
    resolve_value,
    validate_workflow,
)

StepRunner = Callable[[WorkflowStep, Mapping[str, Any]], Awaitable[Mapping[str, Any]]]


def _merge_outcomes(
    current: dict[str, dict[str, Any]], update: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    return {**current, **update}


def _merge_halt(current: str | None, update: str | None) -> str | None:
    return current or update


class WorkflowGraphState(TypedDict, total=False):
    inputs: dict[str, Any]
    step_outcomes: Annotated[dict[str, dict[str, Any]], _merge_outcomes]
    halt_status: Annotated[str | None, _merge_halt]


class LangGraphWorkflowCompiler:
    """Compile fixed topology while delegating portable step meaning to Testflight."""

    def compile(
        self,
        workflow: WorkflowDefinition,
        step_runner: StepRunner,
        *,
        checkpointer: Any = None,
    ):
        try:
            from langgraph.graph import END, START, StateGraph
        except ImportError as error:
            raise RuntimeError(
                "LangGraph is not installed; enable the adapter's 'langgraph' extra."
            ) from error

        validate_workflow(workflow)
        graph = StateGraph(WorkflowGraphState)
        dependents: dict[str, set[str]] = {step.id: set() for step in workflow.steps}

        for step in workflow.steps:

            async def node(state: WorkflowGraphState, selected: WorkflowStep = step):
                update = dict(await step_runner(selected, state))
                halt_status = update.pop("__halt_status", None)
                return {
                    "step_outcomes": {selected.id: update},
                    "halt_status": halt_status,
                }

            graph.add_node(step.id, node)
            for dependency in step.needs:
                dependents[dependency].add(step.id)

        for step in workflow.steps:
            if not step.needs:
                graph.add_edge(START, step.id)
            elif len(step.needs) == 1:
                graph.add_edge(step.needs[0], step.id)
            else:
                graph.add_edge(list(step.needs), step.id)
            if not dependents[step.id]:
                graph.add_edge(step.id, END)
        return graph.compile(checkpointer=checkpointer)


class LangGraphWorkflowEngine(WorkflowEngine):
    """Execute Testflight workflow semantics with LangGraph scheduling and checkpoints."""

    def __init__(
        self,
        *args: Any,
        compiler: LangGraphWorkflowCompiler | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        try:
            from langgraph.checkpoint.memory import InMemorySaver
        except ImportError as error:
            raise RuntimeError(
                "LangGraph is not installed; enable the adapter's 'langgraph' extra."
            ) from error
        self.compiler = compiler or LangGraphWorkflowCompiler()
        self.checkpointer = InMemorySaver()

    async def execute(
        self,
        *,
        principal: WorkflowPrincipal,
        workflow_id: str,
        workflow_version: int,
        run_id: str,
        inputs: Mapping[str, Any],
    ) -> WorkflowRunResult:
        workflow = self.catalog.get(principal, workflow_id, workflow_version)
        if workflow is None:
            raise RuntimeError("workflow is unavailable or access is denied")
        errors = self.validator.validate(inputs, workflow.inputs_schema)
        if errors:
            raise RuntimeError("; ".join(errors))
        validate_workflow(workflow)
        grant = WorkflowGrant(
            grant_id=f"grant:{run_id}",
            principal_id=principal.id,
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            granted_at=datetime.now(UTC),
        )

        async def run_step(step: WorkflowStep, state: Mapping[str, Any]) -> Mapping[str, Any]:
            if state.get("halt_status"):
                return {"suppressed": True}
            prior = {
                step_id: StepResult.model_validate(outcome["result"])
                for step_id, outcome in state.get("step_outcomes", {}).items()
                if not outcome.get("suppressed")
            }
            result, receipt = await self._execute_step(
                workflow, principal, run_id, inputs, prior, step
            )
            halt_status = None
            if result.status is ResultStatus.FAILED and step.on_error is ErrorPolicy.FAIL:
                halt_status = ResultStatus.FAILED.value
            elif result.status in {ResultStatus.FAILED, ResultStatus.HOLD} and (
                step.on_error is ErrorPolicy.HOLD
            ):
                halt_status = ResultStatus.HOLD.value
            return {
                "result": result.model_dump(mode="json"),
                "receipt": receipt.model_dump(mode="json"),
                "__halt_status": halt_status,
            }

        graph = self.compiler.compile(workflow, run_step, checkpointer=self.checkpointer)
        run_errors: list[str] = []
        try:
            async with asyncio.timeout(workflow.run_timeout_seconds):
                state = await graph.ainvoke(
                    {"inputs": dict(inputs), "step_outcomes": {}, "halt_status": None},
                    config={"configurable": {"thread_id": run_id}},
                )
        except TimeoutError:
            return WorkflowRunResult(
                run_id=run_id,
                workflow_id=workflow.id,
                workflow_version=workflow.version,
                principal_id=principal.id,
                grant_id=grant.grant_id,
                status=ResultStatus.HOLD,
                errors=("workflow run timed out",),
            )

        outcomes = state.get("step_outcomes", {})
        results: dict[str, StepResult] = {}
        receipts: list[StepReceipt] = []
        for step in workflow.steps:
            outcome = outcomes.get(step.id, {})
            if outcome.get("suppressed") or "result" not in outcome:
                continue
            result = StepResult.model_validate(outcome["result"])
            results[step.id] = result
            receipts.append(StepReceipt.model_validate(outcome["receipt"]))
            if result.error:
                run_errors.append(f"{step.id}: {result.error}")

        if state.get("halt_status"):
            status = ResultStatus(state["halt_status"])
            return WorkflowRunResult(
                run_id=run_id,
                workflow_id=workflow.id,
                workflow_version=workflow.version,
                principal_id=principal.id,
                grant_id=grant.grant_id,
                status=status,
                step_results=results,
                receipts=tuple(receipts),
                errors=tuple(run_errors),
            )

        outputs = resolve_value(
            workflow.outputs,
            inputs=inputs,
            results=results,
            run_id=run_id,
            item=None,
            index=None,
        )
        output_errors = self.validator.validate(outputs, workflow.outputs_schema)
        if output_errors:
            run_errors.extend(output_errors)
            status = ResultStatus.FAILED
        elif any(result.status is ResultStatus.PARTIAL for result in results.values()):
            status = ResultStatus.PARTIAL
        else:
            status = ResultStatus.SUCCESS
        return WorkflowRunResult(
            run_id=run_id,
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            principal_id=principal.id,
            grant_id=grant.grant_id,
            status=status,
            outputs=outputs,
            step_results=results,
            receipts=tuple(receipts),
            errors=tuple(run_errors),
        )


__all__ = [
    "LangGraphWorkflowCompiler",
    "LangGraphWorkflowEngine",
    "StepRunner",
    "WorkflowGraphState",
]
