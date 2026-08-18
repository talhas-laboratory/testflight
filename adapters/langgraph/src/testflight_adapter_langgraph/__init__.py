"""LangGraph adapter with lazy upstream loading."""

from importlib.util import find_spec

from testflight_core import AdapterDescriptor, Capability, HealthReport, HealthState


class LangGraphAdapter:
    """Owns all LangGraph-specific behavior exposed to Testflight."""

    descriptor = AdapterDescriptor(
        name="langgraph",
        upstream="https://github.com/langchain-ai/langgraph",
        capabilities=frozenset({Capability.ORCHESTRATION}),
    )

    def health(self) -> HealthReport:
        if find_spec("langgraph") is None:
            return HealthReport(
                HealthState.UNAVAILABLE,
                "LangGraph is not installed; enable the adapter's 'langgraph' extra.",
            )
        return HealthReport(HealthState.AVAILABLE, "LangGraph is importable.")


__all__ = ["LangGraphAdapter"]
