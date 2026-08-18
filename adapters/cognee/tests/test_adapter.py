from testflight_adapter_cognee import CogneeAdapter
from testflight_core import Capability, HealthState


def test_descriptor_and_dependency_free_probe() -> None:
    adapter = CogneeAdapter()

    assert adapter.descriptor.capabilities == {Capability.MEMORY}
    assert adapter.health().state in {HealthState.AVAILABLE, HealthState.UNAVAILABLE}
