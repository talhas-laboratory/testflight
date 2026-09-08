from __future__ import annotations

import asyncio
from pathlib import Path

from testflight_adapter_langgraph import LangGraphWorkflowEngine
from testflight_adapter_sqlite_workflow_runtime import SqliteWorkflowRuntimeStore
from testflight_workflow_runtime.biotic_newsletter_handlers import NewsletterReviewPackagePreparer
from testflight_workflow_runtime.config import load_catalog, load_handlers
from testflight_workflow_runtime.service import WorkflowRuntimeService
from testflight_workflows import ResultStatus, StepExecutionContext, WorkflowPrincipal

ROOT = Path(__file__).parents[3]


class FakeNewsletterOperatorClient:
    async def execute(self, payload):
        prompt_id = payload["input"]["prompt_id"]
        if prompt_id.endswith("compose-issue"):
            output = {
                "composition_id": "composition:skin-ecology-01",
                "decision": "selected",
                "candidates": [
                    {
                        "candidate_id": "candidate:skin-ecology",
                        "field": "skin ecology",
                        "reader_question": (
                            "What does a skin ecosystem lens change in a daily ritual?"
                        ),
                        "contribution": "A practical explanatory deep dive.",
                        "editorial_mode": "deep_dive",
                        "moment": "A reader is examining everyday hygiene choices.",
                        "brand_legitimacy_basis": (
                            "Biotic can contribute a bounded hygiene perspective."
                        ),
                        "product_role": "none",
                        "relevance_assessment": {
                            "field_centrality": 4,
                            "lived_stake": 3,
                            "contribution_value": 4,
                            "brand_legitimacy": 4,
                            "reader_independence": 4,
                        },
                    }
                ],
                "selected_candidate_id": "candidate:skin-ecology",
                "selected": {
                    "field": "skin ecology",
                    "reader_question": "What does a skin ecosystem lens change in a daily ritual?",
                    "contribution": "A practical explanatory deep dive.",
                    "editorial_mode": "deep_dive",
                    "moment": "A reader is examining everyday hygiene choices.",
                    "brand_legitimacy_basis": (
                        "Biotic can contribute a bounded hygiene perspective."
                    ),
                    "product_role": "none",
                },
                "assumptions": ["Audience context is aggregated."],
                "uncertainty_notes": ["No individual motive is inferred."],
                "publication_status": "proposal_only",
            }
        elif prompt_id.endswith("form-content-plan"):
            output = {
                "composition_id": "composition:skin-ecology-01",
                "locked": {
                    "controlling_idea": (
                        "A skin ecosystem lens changes how a daily ritual is understood."
                    ),
                    "reader_promise": "Clarify one useful lens.",
                    "product_role": "none",
                    "claim_boundary": "Use the single supplied claim only.",
                    "cta_boundary": "Invite reflection, not purchase.",
                },
                "directional": {"voice": "calm and precise"},
                "open": {"title_alternatives": ["writer choice"]},
                "content_system": {"sections": ["hook", "explanation", "practice"]},
                "artifact_characteristics": {
                    "length": "700-900 words",
                    "format": "editorial letter",
                },
                "factual_claims": [
                    {
                        "claim_id": "claim:skin-microbiome-01",
                        "evidence_id": "evidence:microbiome-1",
                        "claim": "Skin hosts microbial communities.",
                        "source_ref": "source:microbiome-1",
                        "allowed_expression": "Educational, non-clinical explanation.",
                        "limitations": ["General educational context only."],
                    }
                ],
                "product_role": "none",
                "product_role_rationale": "The contribution is valuable without a product mention.",
                "publication_status": "proposal_only",
            }
        elif prompt_id.endswith("draft-newsletter"):
            output = {
                "composition_id": "composition:skin-ecology-01",
                "product_role": "none",
                "subject_options": ["Your skin is an ecosystem"],
                "preheader": "A practical lens for a daily ritual.",
                "sections": [{"heading": "The ecosystem lens", "body": "Draft copy."}],
                "closing": "A question to carry into your routine.",
                "feedback_prompt": "Which routine question would you like us to unpack next?",
                "claims_used": [
                    {
                        "claim_id": "claim:skin-microbiome-01",
                        "evidence_id": "evidence:microbiome-1",
                        "source_ref": "source:microbiome-1",
                        "used_statement": "Skin hosts microbial communities.",
                    }
                ],
                "publication_status": "proposal_only",
            }
        elif prompt_id.endswith("evaluate-issue"):
            output = {
                "composition_id": "composition:skin-ecology-01",
                "product_role": "none",
                "decision": "review_ready",
                "hard_gates": [
                    {
                        "id": "claim_traceability",
                        "status": "pass",
                        "rationale": "Claim has a source.",
                    },
                    {
                        "id": "non_exploitative_identity",
                        "status": "pass",
                        "rationale": "No identity claim.",
                    },
                    {
                        "id": "epistemic_precision",
                        "status": "pass",
                        "rationale": "Claim is bounded.",
                    },
                    {
                        "id": "authority_boundary",
                        "status": "pass",
                        "rationale": "No publication authorization.",
                    },
                ],
                "rubric_scores": {
                    "reader_value": 4,
                    "brand_legitimacy": 4,
                    "reader_independence": 4,
                },
                "findings": ["The draft preserves the selected field and contribution."],
                "required_revisions": [],
                "claim_trace": [
                    {
                        "claim": "Skin hosts microbial communities.",
                        "claim_id": "claim:skin-microbiome-01",
                        "evidence_id": "evidence:microbiome-1",
                        "source_ref": "source:microbiome-1",
                    }
                ],
                "residual_uncertainty": ["No individual motive is inferred."],
                "publication_status": "proposal_only",
            }
        else:
            raise AssertionError(f"unexpected prompt: {prompt_id}")
        return {
            "status": "proposal",
            "output": output,
            "errors": [],
            "receipt": {"provider_id": "fake-newsletter-model", "preflight_passed": True},
        }


