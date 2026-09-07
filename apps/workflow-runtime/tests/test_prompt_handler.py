from __future__ import annotations

import asyncio
import json
from pathlib import Path

from testflight_workflow_runtime.operator_client import HttpOperatorRuntimeClient
from testflight_workflow_runtime.prompt_handler import PromptStepHandler
from testflight_workflows import (
    ResultStatus,
    StepExecutionContext,
    WorkflowPrincipal,
    load_workflow,
)

ROOT = Path(__file__).parents[3]


class Client:
    def __init__(self, output):
        self.output = output
        self.payload = None

    async def execute(self, payload):
        self.payload = payload
        return {
            "status": "proposal",
            "output": self.output,
            "errors": [],
            "receipt": {"provider_id": "fake", "model_id": "fake-model"},
        }


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        return None

    def read(self):
        return json.dumps(self.payload).encode()


def context_for(step_id: str) -> StepExecutionContext:
    workflow = load_workflow(ROOT / "workflows/examples/evidence-synthesis.yaml")
    step = next(item for item in workflow.steps if item.id == step_id)
    return StepExecutionContext(
        run_id="run:prompt-test",
        workflow_id=workflow.id,
        workflow_version=workflow.version,
        principal_id=WorkflowPrincipal(id="agent:testflight-research").id,
        step=step,
        inputs={"question": "Question", "request_id": "request:prompt-test"},
        arguments={
            "question": "Question",
            "evidence": [],
        },
        prior_results={},
        authority=workflow.authority,
        knowledge=workflow.knowledge,
    )


def test_prompt_handler_renders_contract_and_preserves_runtime_receipt():
    client = Client(
        {
            "question": "Question",
            "recommendation": "Collect direct evidence.",
            "epistemic_status": "proposal_only",
            "evidence_refs": [],
            "source_urls": [],
            "limitations": [],
            "canonical_write": False,
        }
    )
    result = asyncio.run(PromptStepHandler(client).execute(context_for("synthesize")))

    assert result.status is ResultStatus.SUCCESS
    assert result.receipt["provider_id"] == "fake"
    assert result.receipt["prompt_id"] == "prompt://testflight/research/synthesize-proposal"
    assert client.payload["operator_id"] == "runtime://testflight/workflow/prompt-step"
    assert 'Research question: "Question"' in client.payload["input"]["user_prompt"]
    assert client.payload["context"]["workspace_id"].endswith("research-learning")


def test_prompt_handler_rejects_schema_valid_but_forbidden_canonical_write():
    client = Client(
        {
            "question": "Question",
            "recommendation": "Unsafe",
            "epistemic_status": "proposal_only",
            "evidence_refs": [],
            "source_urls": [],
            "limitations": [],
            "canonical_write": True,
        }
    )
    result = asyncio.run(PromptStepHandler(client).execute(context_for("synthesize")))

    assert result.status is ResultStatus.FAILED
    assert result.error_code == "invalid_model_output"
    assert "must equal False" in result.error


def test_operator_http_client_sends_normalized_json_without_credentials():
    captured = {}

    def open_url(request, timeout):
        captured["payload"] = json.loads(request.data.decode())
        captured["timeout"] = timeout
        return FakeResponse({"status": "proposal", "output": {"ok": True}})

    client = HttpOperatorRuntimeClient(
        "http://127.0.0.1:8781/execute", timeout_seconds=3, open_url=open_url
    )
    result = asyncio.run(client.execute({"operator_id": "runtime://operator", "input": {}}))

    assert result["status"] == "proposal"
    assert captured["payload"]["operator_id"] == "runtime://operator"
    assert captured["timeout"] == 3
