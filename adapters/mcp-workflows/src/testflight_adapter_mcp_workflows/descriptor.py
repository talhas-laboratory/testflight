"""MCP workflow adapter descriptor and dependency-free health probe."""

from __future__ import annotations

from importlib.util import find_spec

from testflight_core import AdapterDescriptor, Capability, HealthReport, HealthState

descriptor = AdapterDescriptor(
    name="mcp-workflows",
    upstream="https://github.com/modelcontextprotocol/python-sdk",
    capabilities=frozenset({Capability.AGENT_RUNTIME}),
)


def health_probe() -> HealthReport:
    if find_spec("mcp") is None:
        return HealthReport(HealthState.UNAVAILABLE, "The pinned MCP SDK is not importable.")
    return HealthReport(HealthState.AVAILABLE, "The pinned MCP SDK is importable.")


__all__ = ["descriptor", "health_probe"]
