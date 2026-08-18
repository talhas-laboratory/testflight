"""Stable contracts shared by Testflight integrations."""

from .adapter import Adapter, AdapterDescriptor, Capability, HealthReport, HealthState

__all__ = [
    "Adapter",
    "AdapterDescriptor",
    "Capability",
    "HealthReport",
    "HealthState",
]
