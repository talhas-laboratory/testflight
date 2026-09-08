from __future__ import annotations

import asyncio
from pathlib import Path

from testflight_adapter_langgraph import LangGraphWorkflowEngine
from testflight_adapter_sqlite_workflow_runtime import SqliteWorkflowRuntimeStore
from testflight_workflow_runtime.config import load_catalog, load_handlers
from testflight_workflow_runtime.service import WorkflowRuntimeService
from testflight_workflows import ResultStatus, WorkflowPrincipal

ROOT = Path(__file__).parents[3]


class FakeNewsletterOperatorClient:
    async def execute(self, payload):
        prompt_id = payload["input"]["prompt_id"]
        if prompt_id.endswith("compose-issue"):
            output = {
                "field": "skin ecology",
                "reader_question": "What does a skin ecosystem lens change in a daily ritual?",
                "contribution": "A practical explanatory deep dive.",
                "moment": "A reader is examining everyday hygiene choices.",
                "brand_legitimacy_basis": "Biotic can contribute a bounded hygiene perspective.",
                "product_role": "none",
                "assumptions": ["Audience context is aggregated."],
                "uncertainty_notes": ["No individual motive is inferred."],
                "publication_status": "proposal_only",
            }
        elif prompt_id.endswith("form-content-plan"):
            output = {
                "locked": {"reader_promise": "Clarify one useful lens."},
                "directional": {"voice": "calm and precise"},
                "open": {"title_alternatives": "writer choice"},
                "content_system": {"sections": ["hook", "explanation", "practice"]},
                "artifact_characteristics": {"length": "700-900 words"},
                "factual_claims": [
                    {
                        "claim": "Skin hosts microbial communities.",
                        "source_ref": "source:microbiome-1",
                    }
                ],
                "product_role": "none",
                "publication_status": "proposal_only",
            }
        elif prompt_id.endswith("draft-newsletter"):
            output = {
                "subject_options": ["Your skin is an ecosystem"],
                "preheader": "A practical lens for a daily ritual.",
                "sections": [{"heading": "The ecosystem lens", "body": "Draft copy."}],
                "closing": "A question to carry into your routine.",
                "claims_used": ["Skin hosts microbial communities."],
                "publication_status": "proposal_only",
            }
        elif prompt_id.endswith("evaluate-issue"):
            output = {
                "decision": "review_ready",
                "hard_gates": [{"id": "claim_traceability", "passed": True}],
                "rubric_scores": {"reader_value": 4, "brand_legitimacy": 4},
                "required_revisions": [],
                "claim_trace": [
                    {
                        "claim": "Skin hosts microbial communities.",
                        "source_ref": "source:microbiome-1",
                    }
                ],
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
            workflow_version=1,
            run_id="run:biotic-newsletter",
            inputs={
                "request_id": "request:biotic-newsletter",
                "issue_objective": "Help readers understand skin ecology in a daily ritual.",
                "audience_context": {
                    "source_status": "aggregated",
                    "description": "Opt-in interest signal.",
                },
                "evidence_packet": [
                    {
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
    assert package["draft"]["claims_used"] == ["Skin hosts microbial communities."]
    assert package["next_required_decision"] == "human_editorial_review"
