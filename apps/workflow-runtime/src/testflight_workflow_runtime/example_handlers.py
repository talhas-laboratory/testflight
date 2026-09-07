"""Concrete local handlers for the tracked evidence-synthesis example."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from testflight_workflows import (
    HandlerRegistry,
    ResultStatus,
    StepExecutionContext,
    StepResult,
)

from .operator_client import HttpOperatorRuntimeClient
from .prompt_handler import PromptStepHandler

RESEARCH_WORKSPACE = "world://workspace/testflight-product/research-learning"
DISPATCH_ACTION = "action://testflight/proposal/dispatch"
_WORDS = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "does",
    "for",
    "how",
    "in",
    "is",
    "of",
    "should",
    "the",
    "to",
    "what",
}


def _tokens(value: str) -> set[str]:
    return set(_WORDS.findall(value.lower())) - _STOP_WORDS


def _project_root() -> Path:
    configured = os.environ.get("TESTFLIGHT_PROJECT_ROOT")
    return Path(configured).resolve() if configured else Path.cwd().resolve()


def _catalog_records(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in payload.get("research_programs", []):
        records.append({"kind": "research_program", **item})
    for item in payload.get("hypotheses", []):
        records.append({"kind": "hypothesis", **item})
    for item in payload.get("proposed_experiments", []):
        records.append({"kind": "proposed_experiment", **item})
    return records


class ResearchCatalogRetriever:
    async def execute(self, context: StepExecutionContext) -> StepResult:
        if RESEARCH_WORKSPACE not in context.step.access.workspace_ids:
            raise PermissionError("research workflow step did not declare its workspace")
        if RESEARCH_WORKSPACE not in context.step.access.container_ids:
            raise PermissionError("research workflow step did not declare its container")
        if "knowledge.retrieve" not in context.step.capabilities:
            raise PermissionError("research workflow step lacks retrieval capability")

        path = (
            _project_root()
            / "workspaces/testflight-product/research-learning/artifacts/research-catalog.yaml"
        )
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        query = str(context.arguments["query"])
        query_tokens = _tokens(query)
        ranked: list[tuple[int, dict[str, Any]]] = []
        for record in _catalog_records(payload):
            searchable = json.dumps(record, sort_keys=True)
            score = len(query_tokens & _tokens(searchable))
            if score:
                ranked.append((score, {**record, "retrieval_score": score}))
        requested = int(context.arguments.get("max_results", context.knowledge.max_results))
        limit = min(requested, context.knowledge.max_results)
        items = [record for _, record in sorted(ranked, key=lambda item: (-item[0], item[1]["id"]))]
        instruction = context.step.instruction
        return StepResult(
            status=ResultStatus.SUCCESS,
            output={"items": items[:limit]},
            receipt={
                "source": "repo://workspaces/testflight-product/research-learning/artifacts/research-catalog.yaml",
                "workspace_id": RESEARCH_WORKSPACE,
                "container_id": RESEARCH_WORKSPACE,
                "matched": min(len(items), limit),
                "status": "hit" if items else "no_hit",
                "instruction_id": instruction.id if instruction else None,
                "instruction_version": instruction.version if instruction else None,
            },
        )


class ProposalDispatcher:
    async def execute(self, context: StepExecutionContext) -> StepResult:
        if not context.authority.external_action or not context.authority.proposal_write:
            raise PermissionError("workflow grant lacks proposal dispatch authority")
        if DISPATCH_ACTION not in context.authority.action_ids:
            raise PermissionError("workflow grant does not include the dispatch action")
        if DISPATCH_ACTION not in context.step.action_ids:
            raise PermissionError("workflow step does not declare the dispatch action")

        proposal = dict(context.arguments["proposal"])
        digest = hashlib.sha256(
            json.dumps(proposal, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16]
        proposal_id = f"proposal:{digest}"
        output_dir = Path(
            os.environ.get(
                "TESTFLIGHT_WORKFLOW_OUTPUT_DIR",
                _project_root() / ".data/workflow-runtime/dispatched-proposals",
            )
        ).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        destination = output_dir / f"{digest}.json"
        destination.write_text(
            json.dumps(
                {
                    "proposal_id": proposal_id,
                    "workflow_id": context.workflow_id,
                    "workflow_version": context.workflow_version,
                    "principal_id": context.principal_id,
                    "run_id": context.run_id,
                    "status": "dispatched_as_proposal",
                    "proposal": proposal,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        instruction = context.step.instruction
        return StepResult(
            status=ResultStatus.SUCCESS,
            output={
                "proposal_id": proposal_id,
                "status": "dispatched_as_proposal",
                "canonical_write": False,
            },
            receipt={
                "action_id": DISPATCH_ACTION,
                "proposal_id": proposal_id,
                "artifact": str(destination),
                "instruction_id": instruction.id if instruction else None,
                "instruction_version": instruction.version if instruction else None,
            },
        )


def register_workflow_handlers(
    registry: HandlerRegistry, configuration: Mapping[str, Any] | None = None
) -> None:
    settings = configuration or {}
    client = settings.get("operator_client")
    if client is None:
        endpoint = settings.get("operator_runtime_endpoint")
        if not isinstance(endpoint, str) or not endpoint.strip():
            raise ValueError("example handlers require operator_runtime_endpoint")
        client = HttpOperatorRuntimeClient(
            endpoint,
            timeout_seconds=float(settings.get("operator_runtime_timeout_seconds", 120)),
        )
    prompt_handler = PromptStepHandler(client)
    registry.register("knowledge.retrieve", ResearchCatalogRetriever())
    registry.register("reasoning.evaluate_evidence", prompt_handler)
    registry.register("reasoning.synthesize_proposal", prompt_handler)
    registry.register("action.dispatch_proposal", ProposalDispatcher())


__all__ = ["register_workflow_handlers"]
