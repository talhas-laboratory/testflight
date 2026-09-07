"""MCP and REST projections over the provider-neutral workflow service."""

from __future__ import annotations

import re
from collections.abc import Mapping
from contextlib import asynccontextmanager
from typing import Any, Protocol

import uvicorn
from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field, create_model
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from testflight_workflows import WorkflowPrincipal, WorkflowRunRecord


class WorkflowService(Protocol):
    def discover(self, principal: WorkflowPrincipal) -> tuple[dict[str, Any], ...]: ...

    async def start_run(
        self,
        *,
        principal: WorkflowPrincipal,
        workflow_id: str,
        workflow_version: int,
        run_id: str,
        inputs: Mapping[str, Any],
    ) -> WorkflowRunRecord: ...

    async def run_and_wait(
        self,
        *,
        principal: WorkflowPrincipal,
        workflow_id: str,
        workflow_version: int,
        run_id: str,
        inputs: Mapping[str, Any],
    ) -> WorkflowRunRecord: ...

    async def get_run(
        self, principal: WorkflowPrincipal, run_id: str
    ) -> WorkflowRunRecord | None: ...


class RequestAuthenticator(Protocol):
    def authenticate(self, authorization: str | None) -> WorkflowPrincipal | None: ...


class WorkflowInvocation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workflow_id: str = Field(min_length=1)
    workflow_version: int = Field(ge=1)
    run_id: str = Field(min_length=1, max_length=200)
    inputs: dict[str, Any]


class _AuthenticatedMcpApp:
    def __init__(self, app, authenticator: RequestAuthenticator, principal: WorkflowPrincipal):
        self.app = app
        self.authenticator = authenticator
        self.principal = principal

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = {
                key.decode("latin-1").lower(): value.decode("latin-1")
                for key, value in scope.get("headers", [])
            }
            actor = self.authenticator.authenticate(headers.get("authorization"))
            if actor is None or actor.id != self.principal.id:
                await JSONResponse({"error": "authentication required for MCP"}, status_code=401)(
                    scope, receive, send
                )
                return
        await self.app(scope, receive, send)


def _tool_name(workflow_id: str, version: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", workflow_id.lower()).strip("_")
    return f"testflight_run_{slug}_v{version}"[:128]


def _python_type(schema: Mapping[str, Any]) -> Any:
    return {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list[Any],
        "object": dict[str, Any],
    }.get(schema.get("type"), Any)


def _input_model(name: str, schema: Mapping[str, Any]) -> type[BaseModel]:
    required = set(schema.get("required", []))
    fields: dict[str, tuple[Any, Any]] = {}
    for field_name, field_schema in schema.get("properties", {}).items():
        python_type = _python_type(field_schema)
        default = ... if field_name in required else field_schema.get("default", None)
        fields[field_name] = (
            python_type,
            Field(default=default, description=field_schema.get("description")),
        )
    model = create_model(name, __config__=ConfigDict(extra="forbid"), **fields)
    return model


def create_mcp_server(service: WorkflowService, principal: WorkflowPrincipal) -> MCPServer:
    """Create one MCP view already filtered to an authenticated agent identity."""

    mcp = MCPServer("testflight_workflows_mcp")

    @mcp.tool(
        name="testflight_list_workflows",
        title="List authorized Testflight workflows",
        annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False),
    )
    def list_workflows(limit: int = 20, offset: int = 0) -> dict[str, Any]:
        """List workflows this agent may invoke, including schemas and side-effect declarations."""
        bounded_limit = min(max(limit, 1), 100)
        bounded_offset = max(offset, 0)
        items = service.discover(principal)
        page = items[bounded_offset : bounded_offset + bounded_limit]
        next_offset = bounded_offset + len(page)
        return {
            "total": len(items),
            "count": len(page),
            "offset": bounded_offset,
            "items": list(page),
            "has_more": next_offset < len(items),
            "next_offset": next_offset if next_offset < len(items) else None,
        }

    @mcp.tool(
        name="testflight_get_workflow_run",
        title="Get a Testflight workflow run",
        annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False),
    )
    async def get_workflow_run(run_id: str) -> dict[str, Any]:
        """Read one workflow run owned by this agent; unknown or foreign runs are not revealed."""
        record = await service.get_run(principal, run_id)
        if record is None:
            return {"status": "not_found", "message": "Run not found for this agent."}
        return record.model_dump(mode="json")

    for descriptor in service.discover(principal):
        input_model = _input_model(
            f"WorkflowInputs{descriptor['version']}", descriptor["input_schema"]
        )
        side_effects = descriptor["side_effects"]

        def make_invoke(selected):
            async def run_selected(inputs, run_id: str):
                record = await service.run_and_wait(
                    principal=principal,
                    workflow_id=selected["id"],
                    workflow_version=selected["version"],
                    run_id=run_id,
                    inputs=inputs.model_dump(mode="json"),
                )
                return record

            return run_selected

        invoke = make_invoke(descriptor)

        invoke.__name__ = _tool_name(descriptor["id"], descriptor["version"])
        invoke.__doc__ = descriptor["description"]
        invoke.__annotations__["inputs"] = input_model
        invoke.__annotations__["return"] = WorkflowRunRecord
        mcp.tool(
            name=invoke.__name__,
            title=descriptor["name"],
            description=descriptor["description"],
            annotations=ToolAnnotations(
                read_only_hint=not any(side_effects.values()),
                destructive_hint=bool(side_effects["canonical_write"]),
                idempotent_hint=True,
                open_world_hint=bool(side_effects["external_action"]),
            ),
        )(invoke)
    return mcp


