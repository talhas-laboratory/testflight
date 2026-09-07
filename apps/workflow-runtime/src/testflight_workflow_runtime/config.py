"""Load non-secret workflow runtime configuration."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from testflight_workflows import HandlerRegistry, WorkflowCatalog, WorkflowPrincipal, load_workflow

from .auth import PrincipalDeclaration


@dataclass(frozen=True, slots=True)
class RuntimeConfiguration:
    workflow_registry: Path
    database_path: Path
    host: str
    port: int
    principals: tuple[PrincipalDeclaration, ...]
    mcp_principal_id: str | None
    handler_modules: tuple[str, ...]
    handler_configuration: dict[str, dict[str, Any]]


def load_runtime_configuration(path: Path) -> RuntimeConfiguration:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    root = path.parent.parent if path.parent.name == "workflows" else path.parent
    return RuntimeConfiguration(
        workflow_registry=(root / payload["workflow_registry"]).resolve(),
        database_path=(root / payload["database_path"]).resolve(),
        host=str(payload.get("host", "127.0.0.1")),
        port=int(payload.get("port", 8782)),
        principals=tuple(
            PrincipalDeclaration.from_mapping(item) for item in payload.get("principals", [])
        ),
        mcp_principal_id=payload.get("mcp_principal_id"),
        handler_modules=tuple(payload.get("handler_modules", [])),
        handler_configuration={
            str(name): dict(value)
            for name, value in payload.get("handler_configuration", {}).items()
        },
    )


def load_catalog(path: Path) -> WorkflowCatalog:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return WorkflowCatalog(
        [load_workflow(path.parent / item["path"]) for item in payload["definitions"]]
    )


def load_handlers(
    module_names: tuple[str, ...],
    module_configuration: dict[str, dict[str, Any]] | None = None,
) -> HandlerRegistry:
    registry = HandlerRegistry()
    configuration = module_configuration or {}
    for module_name in module_names:
        module = importlib.import_module(module_name)
        register = getattr(module, "register_workflow_handlers", None)
        if not callable(register):
            raise ValueError(
                f"handler module {module_name!r} must expose register_workflow_handlers"
            )
        register(registry, configuration.get(module_name, {}))
    return registry


def mcp_principal(configuration: RuntimeConfiguration) -> WorkflowPrincipal | None:
    if not configuration.mcp_principal_id:
        return None
    declaration = next(
        (item for item in configuration.principals if item.id == configuration.mcp_principal_id),
        None,
    )
    if declaration is None:
        raise ValueError("mcp_principal_id must reference a configured principal")
    return WorkflowPrincipal(id=declaration.id, roles=declaration.roles)


__all__ = [
    "RuntimeConfiguration",
    "load_catalog",
    "load_handlers",
    "load_runtime_configuration",
    "mcp_principal",
]
