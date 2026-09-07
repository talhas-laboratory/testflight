"""Task-specific Creative Field projection and context-packet composition."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .models import (
    ArtifactStatus,
    CreativeContextPacket,
    CreativeFieldVersion,
    CreativeRequest,
    FieldBinding,
    FieldProjection,
    ResolvedCreativeRequest,
    TargetCapabilityManifest,
)


@dataclass(frozen=True, slots=True)
class ProjectionCompilationResult:
    status: ArtifactStatus
    resolved_request: ResolvedCreativeRequest | None = None
    projection: FieldProjection | None = None
    packet: CreativeContextPacket | None = None
    omissions: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    hold_reason: str | None = None
    receipt: Mapping[str, Any] = field(default_factory=dict)


class CreativeContextCompiler:
    """Compile a bound field and the existing world-view result without semantic fallback."""

    def resolve_request(
        self,
        *,
        request: CreativeRequest,
        project_binding_id: str,
        field_binding: FieldBinding,
        field_version: CreativeFieldVersion,
        world_view_request_id: str,
        target_capability_manifest_id: str,
        lens: str,
    ) -> ProjectionCompilationResult:
        if request.project_id != field_binding.project_id:
            return ProjectionCompilationResult(
                status=ArtifactStatus.HELD,
                errors=("creative request project does not match field binding",),
                hold_reason="project_mismatch",
            )
        if field_version.version_id != field_binding.field_version_id:
            return ProjectionCompilationResult(
                status=ArtifactStatus.HELD,
                errors=("field binding and version do not match",),
                hold_reason="version_mismatch",
            )
        if not lens.strip():
            return ProjectionCompilationResult(
                status=ArtifactStatus.HELD,
                errors=("projection lens is required",),
                hold_reason="lens_missing",
            )
        resolved = ResolvedCreativeRequest(
            request_id=request.request_id,
            project_binding_id=project_binding_id,
            field_binding_id=field_binding.binding_id,
            field_version_id=field_version.version_id,
            world_view_request_id=world_view_request_id,
            lens=lens,
            target_capability_manifest_id=target_capability_manifest_id,
            local_override_id=request.local_override_id,
            ambiguity_disposition="resolved",
            permission_context=request.permission_context,
            derivation_id=f"request-resolution:{request.request_id}",
        )
        return ProjectionCompilationResult(
            status=ArtifactStatus.SUCCESS,
            resolved_request=resolved,
            receipt={
                "request_id": request.request_id,
                "project_binding_id": project_binding_id,
                "field_version_id": field_version.version_id,
            },
        )

    def compile(
        self,
        *,
        resolved_request: ResolvedCreativeRequest,
        request: CreativeRequest,
        field_version: CreativeFieldVersion,
        field_binding: FieldBinding,
        world_view: Mapping[str, Any],
        target_manifest: TargetCapabilityManifest,
        disclosure_manifest_id: str,
        visual_language_revision_ids: Sequence[str] = (),
    ) -> ProjectionCompilationResult:
        if resolved_request.field_version_id != field_version.version_id:
            return ProjectionCompilationResult(
                status=ArtifactStatus.HELD,
                errors=("resolved request references a different field version",),
                hold_reason="version_mismatch",
            )
        if request.modality not in target_manifest.accepted_modalities:
            return ProjectionCompilationResult(
                status=ArtifactStatus.UNAVAILABLE,
                errors=(f"target does not accept modality {request.modality}",),
                hold_reason="modality_unsupported",
            )
        view_id = world_view.get("view_id", world_view.get("viewId"))
        if not isinstance(view_id, str) or not view_id.strip():
            return ProjectionCompilationResult(
                status=ArtifactStatus.HELD,
                errors=("world-view result has no stable view id",),
                hold_reason="world_view_missing",
            )
        view_status = str(world_view.get("status", "hit")).lower()
        if view_status in {"no_hit", "hold"}:
            return ProjectionCompilationResult(
                status=ArtifactStatus.HELD,
                errors=(f"world-view resolver returned {view_status}",),
                hold_reason="world_view_unavailable",
            )
        unsupported = {
            item
            for item in target_manifest.controls.get("unsupported_dimension_ids", [])
            if isinstance(item, str)
        }
        dimension_mappings: dict[str, Any] = {}
        omissions: list[str] = []
        for state in field_version.dimension_states:
            if state.dimension_id in unsupported:
                omissions.append(f"target does not expose dimension: {state.dimension_id}")
                continue
            dimension_mappings[state.dimension_id] = {
                "summary": state.summary,
                "values": state.values,
                "source_contribution_ids": list(state.source_contribution_ids),
            }
        omissions.extend(item.dimension_id for item in field_version.missing_dimensions)
        omissions.extend(item for item in world_view.get("omissions", []) if isinstance(item, str))
        conflicts = [item.conflict_id for item in field_version.conflicts]
        conflicts.extend(
            item
            for item in world_view.get(
                "unresolved_conflict_ids", world_view.get("unresolvedConflictIds", [])
            )
            if isinstance(item, str)
        )
        selected_world_records = tuple(
            item
            for item in world_view.get(
                "selected_record_ids", world_view.get("selectedRecordIds", [])
            )
            if isinstance(item, str)
        )
        grounding = tuple(
            dict.fromkeys([*field_version.source_contribution_ids, *selected_world_records])
        )
        projection_status = (
            ArtifactStatus.PARTIAL if omissions or conflicts else ArtifactStatus.SUCCESS
        )
        projection = FieldProjection(
            projection_id=f"projection:{request.request_id}:{field_version.version_id}",
            field_version_id=field_version.version_id,
            request_id=request.request_id,
            lens=resolved_request.lens,
            modality=request.modality,
            principles=tuple(item.statement for item in field_version.principles),
            tensions=tuple(item.statement for item in field_version.tensions),
            exclusions=tuple(item.statement for item in field_version.exclusions),
            dimension_mappings=dimension_mappings,
            grounding_reference_ids=grounding,
            assumptions=tuple(
                item for item in world_view.get("assumptions", []) if isinstance(item, str)
            ),
            omissions=tuple(dict.fromkeys(omissions)),
            sufficiency="partial" if projection_status is ArtifactStatus.PARTIAL else "sufficient",
            derivation_id=f"projection:{request.request_id}",
            status=projection_status,
        )
        if not disclosure_manifest_id.strip():
            return ProjectionCompilationResult(
                status=ArtifactStatus.HELD,
                errors=("disclosure manifest is required",),
                hold_reason="disclosure_missing",
            )
        citations = tuple(item for item in world_view.get("citations", []) if isinstance(item, str))
        packet_status = (
            ArtifactStatus.PARTIAL
            if projection_status is ArtifactStatus.PARTIAL
            or world_view.get("status") in {"partial", "PARTIAL"}
            else ArtifactStatus.SUCCESS
        )
        packet = CreativeContextPacket(
            packet_id=f"creative-context:{request.request_id}",
            request_id=request.request_id,
            resolved_world_view_id=view_id,
            field_projection_id=projection.projection_id,
            visual_language_revision_ids=tuple(visual_language_revision_ids),
            selected_record_ids=tuple(dict.fromkeys((*grounding, *selected_world_records))),
            conflicts=tuple(dict.fromkeys(conflicts)),
            omissions=projection.omissions,
            citations=citations,
            disclosure_manifest_id=disclosure_manifest_id,
            derivation_id=f"packet:{request.request_id}",
            status=packet_status,
        )
        return ProjectionCompilationResult(
            status=packet_status,
            resolved_request=resolved_request,
            projection=projection,
            packet=packet,
            omissions=projection.omissions,
            conflicts=packet.conflicts,
            receipt={
                "request_id": request.request_id,
                "field_binding_id": field_binding.binding_id,
                "field_version_id": field_version.version_id,
                "world_view_id": view_id,
                "target_id": target_manifest.target_id,
            },
        )


__all__ = ["CreativeContextCompiler", "ProjectionCompilationResult"]
