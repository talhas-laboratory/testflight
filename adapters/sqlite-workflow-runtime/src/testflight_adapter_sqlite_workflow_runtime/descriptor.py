"""SQLite workflow runtime adapter descriptor."""

from testflight_core import AdapterDescriptor, Capability, HealthReport, HealthState

descriptor = AdapterDescriptor(
    name="sqlite-workflow-runtime",
    upstream="python-stdlib://sqlite3",
    capabilities=frozenset({Capability.MEMORY}),
)


def health_probe() -> HealthReport:
    return HealthReport(HealthState.AVAILABLE, "Python SQLite support is available.")


__all__ = ["descriptor", "health_probe"]
