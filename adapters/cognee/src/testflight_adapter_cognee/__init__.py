"""Cognee adapter with lazy upstream loading."""

from importlib.util import find_spec

from testflight_core import AdapterDescriptor, Capability, HealthReport, HealthState


class CogneeAdapter:
    """Owns all Cognee-specific behavior exposed to Testflight."""

    descriptor = AdapterDescriptor(
        name="cognee",
        upstream="https://github.com/topoteretes/cognee",
        capabilities=frozenset({Capability.MEMORY}),
    )

    def health(self) -> HealthReport:
        if find_spec("cognee") is None:
            return HealthReport(
                HealthState.UNAVAILABLE,
                "Cognee is not installed; enable the adapter's 'cognee' extra.",
            )
        return HealthReport(HealthState.AVAILABLE, "Cognee is importable.")


__all__ = ["CogneeAdapter"]
