"""Model-backed workflow step execution through the shared operator runtime."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from testflight_workflows import (
    BasicJsonSchemaValidator,
    ResultStatus,
    StepExecutionContext,
    StepResult,
    render_prompt,
)

from .operator_client import OperatorRuntimeClient


def _references(value: Any) -> set[str]:
    if isinstance(value, str) and value.startswith(("repo://", "world://", "source:")):
        return {value}
    if isinstance(value, Mapping):
        return {ref for item in value.values() for ref in _references(item)}
    if isinstance(value, list | tuple):
        return {ref for item in value for ref in _references(item)}
    return set()


class PromptStepHandler:
    def __init__(self, client: OperatorRuntimeClient) -> None:
        self.client = client
        self.validator = BasicJsonSchemaValidator()

    async def execute(self, context: StepExecutionContext) -> StepResult:
        if "model.invoke" not in context.step.capabilities:
            raise PermissionError("prompt-backed step lacks model.invoke capability")
        if "model.invoke" not in context.authority.capabilities:
            raise PermissionError("workflow grant lacks model.invoke capability")
        instruction = context.step.instruction
        if instruction is None or instruction.prompt is None:
            raise ValueError(f"step {context.step.id!r} has no executable prompt contract")
        prompt = instruction.prompt
        rendered = render_prompt(prompt, inputs=context.inputs, arguments=context.arguments)
        workspace_id = next(
            iter(context.step.access.workspace_ids), context.knowledge.workspace_ids[0]
        )
        disclosure_refs = _references(context.arguments) | set(context.step.access.container_ids)
        if not disclosure_refs:
            disclosure_refs.add(workspace_id)
        operation_key = ":".join(
            str(item)
            for item in (
                context.run_id,
                context.step.id,
                context.loop_index if context.loop_index is not None else "single",
                f"{prompt.id}@{prompt.version}",
            )
        )
        operator_contract = {
            "prompt_id": prompt.id,
            "prompt_version": prompt.version,
            "instruction_id": instruction.id,
            "instruction_version": instruction.version,
            "system": rendered.system,
            "output_schema": prompt.output_schema,
            "rules": list(instruction.rules),
        }
        configuration = {
            **prompt.configuration,
            "operator_contracts": {prompt.operator_id: operator_contract},
        }
        response = await self.client.execute(
            {
                "operator_id": prompt.operator_id,
                "operator_version": prompt.operator_version,
                "operation_key": operation_key,
                "modality": prompt.modality,
                "input": {
                    "prompt_id": prompt.id,
                    "prompt_version": prompt.version,
                    "user_prompt": rendered.user,
                    "arguments": dict(context.arguments),
                },
                "context": {
                    "workspace_id": workspace_id,
                    "project_id": context.workflow_id,
                    "authority_grant_id": f"grant:{context.run_id}",
                    "disclosure_refs": sorted(disclosure_refs),
                },
                "configuration": configuration,
                "requested_status": "proposal",
            }
        )
        status = response.get("status")
        output = response.get("output")
        receipt = response.get("receipt")
        normalized_receipt = dict(receipt) if isinstance(receipt, Mapping) else {}
        normalized_receipt.update(
            {
                "prompt_id": prompt.id,
                "prompt_version": prompt.version,
                "instruction_id": instruction.id,
                "instruction_version": instruction.version,
            }
        )
        if status == "proposal":
            if not isinstance(output, Mapping):
                return StepResult(
                    status=ResultStatus.FAILED,
                    error="prompt output must be an object",
                    error_code="invalid_model_output",
                    receipt=normalized_receipt,
                )
            errors = self.validator.validate(output, prompt.output_schema)
            if errors:
                return StepResult(
                    status=ResultStatus.FAILED,
                    error="; ".join(errors),
                    error_code="invalid_model_output",
                    receipt=normalized_receipt,
                )
            return StepResult(
                status=ResultStatus.SUCCESS,
                output=dict(output),
                receipt=normalized_receipt,
            )
        if status == "partial":
            return StepResult(
                status=ResultStatus.PARTIAL,
                output=output,
                error="; ".join(response.get("errors", [])) or None,
                receipt=normalized_receipt,
            )
        return StepResult(
            status=ResultStatus.HOLD
            if status in {"hold", "branch", "ask", "no_hit"}
            else ResultStatus.FAILED,
            error="; ".join(response.get("errors", [])) or str(response.get("hold_reason", status)),
            error_code=f"operator_{status or 'invalid'}",
            receipt=normalized_receipt,
        )


__all__ = ["PromptStepHandler"]
