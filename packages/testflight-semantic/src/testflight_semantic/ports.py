"""Small provider and persistence ports for workflow composition."""

from collections.abc import Awaitable, Callable, Iterable
from enum import StrEnum
from typing import Any, Protocol

from .models import ExtractionResult


class SemanticStatus(StrEnum):
    ACCEPTED = "accepted"
    PARTIAL = "partial"
    HELD = "held"
    REJECTED = "rejected"
    UNAVAILABLE = "unavailable"
    NO_HIT = "no_hit"


class StructuredExtractionProvider(Protocol):
    async def extract(
        self, text: str, system_prompt: str, response_model: type[ExtractionResult]
    ) -> ExtractionResult | dict[str, Any]:
        """Return structured output without committing semantic state."""
        ...


class EvidenceRepository(Protocol):
    def put_envelope(self, envelope: Any, content: str) -> None:
        """Store immutable source metadata and content."""
        ...


class AssertionRepository(Protocol):
    def append(self, records: Iterable[Any]) -> None:
        """Append accepted semantic records atomically."""
        ...


ProjectionCallable = Callable[[str], Awaitable[dict[str, Any]]]


__all__ = [
    "AssertionRepository",
    "EvidenceRepository",
    "ProjectionCallable",
    "SemanticStatus",
    "StructuredExtractionProvider",
]
