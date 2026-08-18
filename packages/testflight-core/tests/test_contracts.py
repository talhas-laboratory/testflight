from testflight_core import AdapterDescriptor, Capability


def test_descriptor_is_immutable() -> None:
    descriptor = AdapterDescriptor(
        name="example",
        upstream="https://example.invalid/repository",
        capabilities=frozenset({Capability.MEMORY}),
    )

    assert descriptor.name == "example"
    assert descriptor.capabilities == {Capability.MEMORY}
