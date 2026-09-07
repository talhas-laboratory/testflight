"""Executable reference semantics for declarative workflows."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from .catalog import WorkflowCatalog
from .models import (
    Condition,
    ConditionOperator,
    ErrorPolicy,
    ResultStatus,
    StepReceipt,
    StepResult,
    WorkflowAuthority,
    WorkflowDefinition,
    WorkflowGrant,
    WorkflowPrincipal,
    WorkflowRunRecord,
    WorkflowRunResult,
    WorkflowStep,
)
from .validation import step_by_id, validate_workflow


class WorkflowRuntimeError(RuntimeError):
    pass


class InputValidator(Protocol):
    def validate(self, value: Mapping[str, Any], schema: Mapping[str, Any]) -> tuple[str, ...]: ...


class BasicJsonSchemaValidator:
    """Dependency-free validation for the object subset used at the API boundary.

    A composition root may replace this with a complete JSON Schema implementation.
    """

    _types = {
        "string": str,
        "object": dict,
        "array": list,
        "boolean": bool,
        "integer": int,
        "number": (int, float),
    }

    def validate(self, value: Mapping[str, Any], schema: Mapping[str, Any]) -> tuple[str, ...]:
        errors: list[str] = []
        for name in schema.get("required", []):
            if name not in value:
                errors.append(f"missing required input: {name}")
        for name, definition in schema.get("properties", {}).items():
            if name not in value or not isinstance(definition, Mapping):
                continue
            expected_name = definition.get("type")
            expected = self._types.get(expected_name)
            if expected and not isinstance(value[name], expected):
                errors.append(f"value {name!r} must be {expected_name}")
            if "const" in definition and value[name] != definition["const"]:
                errors.append(f"value {name!r} must equal {definition['const']!r}")
        if schema.get("additionalProperties") is False:
            unknown = set(value) - set(schema.get("properties", {}))
            errors.extend(f"unknown input: {name}" for name in sorted(unknown))
        return tuple(errors)


@dataclass(frozen=True, slots=True)
class StepExecutionContext:
    run_id: str
    workflow_id: str
    workflow_version: int
    principal_id: str
    step: WorkflowStep
    inputs: Mapping[str, Any]
    arguments: Mapping[str, Any]
    prior_results: Mapping[str, StepResult]
    authority: WorkflowAuthority
    knowledge: Any
    loop_item: Any = None
    loop_index: int | None = None


class StepHandler(Protocol):
    async def execute(self, context: StepExecutionContext) -> StepResult: ...


class HandlerRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, StepHandler] = {}

    def register(self, handler_id: str, handler: StepHandler) -> None:
        if not handler_id.strip() or handler_id in self._handlers:
            raise ValueError(f"invalid or duplicate handler: {handler_id!r}")
        self._handlers[handler_id] = handler

    def require(self, handler_id: str) -> StepHandler:
        try:
            return self._handlers[handler_id]
        except KeyError as error:
            raise WorkflowRuntimeError(f"handler is not registered: {handler_id}") from error


class IdempotencyStore(Protocol):
    async def get(self, key: str) -> StepResult | None: ...

    async def put(self, key: str, result: StepResult) -> None: ...


class WorkflowRunStore(Protocol):
    async def get_run(self, run_id: str) -> WorkflowRunRecord | None: ...

    async def put_run(self, record: WorkflowRunRecord) -> None: ...


class MemoryIdempotencyStore:
    def __init__(self) -> None:
        self._results: dict[str, StepResult] = {}

    async def get(self, key: str) -> StepResult | None:
        return self._results.get(key)

    async def put(self, key: str, result: StepResult) -> None:
        self._results[key] = result


def _path(value: Any, parts: Sequence[str]) -> Any:
    current = value
    for part in parts:
        if isinstance(current, Mapping):
            if part not in current:
                raise WorkflowRuntimeError(f"reference path does not exist: {'.'.join(parts)}")
            current = current[part]
        elif isinstance(current, Sequence) and not isinstance(current, (str, bytes)):
            try:
                current = current[int(part)]
            except (ValueError, IndexError) as error:
                raise WorkflowRuntimeError(
                    f"reference sequence index is invalid: {'.'.join(parts)}"
                ) from error
        else:
            raise WorkflowRuntimeError(f"reference cannot be traversed: {'.'.join(parts)}")
    return current


def resolve_reference(
    ref: str,
    *,
    inputs: Mapping[str, Any],
    results: Mapping[str, StepResult],
    run_id: str,
    item: Any = None,
    index: int | None = None,
) -> Any:
    if not ref.startswith("$"):
        return ref
    parts = ref[1:].split(".")
    root = parts.pop(0)
    if root == "inputs":
        return _path(inputs, parts)
    if root == "steps":
        step_id = parts.pop(0)
        result = results.get(step_id)
        if result is None:
            raise WorkflowRuntimeError(f"step result is unavailable: {step_id}")
        base = {"output": result.output, "status": result.status.value, "receipt": result.receipt}
        return _path(base, parts)
    if root == "run":
        return _path({"id": run_id}, parts)
    if root == "item":
        return _path(item, parts) if parts else item
    if root == "index":
        return index
    raise WorkflowRuntimeError(f"unsupported reference root: {root}")


def resolve_value(value: Any, **context: Any) -> Any:
    if isinstance(value, str) and value.startswith("$"):
        return resolve_reference(value, **context)
    if isinstance(value, dict):
        return {key: resolve_value(item, **context) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_value(item, **context) for item in value]
    return value


def evaluate_condition(condition: Condition, value: Any) -> bool:
    operator = condition.operator
    if operator is ConditionOperator.EXISTS:
        return value is not None
    if operator is ConditionOperator.NOT_EXISTS:
        return value is None
    if operator is ConditionOperator.TRUTHY:
        return bool(value)
    if operator is ConditionOperator.FALSY:
        return not value
    if operator is ConditionOperator.EQUALS:
        return value == condition.value
    if operator is ConditionOperator.NOT_EQUALS:
        return value != condition.value
    if operator is ConditionOperator.IN:
        return value in condition.value
    if operator is ConditionOperator.CONTAINS:
        return condition.value in value
    if operator is ConditionOperator.GREATER_THAN:
        return value > condition.value
    if operator is ConditionOperator.LESS_THAN:
        return value < condition.value
    raise WorkflowRuntimeError(f"unsupported condition operator: {operator}")


class WorkflowEngine:
    """Run a validated workflow through registered capability-bound handlers."""

    def __init__(
        self,
        *,
        catalog: WorkflowCatalog,
        handlers: HandlerRegistry,
        validator: InputValidator | None = None,
        idempotency: IdempotencyStore | None = None,
    ) -> None:
        self.catalog = catalog
        self.handlers = handlers
        self.validator = validator or BasicJsonSchemaValidator()
        self.idempotency = idempotency or MemoryIdempotencyStore()

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
            raise WorkflowRuntimeError("workflow is unavailable or access is denied")
        errors = self.validator.validate(inputs, workflow.inputs_schema)
        if errors:
            raise WorkflowRuntimeError("; ".join(errors))
        plan = validate_workflow(workflow)
        now = datetime.now(UTC)
        grant = WorkflowGrant(
            grant_id=f"grant:{run_id}",
            principal_id=principal.id,
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            granted_at=now,
        )
        results: dict[str, StepResult] = {}
        receipts: list[StepReceipt] = []
        run_errors: list[str] = []
        semaphore = asyncio.Semaphore(workflow.max_concurrency)

        async def run_one(step: WorkflowStep) -> tuple[StepResult, StepReceipt]:
            async with semaphore:
                return await self._execute_step(workflow, principal, run_id, inputs, results, step)

        try:
            async with asyncio.timeout(workflow.run_timeout_seconds):
                for stage in plan.stages:
                    stage_outcomes = await asyncio.gather(
                        *(run_one(step_by_id(workflow, step_id)) for step_id in stage.step_ids)
                    )
                    stop_status: ResultStatus | None = None
                    for step_id, (result, receipt) in zip(
                        stage.step_ids, stage_outcomes, strict=True
                    ):
                        results[step_id] = result
                        receipts.append(receipt)
                        step = step_by_id(workflow, step_id)
                        if (
                            result.status is ResultStatus.FAILED
                            and step.on_error is ErrorPolicy.FAIL
                        ):
                            stop_status = ResultStatus.FAILED
                        elif result.status in {ResultStatus.FAILED, ResultStatus.HOLD} and (
                            step.on_error is ErrorPolicy.HOLD
                        ):
                            stop_status = ResultStatus.HOLD
                        if result.error:
                            run_errors.append(f"{step_id}: {result.error}")
                    if stop_status:
                        return WorkflowRunResult(
                            run_id=run_id,
                            workflow_id=workflow.id,
                            workflow_version=workflow.version,
                            principal_id=principal.id,
                            grant_id=grant.grant_id,
                            status=stop_status,
                            step_results=results,
                            receipts=tuple(receipts),
                            errors=tuple(run_errors),
                        )
        except TimeoutError:
            run_errors.append("workflow run timed out")
            return WorkflowRunResult(
                run_id=run_id,
                workflow_id=workflow.id,
                workflow_version=workflow.version,
                principal_id=principal.id,
                grant_id=grant.grant_id,
                status=ResultStatus.HOLD,
                step_results=results,
                receipts=tuple(receipts),
                errors=tuple(run_errors),
            )

        outputs = resolve_value(
            workflow.outputs, inputs=inputs, results=results, run_id=run_id, item=None, index=None
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

    async def _execute_step(
        self,
        workflow: WorkflowDefinition,
        principal: WorkflowPrincipal,
        run_id: str,
        inputs: Mapping[str, Any],
        results: Mapping[str, StepResult],
        step: WorkflowStep,
    ) -> tuple[StepResult, StepReceipt]:
        started = datetime.now(UTC)
        ref_context = dict(inputs=inputs, results=results, run_id=run_id, item=None, index=None)
        try:
            if not all(
                evaluate_condition(
                    condition,
                    resolve_reference(condition.ref, **ref_context),
                )
                for condition in step.when
            ):
                result = StepResult(status=ResultStatus.SKIPPED)
                return result, StepReceipt(
                    step_id=step.id,
                    handler=step.handler,
                    status=result.status,
                    attempts=0,
                    started_at=started,
                    finished_at=datetime.now(UTC),
                )
            arguments = (
                step.arguments
                if step.kind.value == "loop"
                else resolve_value(step.arguments, **ref_context)
            )
            idem_key = (
                str(resolve_reference(step.idempotency_key, **ref_context))
                if step.idempotency_key
                else None
            )
            scoped_key = (
                f"{workflow.id}@{workflow.version}:{step.id}:{idem_key}" if idem_key else None
            )
            if scoped_key:
                replay = await self.idempotency.get(scoped_key)
                if replay is not None:
                    return replay, StepReceipt(
                        step_id=step.id,
                        handler=step.handler,
                        status=replay.status,
                        attempts=0,
                        started_at=started,
                        finished_at=datetime.now(UTC),
                        idempotent_replay=True,
                        handler_receipt=replay.receipt,
                    )
            if step.kind.value == "loop":
                items = resolve_reference(step.foreach or "", **ref_context)
                if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
                    raise WorkflowRuntimeError(
                        f"loop step {step.id!r} foreach must resolve to an array"
                    )
                if len(items) > (step.max_iterations or 0):
                    raise WorkflowRuntimeError(f"loop step {step.id!r} exceeded max_iterations")
                result, attempts = await self._execute_loop(
                    workflow, principal, run_id, inputs, results, step, arguments, list(items)
                )
            else:
                result, attempts = await self._call_handler(
                    workflow, principal, run_id, inputs, results, step, arguments
                )
            if scoped_key and result.status in {ResultStatus.SUCCESS, ResultStatus.PARTIAL}:
                await self.idempotency.put(scoped_key, result)
            return result, StepReceipt(
                step_id=step.id,
                handler=step.handler,
                status=result.status,
                attempts=attempts,
                started_at=started,
                finished_at=datetime.now(UTC),
                error=result.error,
                handler_receipt=result.receipt,
            )
        except Exception as error:  # noqa: BLE001 - normalize handler/runtime boundaries.
            result = StepResult(
                status=ResultStatus.HOLD
                if step.on_error is ErrorPolicy.HOLD
                else ResultStatus.FAILED,
                error=str(error),
                error_code="runtime_error",
            )
            return result, StepReceipt(
                step_id=step.id,
                handler=step.handler,
                status=result.status,
                attempts=0,
                started_at=started,
                finished_at=datetime.now(UTC),
                error=result.error,
            )

    async def _call_handler(
        self,
        workflow: WorkflowDefinition,
        principal: WorkflowPrincipal,
        run_id: str,
        inputs: Mapping[str, Any],
        results: Mapping[str, StepResult],
        step: WorkflowStep,
        arguments: Mapping[str, Any],
        *,
        item: Any = None,
        index: int | None = None,
    ) -> tuple[StepResult, int]:
        handler = self.handlers.require(step.handler)
        attempts = 0
        result = StepResult(status=ResultStatus.FAILED, error="handler was not attempted")
        for attempts in range(1, step.retry.max_attempts + 1):
            context = StepExecutionContext(
                run_id=run_id,
                workflow_id=workflow.id,
                workflow_version=workflow.version,
                principal_id=principal.id,
                step=step,
                inputs=inputs,
                arguments=arguments,
                prior_results=results,
                authority=workflow.authority,
                knowledge=workflow.knowledge,
                loop_item=item,
                loop_index=index,
            )
            try:
                async with asyncio.timeout(step.timeout_seconds):
                    result = await handler.execute(context)
            except TimeoutError:
                result = StepResult(
                    status=ResultStatus.FAILED,
                    error="step timed out",
                    error_code="timeout",
                )
            except Exception as error:  # noqa: BLE001 - handler errors become typed outcomes.
                result = StepResult(
                    status=ResultStatus.FAILED,
                    error=str(error),
                    error_code="handler_error",
                )
            if (
                result.status is not ResultStatus.FAILED
                or result.error_code not in step.retry.retry_on
                or attempts >= step.retry.max_attempts
            ):
                break
            if step.retry.backoff_seconds:
                await asyncio.sleep(step.retry.backoff_seconds)
        return result, attempts

    async def _execute_loop(
        self,
        workflow: WorkflowDefinition,
        principal: WorkflowPrincipal,
        run_id: str,
        inputs: Mapping[str, Any],
        results: Mapping[str, StepResult],
        step: WorkflowStep,
        arguments: Mapping[str, Any],
        items: list[Any],
    ) -> tuple[StepResult, int]:
        semaphore = asyncio.Semaphore(step.loop_concurrency)

        async def invoke(index: int, item: Any) -> tuple[StepResult, int]:
            async with semaphore:
                item_context = dict(
                    inputs=inputs, results=results, run_id=run_id, item=item, index=index
                )
                resolved_arguments = resolve_value(arguments, **item_context)
                return await self._call_handler(
                    workflow,
                    principal,
                    run_id,
                    inputs,
                    results,
                    step,
                    resolved_arguments,
                    item=item,
                    index=index,
                )

        outcomes = await asyncio.gather(*(invoke(index, item) for index, item in enumerate(items)))
        item_results = [outcome[0] for outcome in outcomes]
        attempts = sum(outcome[1] for outcome in outcomes)
        failures = [result for result in item_results if result.status is ResultStatus.FAILED]
        holds = [result for result in item_results if result.status is ResultStatus.HOLD]
        if failures:
            status = ResultStatus.FAILED
        elif holds:
            status = ResultStatus.HOLD
        elif any(result.status is ResultStatus.PARTIAL for result in item_results):
            status = ResultStatus.PARTIAL
        else:
            status = ResultStatus.SUCCESS
        return StepResult(
            status=status,
            output=[result.output for result in item_results],
            error="one or more loop items failed" if failures else None,
            receipt={"item_count": len(items)},
        ), attempts


__all__ = [
    "BasicJsonSchemaValidator",
    "HandlerRegistry",
    "IdempotencyStore",
    "InputValidator",
    "MemoryIdempotencyStore",
    "StepExecutionContext",
    "StepHandler",
    "WorkflowEngine",
    "WorkflowRuntimeError",
    "WorkflowRunStore",
    "evaluate_condition",
    "resolve_reference",
    "resolve_value",
]
