from testflight_adapter_langgraph import LangGraphAdapter
from testflight_core import Capability, HealthState


def test_descriptor_and_dependency_free_probe() -> None:
    adapter = LangGraphAdapter()

    assert adapter.descriptor.capabilities == {Capability.ORCHESTRATION}
    assert adapter.health().state in {HealthState.AVAILABLE, HealthState.UNAVAILABLE}
