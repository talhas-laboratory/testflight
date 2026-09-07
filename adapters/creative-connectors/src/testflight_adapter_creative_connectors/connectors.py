"""Provider-neutral text and image target connectors."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from testflight_creative_field import (
    ArtifactStatus,
    FieldProjection,
    GenerationPacket,
    TargetCapabilityManifest,
)


class ConnectorPreflightError(ValueError):
    """Raised when a packet cannot be safely sent to a target."""


@dataclass(frozen=True, slots=True)
class NormalizedOutput:
    output_id: str
    media_type: str
    content: str | bytes
    adapter_version: str
    packet_id: str


@dataclass(frozen=True, slots=True)
class ConnectorInvocationReceipt:
    invocation_id: str
    packet_id: str
    target_id: str
    adapter_version: str
    disclosure_manifest_id: str
    grounding_assets_sent: tuple[str, ...]
    capability_limitations: tuple[str, ...]
    status: ArtifactStatus
    errors: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ConnectorResult:
    status: ArtifactStatus
    output: NormalizedOutput | None
    receipt: ConnectorInvocationReceipt


class TargetTransport(Protocol):
    def __call__(self, packet: GenerationPacket) -> str | bytes: ...


TEXT_TARGET_MANIFEST = TargetCapabilityManifest(
    target_id="target:text:local",
    adapter_version="1",
    accepted_modalities=("text",),
    controls={
        "supported_control_ids": ("principles", "tensions", "exclusions", "dimensions"),
    },
    privacy_policy_id="policy:connector-local",
)

IMAGE_TARGET_MANIFEST = TargetCapabilityManifest(
    target_id="target:image:local",
    adapter_version="1",
    accepted_modalities=("image",),
    controls={
        "supported_control_ids": ("principles", "tensions", "exclusions", "dimensions"),
    },
    privacy_policy_id="policy:connector-local",
)


def _supported_controls(manifest: TargetCapabilityManifest) -> set[str]:
    value = manifest.controls.get("supported_control_ids", ())
    return (
        {item for item in value if isinstance(item, str)}
        if isinstance(value, (list, tuple))
        else set()
    )


def compile_generation_packet(
    projection: FieldProjection,
    manifest: TargetCapabilityManifest,
    *,
    disclosure_manifest_id: str,
    grounding_asset_ids: Sequence[str] = (),
    permitted_asset_ids: Sequence[str] = (),
) -> GenerationPacket:
    """Translate a target-neutral projection and enforce asset/disclosure preflight."""

    if projection.modality not in manifest.accepted_modalities:
        raise ConnectorPreflightError(
            f"target {manifest.target_id} does not accept {projection.modality}"
        )
    if not disclosure_manifest_id.strip():
        raise ConnectorPreflightError("disclosure manifest is required")
    grounding = tuple(dict.fromkeys(grounding_asset_ids))
    permitted = set(permitted_asset_ids)
    blocked = tuple(sorted(set(grounding) - permitted))
    if blocked:
        raise ConnectorPreflightError(
            f"grounding assets are not permitted for target: {', '.join(blocked)}"
        )
    supported = _supported_controls(manifest)
    requested: dict[str, Any] = {
        "principles": list(projection.principles),
        "tensions": list(projection.tensions),
        "exclusions": list(projection.exclusions),
        "dimensions": projection.dimension_mappings,
    }
    controls_sent = {key: value for key, value in requested.items() if key in supported}
    limitations = tuple(
        f"target does not support control: {key}" for key in requested if key not in supported
    )
    return GenerationPacket(
        packet_id=f"generation:{projection.projection_id}:{manifest.target_id}",
        projection_id=projection.projection_id,
        target_capability_manifest_id=manifest.target_id,
        controls_sent=controls_sent,
        grounding_assets_sent=grounding,
        capability_limitations=limitations,
        disclosure_manifest_id=disclosure_manifest_id,
        expected_output={"modality": projection.modality},
        adapter_version=manifest.adapter_version,
        derivation_id=f"generation-packet:{projection.projection_id}",
    )


class _BaseTargetAdapter:
    def __init__(self, manifest: TargetCapabilityManifest, transport: TargetTransport) -> None:
        self.manifest = manifest
        self._transport = transport

    def invoke(self, packet: GenerationPacket, *, invocation_id: str) -> ConnectorResult:
        if packet.target_capability_manifest_id != self.manifest.target_id:
            raise ConnectorPreflightError("generation packet target does not match adapter")
        if packet.adapter_version != self.manifest.adapter_version:
            raise ConnectorPreflightError("generation packet adapter version is stale")
        try:
            content = self._transport(packet)
        except Exception as error:  # noqa: BLE001 - adapter boundary normalizes provider failures.
            receipt = ConnectorInvocationReceipt(
                invocation_id=invocation_id,
                packet_id=packet.packet_id,
                target_id=self.manifest.target_id,
                adapter_version=self.manifest.adapter_version,
                disclosure_manifest_id=packet.disclosure_manifest_id,
                grounding_assets_sent=packet.grounding_assets_sent,
                capability_limitations=packet.capability_limitations,
                status=ArtifactStatus.FAILED,
                errors=(str(error),),
            )
            return ConnectorResult(status=ArtifactStatus.FAILED, output=None, receipt=receipt)
        output = self._normalize(content, packet)
        receipt = ConnectorInvocationReceipt(
            invocation_id=invocation_id,
            packet_id=packet.packet_id,
            target_id=self.manifest.target_id,
            adapter_version=self.manifest.adapter_version,
            disclosure_manifest_id=packet.disclosure_manifest_id,
            grounding_assets_sent=packet.grounding_assets_sent,
            capability_limitations=packet.capability_limitations,
            status=ArtifactStatus.PARTIAL
            if packet.capability_limitations
            else ArtifactStatus.SUCCESS,
        )
        status = receipt.status
        return ConnectorResult(status=status, output=output, receipt=receipt)

    def _normalize(self, content: str | bytes, packet: GenerationPacket) -> NormalizedOutput:
        raise NotImplementedError


class TextTargetAdapter(_BaseTargetAdapter):
    def __init__(self, transport: TargetTransport) -> None:
        super().__init__(TEXT_TARGET_MANIFEST, transport)

    def _normalize(self, content: str | bytes, packet: GenerationPacket) -> NormalizedOutput:
        if not isinstance(content, str):
            raise ConnectorPreflightError("text target returned non-text output")
        return NormalizedOutput(
            output_id=f"output:{packet.packet_id}",
            media_type="text/plain",
            content=content,
            adapter_version=self.manifest.adapter_version,
            packet_id=packet.packet_id,
        )


class ImageTargetAdapter(_BaseTargetAdapter):
    def __init__(self, transport: TargetTransport) -> None:
        super().__init__(IMAGE_TARGET_MANIFEST, transport)

    def _normalize(self, content: str | bytes, packet: GenerationPacket) -> NormalizedOutput:
        if not isinstance(content, bytes):
            raise ConnectorPreflightError("image target returned non-binary output")
        return NormalizedOutput(
            output_id=f"output:{packet.packet_id}",
            media_type="image/png",
            content=content,
            adapter_version=self.manifest.adapter_version,
            packet_id=packet.packet_id,
        )


__all__ = [
    "ConnectorInvocationReceipt",
    "ConnectorPreflightError",
    "ConnectorResult",
    "IMAGE_TARGET_MANIFEST",
    "ImageTargetAdapter",
    "NormalizedOutput",
    "TEXT_TARGET_MANIFEST",
    "TextTargetAdapter",
    "compile_generation_packet",
]
