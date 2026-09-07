"""Workflow Runtime command-line composition root."""

from __future__ import annotations

import argparse
from pathlib import Path

from testflight_adapter_langgraph import LangGraphWorkflowEngine
from testflight_adapter_mcp_workflows import create_http_app, serve_http_app
from testflight_adapter_sqlite_workflow_runtime import SqliteWorkflowRuntimeStore

from .auth import EnvironmentTokenAuthenticator
from .config import load_catalog, load_handlers, load_runtime_configuration, mcp_principal
from .service import WorkflowRuntimeService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("workflows/runtime.example.yaml"))
    args = parser.parse_args(argv)
    configuration = load_runtime_configuration(args.config.resolve())
    catalog = load_catalog(configuration.workflow_registry)
    handlers = load_handlers(
        configuration.handler_modules,
        configuration.handler_configuration,
    )
    store = SqliteWorkflowRuntimeStore(configuration.database_path)
    engine = LangGraphWorkflowEngine(catalog=catalog, handlers=handlers, idempotency=store)
    service = WorkflowRuntimeService(catalog=catalog, engine=engine, run_store=store)
    authenticator = EnvironmentTokenAuthenticator.from_declarations(configuration.principals)
    app = create_http_app(service, authenticator, mcp_principal=mcp_principal(configuration))
    serve_http_app(app, host=configuration.host, port=configuration.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