def test_biotic_newsletter_workflow_returns_review_only_package(tmp_path, monkeypatch):
    monkeypatch.setenv("TESTFLIGHT_PROJECT_ROOT", str(ROOT))
    catalog = load_catalog(ROOT / "workflows/registry.yaml")
    handlers = load_handlers(
        ("testflight_workflow_runtime.biotic_newsletter_handlers",),
        {
            "testflight_workflow_runtime.biotic_newsletter_handlers": {
                "operator_client": FakeNewsletterOperatorClient()
            }
        },
    )
    engine = LangGraphWorkflowEngine(
        catalog=catalog,
        handlers=handlers,
        idempotency=SqliteWorkflowRuntimeStore(tmp_path / "runtime.sqlite3"),
    )
    service = WorkflowRuntimeService(
        catalog=catalog,
        engine=engine,
        run_store=SqliteWorkflowRuntimeStore(tmp_path / "runs.sqlite3"),
    )

    record = asyncio.run(
        service.run_and_wait(
            principal=WorkflowPrincipal(id="agent:hellobiotic-newsletter-strategist"),
            workflow_id="workflow://testflight/biotic/newsletter-compose",
            workflow_version=2,
            run_id="run:biotic-newsletter",
            inputs={
                "request_id": "request:biotic-newsletter",
                "issue_objective": "Help readers understand skin ecology in a daily ritual.",
                "audience_context": {
                    "source_status": "aggregated",
                    "description": "Opt-in interest signal.",
                    "source_refs": ["source:biotic-opt-in-interest-aggregate"],
                },
                "evidence_packet": [
                    {
                        "evidence_id": "evidence:microbiome-1",
                        "claim": "Skin hosts microbial communities.",
                        "source_ref": "source:microbiome-1",
                        "evidence_status": "reviewed_source",
                        "limitations": ["General educational context only."],
                    }
                ],
                "current_field_signals": [],
                "prior_issue_feedback": [],
                "authorized_product_context": {},
            },
        )
    )

    assert record.result is not None
    assert record.result.status is ResultStatus.SUCCESS
    package = record.result.outputs["review_package"]
    assert package["status"] == "review_required"
    assert package["publication_status"] == "proposal_only"
    assert package["canonical_write"] is False
    assert package["send_authorized"] is False
    assert package["content_plan"]["product_role"] == "none"
    assert package["draft"]["claims_used"][0]["evidence_id"] == "evidence:microbiome-1"
    assert package["next_required_decision"] == "human_editorial_review"


def test_review_package_rejects_claim_lineage_drift():
    catalog = load_catalog(ROOT / "workflows/registry.yaml")
    workflow = catalog.get(
        WorkflowPrincipal(id="agent:hellobiotic-newsletter-strategist"),
        "workflow://testflight/biotic/newsletter-compose",
        2,
    )
    assert workflow is not None
    step = next(item for item in workflow.steps if item.id == "prepare_review_package")
    composition_id = "composition:test"
    result = asyncio.run(
        NewsletterReviewPackagePreparer().execute(
            StepExecutionContext(
                run_id="run:claim-drift",
                workflow_id=workflow.id,
                workflow_version=workflow.version,
                principal_id="agent:hellobiotic-newsletter-strategist",
                step=step,
                inputs={"request_id": "request:claim-drift"},
                arguments={
                    "request_id": "request:claim-drift",
                    "context": {
                        "packet_id": "packet:test",
                        "evidence_packet": [
                            {"evidence_id": "evidence:known", "source_ref": "source:known"}
                        ],
                        "limitations": [],
                    },
                    "composition": {
                        "composition_id": composition_id,
                        "publication_status": "proposal_only",
                        "selected": {"product_role": "none"},
                    },
                    "content_plan": {
                        "composition_id": composition_id,
                        "publication_status": "proposal_only",
                        "product_role": "none",
                        "factual_claims": [
                            {
                                "claim_id": "claim:known",
                                "evidence_id": "evidence:known",
                                "source_ref": "source:known",
                            }
                        ],
                    },
                    "draft": {
                        "composition_id": composition_id,
                        "publication_status": "proposal_only",
                        "product_role": "none",
                        "claims_used": [
                            {
                                "claim_id": "claim:drifted",
                                "evidence_id": "evidence:unknown",
                                "source_ref": "source:unknown",
                            }
                        ],
                    },
                    "evaluation": {
                        "composition_id": composition_id,
                        "publication_status": "proposal_only",
                        "decision": "review_ready",
                        "hard_gates": [
                            {"id": gate_id, "status": "pass"}
                            for gate_id in (
                                "claim_traceability",
                                "non_exploitative_identity",
                                "epistemic_precision",
                                "authority_boundary",
                            )
                        ],
                        "claim_trace": [],
                    },
                },
                prior_results={},
                authority=workflow.authority,
                knowledge=workflow.knowledge,
            )
        )
    )
    assert result.status is ResultStatus.HOLD
    assert result.output["reason"] == "claim_lineage_continuity_failed"
