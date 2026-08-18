"""Dependency-free contracts implemented by upstream adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class Capability(StrEnum):
    """Broad roles an upstream can provide without prescribing its API."""

    AGENT_RUNTIME = "agent-runtime"
    MEMORY = "memory"
    ORCHESTRATION = "orchestration"


class HealthState(StrEnum):
    """Availability state of an integration in the current environment."""

    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class AdapterDescriptor:
    """Stable metadata exposed by every adapter."""

    name: str
    upstream: str
    capabilities: frozenset[Capability]
    adapter_version: str = "0.1.0"


@dataclass(frozen=True, slots=True)
class HealthReport:
    """Machine-readable probe result that never requires secret values."""

    state: HealthState
    message: str
    details: dict[str, str] = field(default_factory=dict)


class Adapter(Protocol):
    """Minimum lifecycle-independent boundary for an upstream integration."""

    descriptor: AdapterDescriptor

    def health(self) -> HealthReport:
        """Report whether the upstream dependency is usable in this environment."""
        ...
