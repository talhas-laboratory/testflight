"""Proposal-only handlers for Biotic's relational newsletter workflow.

The deterministic handlers expose only the declared content-strategy material. Model-backed
formation is delegated to the shared prompt handler so this module never couples to a provider.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from testflight_workflows import HandlerRegistry, ResultStatus, StepExecutionContext, StepResult

from .operator_client import HttpOperatorRuntimeClient
from .prompt_handler import PromptStepHandler

CONTENT_STRATEGY_WORKSPACE = "world://workspace/brand/hellobiotic-research/content-strategy"
_STRATEGY_ROOT = Path("workspaces/brand-hellobiotic-research/content-strategy")


def _project_root() -> Path:
    configured = os.environ.get("TESTFLIGHT_PROJECT_ROOT")
    return Path(configured).resolve() if configured else Path.cwd().resolve()


def _read_artifact(name: str) -> tuple[dict[str, Any], str]:
    path = _project_root() / _STRATEGY_ROOT / "artifacts" / name
    return yaml.safe_load(
        path.read_text(encoding="utf-8")
    ), f"repo://{path.relative_to(_project_root())}"


class RelationalNewsletterContextCompiler:
    """Compile strategy, audience, and evidence inputs into a bounded packet."""

    async def execute(self, context: StepExecutionContext) -> StepResult:
        if CONTENT_STRATEGY_WORKSPACE not in context.step.access.workspace_ids:
            raise PermissionError("newsletter context step did not declare the strategy workspace")
        if "knowledge.retrieve" not in context.step.capabilities:
            raise PermissionError("newsletter context step lacks retrieval capability")
        try:
            model, model_ref = _read_artifact("relational-content-model.yaml")
            charter, charter_ref = _read_artifact("newsletter-agent-charter.yaml")
            rubric, rubric_ref = _read_artifact("evaluation-rubric.yaml")
        except FileNotFoundError:
            return StepResult(
                status=ResultStatus.HOLD,
                output={"reason": "content_strategy_artifact_missing"},
                receipt={"workspace_id": CONTENT_STRATEGY_WORKSPACE, "status": "hold"},
            )

        audience = dict(context.arguments["audience_context"])
        source_status = str(audience.get("source_status", "")).strip()
        if source_status not in {"explicit", "aggregated", "unknown"}:
            return StepResult(
                status=ResultStatus.HOLD,
                output={"reason": "audience_context_requires_supported_source_status"},
                receipt={"status": "hold"},
            )
        evidence = list(context.arguments["evidence_packet"])
        malformed = [
            index
            for index, item in enumerate(evidence)
            if not isinstance(item, Mapping)
            or not all(
                isinstance(item.get(key), str) and item[key].strip()
                for key in ("claim", "source_ref", "evidence_status")
            )
            or not isinstance(item.get("limitations"), list)
        ]
        if malformed:
            return StepResult(
                status=ResultStatus.HOLD,
                output={"reason": "evidence_packet_is_not_traceable", "invalid_indices": malformed},
                receipt={"status": "hold"},
            )
        return StepResult(
            status=ResultStatus.SUCCESS,
            output={
                "packet_id": f"packet:{context.run_id}:biotic-newsletter",
                "workspace_id": CONTENT_STRATEGY_WORKSPACE,
                "issue_objective": context.arguments["issue_objective"],
                "audience_context": audience,
                "evidence_packet": evidence,
                "current_field_signals": context.arguments.get("current_field_signals", []),
                "prior_issue_feedback": context.arguments.get("prior_issue_feedback", []),
                "authorized_product_context": context.arguments.get("authorized_product_context"),
                "relational_contract": model["composition_contract"],
                "candidate_fields": model["biotic_candidate_fields"],
                "charter": {
                    "editorial_modes": charter["editorial_modes"],
                    "claim_policy": charter["claim_policy"],
                    "product_role_values": charter["issue_packet"]["product_role_values"],
                },
                "rubric": rubric,
                "limitations": [
                    "Founder-directed strategy is an editorial constraint, not customer evidence.",
                    (
                        "Audience context does not authorize inference about an individual's "
                        "identity, "
                        "health, insecurity, or motive."
                    ),
                    (
                        "Evidence packet items remain source-bound proposals; retrieval does not "
                        "establish truth."
                    ),
                    (
                        "This workflow produces a reviewable proposal only and has no publication "
                        "authority."
                    ),
                ],
            },
            receipt={
                "workspace_id": CONTENT_STRATEGY_WORKSPACE,
                "source_refs": [model_ref, charter_ref, rubric_ref],
                "operator_ids": [
                    "world://operator/guardrail/workspace-isolation@1",
                    "world://operator/guardrail/evidence-truth-conflation@1",
                    "world://operator/guardrail/ontology-conflation@1",
                ],
            },
        )


class NewsletterReviewPackagePreparer:
    """Make the final proposal explicitly reviewable without persisting or publishing it."""

    async def execute(self, context: StepExecutionContext) -> StepResult:
        evaluation = context.arguments["evaluation"]
        if evaluation.get("decision") != "review_ready":
            return StepResult(
                status=ResultStatus.HOLD,
                output={
                    "reason": "editorial_evaluation_did_not_clear_review_gate",
                    "evaluation": evaluation,
                },
                receipt={"status": "hold"},
            )
        return StepResult(
            status=ResultStatus.SUCCESS,
            output={
                "request_id": context.arguments["request_id"],
                "status": "review_required",
                "publication_status": "proposal_only",
                "canonical_write": False,
                "send_authorized": False,
                "context_packet_id": context.arguments["context"]["packet_id"],
                "relational_composition": context.arguments["composition"],
                "content_plan": context.arguments["content_plan"],
                "draft": context.arguments["draft"],
                "evaluation": evaluation,
                "limitations": context.arguments["context"]["limitations"],
                "next_required_decision": "human_editorial_review",
            },
            receipt={
                "operator_ids": [
                    "world://operator/guardrail/evaluation-schema@1",
                    "world://operator/guardrail/validation-persistence-conflation@1",
                ],
                "publication_action": "not_available_in_this_workflow",
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
            raise ValueError("Biotic newsletter handlers require operator_runtime_endpoint")
        client = HttpOperatorRuntimeClient(
            endpoint,
            timeout_seconds=float(settings.get("operator_runtime_timeout_seconds", 120)),
        )
    prompt_handler = PromptStepHandler(client)
    registry.register("biotic.compile_newsletter_context", RelationalNewsletterContextCompiler())
    registry.register("biotic.compose_newsletter_issue", prompt_handler)
    registry.register("biotic.form_newsletter_content_plan", prompt_handler)
    registry.register("biotic.draft_newsletter", prompt_handler)
    registry.register("biotic.evaluate_newsletter", prompt_handler)
    registry.register("biotic.prepare_newsletter_review_package", NewsletterReviewPackagePreparer())


__all__ = ["register_workflow_handlers"]
