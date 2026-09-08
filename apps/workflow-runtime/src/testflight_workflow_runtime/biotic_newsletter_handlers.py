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
_REQUIRED_REVIEW_GATES = {
    "claim_traceability",
    "non_exploitative_identity",
    "epistemic_precision",
    "authority_boundary",
}
_PRODUCT_ROLE_RANK = {
    "none": 0,
    "contextual": 1,
    "illustrative": 2,
    "practical": 3,
    "central_and_justified": 4,
}


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
        source_refs = audience.get("source_refs")
        if not isinstance(source_refs, list) or not all(
            isinstance(reference, str) and reference.strip() for reference in source_refs
        ):
            return StepResult(
                status=ResultStatus.HOLD,
                output={"reason": "audience_context_requires_source_refs"},
                receipt={"status": "hold"},
            )
        evidence = list(context.arguments["evidence_packet"])
        malformed = [
            index
            for index, item in enumerate(evidence)
            if not isinstance(item, Mapping)
            or not all(
                isinstance(item.get(key), str) and item[key].strip()
                for key in ("evidence_id", "claim", "source_ref", "evidence_status")
            )
            or not isinstance(item.get("limitations"), list)
        ]
        if malformed:
            return StepResult(
                status=ResultStatus.HOLD,
                output={"reason": "evidence_packet_is_not_traceable", "invalid_indices": malformed},
                receipt={"status": "hold"},
            )
        evidence_ids = [str(item["evidence_id"]) for item in evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            return StepResult(
                status=ResultStatus.HOLD,
                output={"reason": "evidence_packet_contains_duplicate_evidence_ids"},
                receipt={"status": "hold"},
            )
        personalization_mode = {
            "explicit": "contextual_only",
            "aggregated": "audience_level_only",
            "unknown": "broad_non_personalized_only",
        }[source_status]
        return StepResult(
            status=ResultStatus.SUCCESS,
            output={
                "packet_id": f"packet:{context.run_id}:biotic-newsletter",
                "workspace_id": CONTENT_STRATEGY_WORKSPACE,
                "issue_objective": context.arguments["issue_objective"],
                "audience_context": audience,
                "personalization_mode": personalization_mode,
                "evidence_packet": evidence,
                "current_field_signals": context.arguments.get("current_field_signals", []),
                "prior_issue_feedback": context.arguments.get("prior_issue_feedback", []),
                "authorized_product_context": context.arguments.get("authorized_product_context"),
                "relational_contract": model["composition_contract"],
                "candidate_fields": model["biotic_candidate_fields"],
                "composition_requirements": {
                    "required_relations": model["composition_contract"]["required"],
                    "optional_relations": model["composition_contract"]["optional"],
                    "forbidden_substitutions": model["composition_contract"][
                        "forbidden_substitutions"
                    ],
                    "uncertain_compositions": model["composition_contract"][
                        "uncertain_compositions"
                    ],
                },
                "charter": {
                    "editorial_modes": charter["editorial_modes"],
                    "claim_policy": charter["claim_policy"],
                    "product_role_values": charter["issue_packet"]["product_role_values"],
                },
                "rubric": rubric,
                "handoff_invariants": {
                    "composition_id": "Must be preserved by every subsequent node.",
                    "claim_ids": (
                        "Every factual claim must resolve to an evidence_id and source_ref."
                    ),
                    "product_role": (
                        "May narrow but must not become more central without new authority."
                    ),
                    "publication_status": "Must remain proposal_only.",
                },
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
        composition = context.arguments["composition"]
        content_plan = context.arguments["content_plan"]
        draft = context.arguments["draft"]
        context_packet = context.arguments["context"]
        if evaluation.get("decision") != "review_ready":
            return StepResult(
                status=ResultStatus.HOLD,
                output={
                    "reason": "editorial_evaluation_did_not_clear_review_gate",
                    "evaluation": evaluation,
                },
                receipt={"status": "hold"},
            )
        if any(
            item.get("publication_status") != "proposal_only"
            for item in (composition, content_plan, draft, evaluation)
            if isinstance(item, Mapping)
        ):
            return StepResult(
                status=ResultStatus.HOLD,
                output={"reason": "publication_status_drift"},
                receipt={"status": "hold"},
            )
        composition_id = composition.get("composition_id")
        if (
            not isinstance(composition_id, str)
            or not composition_id
            or any(
                item.get("composition_id") != composition_id
                for item in (content_plan, draft, evaluation)
                if isinstance(item, Mapping)
            )
        ):
            return StepResult(
                status=ResultStatus.HOLD,
                output={"reason": "composition_continuity_failed"},
                receipt={"status": "hold"},
            )
        selected = composition.get("selected")
        source_product_role = (
            selected.get("product_role") if isinstance(selected, Mapping) else None
        )
        downstream_roles = [content_plan.get("product_role"), draft.get("product_role")]
        if (
            source_product_role not in _PRODUCT_ROLE_RANK
            or any(role not in _PRODUCT_ROLE_RANK for role in downstream_roles)
            or any(
                _PRODUCT_ROLE_RANK[role] > _PRODUCT_ROLE_RANK[source_product_role]
                for role in downstream_roles
            )
        ):
            return StepResult(
                status=ResultStatus.HOLD,
                output={"reason": "product_role_continuity_failed"},
                receipt={"status": "hold"},
            )
        gates = evaluation.get("hard_gates")
        passed_gates = (
            {
                item.get("id")
                for item in gates
                if isinstance(item, Mapping) and item.get("status") == "pass"
            }
            if isinstance(gates, list)
            else set()
        )
        if not _REQUIRED_REVIEW_GATES.issubset(passed_gates):
            return StepResult(
                status=ResultStatus.HOLD,
                output={"reason": "required_review_gates_not_passed", "evaluation": evaluation},
                receipt={"status": "hold"},
            )
        evidence_by_id = {
            item["evidence_id"]: item["source_ref"] for item in context_packet["evidence_packet"]
        }
        factual_claims = content_plan.get("factual_claims")
        claims_used = draft.get("claims_used")
        claim_trace = evaluation.get("claim_trace")
        if not all(isinstance(value, list) for value in (factual_claims, claims_used, claim_trace)):
            return StepResult(
                status=ResultStatus.HOLD,
                output={"reason": "claim_trace_contract_invalid"},
                receipt={"status": "hold"},
            )
        plan_claim_ids = {
            item.get("claim_id")
            for item in factual_claims
            if isinstance(item, Mapping)
            and evidence_by_id.get(item.get("evidence_id")) == item.get("source_ref")
        }
        used_claim_ids = {
            item.get("claim_id")
            for item in claims_used
            if isinstance(item, Mapping)
            and evidence_by_id.get(item.get("evidence_id")) == item.get("source_ref")
        }
        traced_claim_ids = {
            item.get("claim_id")
            for item in claim_trace
            if isinstance(item, Mapping)
            and evidence_by_id.get(item.get("evidence_id")) == item.get("source_ref")
        }
        if (
            len(plan_claim_ids) != len(factual_claims)
            or len(used_claim_ids) != len(claims_used)
            or len(traced_claim_ids) != len(claim_trace)
            or not used_claim_ids.issubset(plan_claim_ids)
            or not used_claim_ids.issubset(traced_claim_ids)
        ):
            return StepResult(
                status=ResultStatus.HOLD,
                output={"reason": "claim_lineage_continuity_failed"},
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
                "context_packet_id": context_packet["packet_id"],
                "relational_composition": composition,
                "content_plan": content_plan,
                "draft": draft,
                "evaluation": evaluation,
                "limitations": context_packet["limitations"],
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
