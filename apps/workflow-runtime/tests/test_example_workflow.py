from __future__ import annotations

import asyncio
import json
from pathlib import Path

from mcp import Client
from testflight_adapter_langgraph import LangGraphWorkflowEngine
from testflight_adapter_mcp_workflows import create_mcp_server
from testflight_adapter_sqlite_workflow_runtime import SqliteWorkflowRuntimeStore
from testflight_workflow_runtime.config import load_catalog, load_handlers
from testflight_workflow_runtime.service import WorkflowRuntimeService
from testflight_workflows import ResultStatus, WorkflowPrincipal

ROOT = Path(__file__).parents[3]


class FakeOperatorClient:
    def __init__(self) -> None:
        self.calls = []

    async def execute(self, payload):
        self.calls.append(payload)
        prompt_id = payload["input"]["prompt_id"]
        arguments = payload["input"]["arguments"]
        if prompt_id.endswith("evaluate-record"):
            record = arguments["record"]
            limitations = list(record.get("limitations", []))
            if record.get("limitation"):
                limitations.append(record["limitation"])
            output = {
                "record_id": record["id"],
                "kind": record["kind"],
                "relevance_score": record.get("retrieval_score", 0),
                "evidence_strength": (
                    "supported_with_limitations"
                    if record.get("status")
                    in {"complete_with_limitations", "desk_research_supported"}
                    else "hypothesis_only"
                ),
                "source_url": record.get("source_url"),
                "findings": record.get("findings", []),
                "measures": record.get("measures", []),
                "limitations": limitations,
            }
        else:
            evidence = arguments["evidence"]
            output = {
                "question": arguments["question"],
                "recommendation": "Run a bounded design-partner pilot.",
                "epistemic_status": "proposal_supported_by_scoped_evidence",
                "evidence_refs": [item["record_id"] for item in evidence],
                "source_urls": [item["source_url"] for item in evidence if item["source_url"]],
                "limitations": sorted(
                    {value for item in evidence for value in item["limitations"]}
                ),
                "canonical_write": False,
            }
        return {
            "status": "proposal",
            "output": output,
            "errors": [],
            "receipt": {
                "provider_id": "fake-operator-provider",
                "model_id": "fake-structured-model",
                "preflight_passed": True,
            },
        }


def test_assigned_agent_executes_real_langgraph_workflow(tmp_path, monkeypatch):
    monkeypatch.setenv("TESTFLIGHT_PROJECT_ROOT", str(ROOT))
    monkeypatch.setenv("TESTFLIGHT_WORKFLOW_OUTPUT_DIR", str(tmp_path / "proposals"))
    catalog = load_catalog(ROOT / "workflows/registry.yaml")
    operator_client = FakeOperatorClient()
    handlers = load_handlers(
        ("testflight_workflow_runtime.example_handlers",),
        {"testflight_workflow_runtime.example_handlers": {"operator_client": operator_client}},
    )
    store = SqliteWorkflowRuntimeStore(tmp_path / "runtime.sqlite3")
    engine = LangGraphWorkflowEngine(catalog=catalog, handlers=handlers, idempotency=store)
    service = WorkflowRuntimeService(catalog=catalog, engine=engine, run_store=store)
    principal = WorkflowPrincipal(id="agent:testflight-research")

    async def exercise():
        first = await service.run_and_wait(
            principal=principal,
            workflow_id="workflow://testflight/evidence-synthesis",
            workflow_version=1,
            run_id="run:langgraph-agent-test",
            inputs={
                "question": "What should Testflight validate for campaign decision intelligence?",
                "request_id": "request:langgraph-agent-test",
            },
        )
        replay = await service.run_and_wait(
            principal=principal,
            workflow_id="workflow://testflight/evidence-synthesis",
            workflow_version=1,
            run_id="run:langgraph-agent-replay",
            inputs={
                "question": "What should Testflight validate for campaign decision intelligence?",
                "request_id": "request:langgraph-agent-test",
            },
        )
        server = create_mcp_server(service, principal)
        async with Client(server) as client:
            tools = await client.list_tools()
            workflow_tool = "testflight_run_workflow_testflight_evidence_synthesis_v1"
            assert workflow_tool in {tool.name for tool in tools.tools}
            agent_result = await client.call_tool(
                workflow_tool,
                {
                    "inputs": {
                        "question": (
                            "What should Testflight validate for campaign decision intelligence?"
                        ),
                        "request_id": "request:mcp-agent-test",
                    },
                    "run_id": "run:mcp-assigned-agent",
                },
            )
        return first, replay, agent_result

    record, replay, agent_result = asyncio.run(exercise())

    assert record.result is not None
    assert record.result.status is ResultStatus.SUCCESS
    assert list(record.result.step_results) == [
        "retrieve",
        "evaluate_records",
        "synthesize",
        "dispatch",
    ]
    proposal = record.result.outputs["proposal"]
    assert "research:commercial-viability" in proposal["evidence_refs"]
    assert proposal["canonical_write"] is False
    dispatch = record.result.outputs["dispatch"]
    assert dispatch["status"] == "dispatched_as_proposal"
    artifacts = list((tmp_path / "proposals").glob("*.json"))
    assert len(artifacts) == 1
    persisted = json.loads(artifacts[0].read_text(encoding="utf-8"))
    assert persisted["principal_id"] == principal.id
    assert persisted["proposal_id"] == dispatch["proposal_id"]

    receipts = {receipt.step_id: receipt for receipt in record.result.receipts}
    assert receipts["evaluate_records"].handler_receipt["item_count"] >= 1
    assert receipts["dispatch"].handler_receipt["action_id"].endswith("proposal/dispatch")
    assert replay.result is not None
    replay_receipts = {receipt.step_id: receipt for receipt in replay.result.receipts}
    assert replay_receipts["dispatch"].idempotent_replay is True
    assert not agent_result.is_error
    assert agent_result.structured_content is not None
    assert agent_result.structured_content["result"]["status"] == "success"
    assert {call["input"]["prompt_id"] for call in operator_client.calls} == {
        "prompt://testflight/research/evaluate-record",
        "prompt://testflight/research/synthesize-proposal",
    }
    assert all(call["context"]["disclosure_refs"] for call in operator_client.calls)
