"""Cross-record workflow validation and deterministic compilation."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

from .models import StepKind, WorkflowDefinition, WorkflowStep


class WorkflowValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ExecutionStage:
    index: int
    step_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    workflow_id: str
    workflow_version: int
    stages: tuple[ExecutionStage, ...]


def _is_subset(values: tuple[str, ...], allowed: tuple[str, ...], label: str) -> None:
    unknown = sorted(set(values) - set(allowed))
    if unknown:
        raise WorkflowValidationError(f"{label} exceeds workflow envelope: {unknown}")


def _refs(value: Any) -> list[str]:
    if isinstance(value, str) and value.startswith("$"):
        return [value]
    if isinstance(value, dict):
        return [ref for item in value.values() for ref in _refs(item)]
    if isinstance(value, (list, tuple)):
        return [ref for item in value for ref in _refs(item)]
    return []


def _step_ref(ref: str) -> str | None:
    parts = ref.removeprefix("$").split(".")
    return parts[1] if len(parts) > 1 and parts[0] == "steps" else None


def validate_workflow(workflow: WorkflowDefinition) -> ExecutionPlan:
    steps = {step.id: step for step in workflow.steps}
    if len(steps) != len(workflow.steps):
        raise WorkflowValidationError("workflow step ids must be unique")

    for step in workflow.steps:
        missing = sorted(set(step.needs) - steps.keys())
        if missing:
            raise WorkflowValidationError(f"step {step.id!r} has missing dependencies: {missing}")
        if step.id in step.needs:
            raise WorkflowValidationError(f"step {step.id!r} cannot depend on itself")
        _is_subset(step.access.workspace_ids, workflow.knowledge.workspace_ids, "workspace access")
        _is_subset(step.access.container_ids, workflow.knowledge.container_ids, "container access")
        _is_subset(step.access.entity_ids, workflow.knowledge.entity_ids, "entity access")
        _is_subset(step.access.entity_types, workflow.knowledge.entity_types, "entity-type access")
        _is_subset(step.capabilities, workflow.authority.capabilities, "step capabilities")
        _is_subset(step.action_ids, workflow.authority.action_ids, "step actions")
        if step.kind is StepKind.ACTION:
            if not workflow.authority.external_action:
                raise WorkflowValidationError(
                    "action step requires workflow external_action authority"
                )
            if not step.action_ids:
                raise WorkflowValidationError(f"action step {step.id!r} must declare action_ids")

        values = [step.arguments, [condition.ref for condition in step.when]]
        if step.foreach:
            values.append(step.foreach)
        if step.idempotency_key:
            values.append(step.idempotency_key)
        for ref in _refs(values):
            referenced = _step_ref(ref)
            if referenced and referenced not in steps:
                raise WorkflowValidationError(
                    f"step {step.id!r} references unknown step {referenced!r}"
                )
            if referenced and referenced not in step.needs:
                raise WorkflowValidationError(
                    f"step {step.id!r} must list referenced step {referenced!r} in needs"
                )

    for ref in _refs(workflow.outputs):
        referenced = _step_ref(ref)
        if referenced and referenced not in steps:
            raise WorkflowValidationError(f"workflow output references unknown step {referenced!r}")

    indegree = {step_id: 0 for step_id in steps}
    children: dict[str, list[str]] = defaultdict(list)
    for step in workflow.steps:
        for dependency in step.needs:
            indegree[step.id] += 1
            children[dependency].append(step.id)
    ready = deque(sorted(step_id for step_id, degree in indegree.items() if degree == 0))
    stages: list[ExecutionStage] = []
    visited = 0
    while ready:
        current = tuple(ready)
        ready.clear()
        stages.append(ExecutionStage(index=len(stages), step_ids=current))
        visited += len(current)
        next_ready: list[str] = []
        for step_id in current:
            for child in children[step_id]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    next_ready.append(child)
        ready.extend(sorted(next_ready))
    if visited != len(steps):
        raise WorkflowValidationError("workflow graph contains a cycle")
    return ExecutionPlan(workflow.id, workflow.version, tuple(stages))


def step_by_id(workflow: WorkflowDefinition, step_id: str) -> WorkflowStep:
    return next(step for step in workflow.steps if step.id == step_id)


__all__ = [
    "ExecutionPlan",
    "ExecutionStage",
    "WorkflowValidationError",
    "step_by_id",
    "validate_workflow",
]
