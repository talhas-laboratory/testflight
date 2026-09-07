"""Capability-honest target adapters for Creative Field generation packets."""

from .connectors import (
    IMAGE_TARGET_MANIFEST,
    TEXT_TARGET_MANIFEST,
    ConnectorInvocationReceipt,
    ConnectorPreflightError,
    ConnectorResult,
    ImageTargetAdapter,
    NormalizedOutput,
    TextTargetAdapter,
    compile_generation_packet,
)
from .descriptor import descriptor, health_probe

__all__ = [
    "IMAGE_TARGET_MANIFEST",
    "TEXT_TARGET_MANIFEST",
    "ConnectorInvocationReceipt",
    "ConnectorPreflightError",
    "ConnectorResult",
    "ImageTargetAdapter",
    "NormalizedOutput",
    "TextTargetAdapter",
    "compile_generation_packet",
    "descriptor",
    "health_probe",
]
