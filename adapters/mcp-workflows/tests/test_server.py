from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from mcp import Client
from starlette.testclient import TestClient
from testflight_adapter_mcp_workflows import (
    create_http_app,
    create_mcp_server,
    descriptor,
    health_probe,
)
from testflight_core import Capability, HealthState
from testflight_workflows import (
    ResultStatus,
    RunPhase,
    WorkflowPrincipal,
    WorkflowRunRecord,
    WorkflowRunResult,
)


class Service:
    def discover(self, _principal):
        return (
            {
                "id": "workflow://example/summarize",
                "version": 1,
                "name": "Summarize evidence",
                "description": "Summarize authorized evidence.",
                "tags": ["summary"],
                "input_schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["question"],
                    "properties": {"question": {"type": "string"}},
                },
                "output_schema": {"type": "object"},
                "side_effects": {
                    "proposal_write": False,
                    "canonical_write": False,
                    "external_action": False,
                },
            },
        )

    async def run_and_wait(self, *, principal, workflow_id, workflow_version, run_id, inputs):
        now = datetime.now(UTC)
        return WorkflowRunRecord(
            run_id=run_id,
            workflow_id=workflow_id,
            workflow_version=workflow_version,
            principal_id=principal.id,
            inputs=inputs,
            phase=RunPhase.COMPLETED,
            created_at=now,
            updated_at=now,
            result=WorkflowRunResult(
                run_id=run_id,
                workflow_id=workflow_id,
                workflow_version=workflow_version,
                principal_id=principal.id,
                grant_id=f"grant:{run_id}",
                status=ResultStatus.SUCCESS,
                outputs={"summary": inputs["question"]},
            ),
        )

    async def get_run(self, _principal, _run_id):
        return None


class Authenticator:
    def authenticate(self, authorization):
        return WorkflowPrincipal(id="agent:test") if authorization == "Bearer valid" else None


def test_mcp_exposes_discovery_and_typed_workflow_tool():
    async def exercise():
        server = create_mcp_server(Service(), WorkflowPrincipal(id="agent:test"))
        async with Client(server) as client:
            tools = await client.list_tools()
            names = {tool.name for tool in tools.tools}
            assert "testflight_list_workflows" in names
            workflow_tool = "testflight_run_workflow_example_summarize_v1"
            assert workflow_tool in names
            tool = next(item for item in tools.tools if item.name == workflow_tool)
            assert set(tool.input_schema["properties"]) == {"inputs", "run_id"}
            result = await client.call_tool(
                workflow_tool,
                {"inputs": {"question": "What changed?"}, "run_id": "run:mcp"},
            )
            assert not result.is_error, result.content
            assert result.structured_content is not None, result.content
            assert result.structured_content["result"]["outputs"]["summary"] == "What changed?"

    asyncio.run(exercise())


def test_adapter_descriptor_and_health_probe():
    assert descriptor.capabilities == {Capability.AGENT_RUNTIME}
    assert health_probe().state is HealthState.AVAILABLE


def test_http_api_authenticates_and_paginates_discovery():
    app = create_http_app(Service(), Authenticator())
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/v1/workflows").status_code == 401
        response = client.get(
            "/v1/workflows?limit=1&offset=0", headers={"Authorization": "Bearer valid"}
        )
        assert response.status_code == 200
        assert response.json()["items"][0]["id"] == "workflow://example/summarize"


def test_mcp_http_mount_requires_selected_principal_bearer_token():
    selected = WorkflowPrincipal(id="agent:test")
    app = create_http_app(Service(), Authenticator(), mcp_principal=selected)
    with TestClient(app) as client:
        assert client.post("/mcp/").status_code == 401
