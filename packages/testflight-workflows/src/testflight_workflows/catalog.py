"""Workflow loading, discovery and agent-facing tool descriptors."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

import yaml

from .models import WorkflowDefinition, WorkflowPrincipal
from .validation import validate_workflow


class WorkflowAccessPolicy(Protocol):
    def permits(self, principal: WorkflowPrincipal, workflow: WorkflowDefinition) -> bool: ...


class DeclaredAccessPolicy:
    def permits(self, principal: WorkflowPrincipal, workflow: WorkflowDefinition) -> bool:
        access = workflow.access
        return (
            access.public
            or principal.id in access.agent_ids
            or bool(set(principal.roles) & set(access.roles))
        )


class WorkflowCatalog:
    def __init__(
        self,
        workflows: list[WorkflowDefinition] | tuple[WorkflowDefinition, ...],
        access_policy: WorkflowAccessPolicy | None = None,
    ) -> None:
        self._workflows: dict[tuple[str, int], WorkflowDefinition] = {}
        self.access_policy = access_policy or DeclaredAccessPolicy()
        for workflow in workflows:
            validate_workflow(workflow)
            key = (workflow.id, workflow.version)
            if key in self._workflows:
                raise ValueError(f"duplicate workflow: {workflow.id}@{workflow.version}")
            self._workflows[key] = workflow

    @classmethod
    def from_paths(cls, paths: list[Path] | tuple[Path, ...]) -> WorkflowCatalog:
        return cls([load_workflow(path) for path in paths])

    def get(
        self, principal: WorkflowPrincipal, workflow_id: str, version: int
    ) -> WorkflowDefinition | None:
        workflow = self._workflows.get((workflow_id, version))
        if workflow is None or not self.access_policy.permits(principal, workflow):
            return None
        return workflow

    def discover(self, principal: WorkflowPrincipal) -> tuple[dict[str, Any], ...]:
        visible = [
            workflow
            for workflow in self._workflows.values()
            if self.access_policy.permits(principal, workflow)
        ]
        return tuple(
            {
                "id": workflow.id,
                "version": workflow.version,
                "name": workflow.name,
                "description": workflow.description,
                "tags": list(workflow.tags),
                "input_schema": workflow.inputs_schema,
                "output_schema": workflow.outputs_schema,
                "side_effects": {
                    "proposal_write": workflow.authority.proposal_write,
                    "canonical_write": workflow.authority.canonical_write,
                    "external_action": workflow.authority.external_action,
                },
            }
            for workflow in sorted(visible, key=lambda item: (item.id, item.version))
        )


def load_workflow(path: Path) -> WorkflowDefinition:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    workflow = WorkflowDefinition.model_validate(payload)
    validate_workflow(workflow)
    return workflow


def workflow_json_schema() -> dict[str, Any]:
    return WorkflowDefinition.model_json_schema()


__all__ = [
    "DeclaredAccessPolicy",
    "WorkflowAccessPolicy",
    "WorkflowCatalog",
    "load_workflow",
    "workflow_json_schema",
]