def create_http_app(
    service: WorkflowService,
    authenticator: RequestAuthenticator,
    *,
    mcp_principal: WorkflowPrincipal | None = None,
    max_body_bytes: int = 1024 * 1024,
) -> Starlette:
    """Create REST endpoints and an optional localhost MCP mount."""

    def principal(request: Request) -> WorkflowPrincipal | None:
        return authenticator.authenticate(request.headers.get("authorization"))

    async def health(_request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    async def list_workflows(request: Request) -> JSONResponse:
        actor = principal(request)
        if actor is None:
            return JSONResponse({"error": "authentication required"}, status_code=401)
        try:
            limit = min(max(int(request.query_params.get("limit", "20")), 1), 100)
            offset = max(int(request.query_params.get("offset", "0")), 0)
        except ValueError:
            return JSONResponse({"error": "limit and offset must be integers"}, status_code=400)
        items = service.discover(actor)
        page = items[offset : offset + limit]
        next_offset = offset + len(page)
        return JSONResponse(
            {
                "total": len(items),
                "count": len(page),
                "offset": offset,
                "items": list(page),
                "has_more": next_offset < len(items),
                "next_offset": next_offset if next_offset < len(items) else None,
            }
        )

    async def start_run(request: Request) -> JSONResponse:
        actor = principal(request)
        if actor is None:
            return JSONResponse({"error": "authentication required"}, status_code=401)
        body = await request.body()
        if len(body) > max_body_bytes:
            return JSONResponse({"error": "request body exceeds size limit"}, status_code=413)
        try:
            invocation = WorkflowInvocation.model_validate_json(body)
            record = await service.start_run(principal=actor, **invocation.model_dump())
        except ValueError as error:
            return JSONResponse({"error": str(error)}, status_code=400)
        return JSONResponse(record.model_dump(mode="json"), status_code=202)

    async def get_run(request: Request) -> JSONResponse:
        actor = principal(request)
        if actor is None:
            return JSONResponse({"error": "authentication required"}, status_code=401)
        record = await service.get_run(actor, request.path_params["run_id"])
        if record is None:
            return JSONResponse({"error": "run not found"}, status_code=404)
        return JSONResponse(record.model_dump(mode="json"))

    routes = [
        Route("/health", health),
        Route("/v1/workflows", list_workflows),
        Route("/v1/runs", start_run, methods=["POST"]),
        Route("/v1/runs/{run_id}", get_run),
    ]
    mcp = create_mcp_server(service, mcp_principal) if mcp_principal else None
    if mcp:
        mcp_app = mcp.streamable_http_app(streamable_http_path="/")
        routes.append(
            Mount("/mcp", app=_AuthenticatedMcpApp(mcp_app, authenticator, mcp_principal))
        )

    @asynccontextmanager
    async def lifespan(_app: Starlette):
        if mcp:
            async with mcp.session_manager.run():
                yield
        else:
            yield

    return Starlette(routes=routes, lifespan=lifespan)


def serve_http_app(app: Starlette, *, host: str = "127.0.0.1", port: int = 8782) -> None:
    """Serve the combined API; localhost is the safe default."""
    uvicorn.run(app, host=host, port=port)


__all__ = [
    "RequestAuthenticator",
    "WorkflowInvocation",
    "WorkflowService",
    "create_http_app",
    "create_mcp_server",
    "serve_http_app",
]
