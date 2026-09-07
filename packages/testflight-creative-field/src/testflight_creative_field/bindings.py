"""Deterministic project and Brand-world binding resolution."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from testflight_semantic import RelationshipFrame, RoleBinding

from .models import (
    ArtifactStatus,
    CreativeFieldVersion,
    FieldBinding,
    LifecycleStatus,
    ProjectBinding,
)


@dataclass(frozen=True, slots=True)
class BindingResolution:
    status: ArtifactStatus
    project_binding: ProjectBinding | None = None
    field_binding: FieldBinding | None = None
    relationship_frame: RelationshipFrame | None = None
    conflicts: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    hold_reason: str | None = None
    receipt: Mapping[str, Any] = field(default_factory=dict)


def _parse_time(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _entity_scope(entity: Mapping[str, Any]) -> tuple[str | None, str | None]:
    entity_id = entity.get("entity_id", entity.get("id"))
    workspace_id = entity.get("workspace_id")
    return (
        entity_id if isinstance(entity_id, str) and entity_id.strip() else None,
        workspace_id if isinstance(workspace_id, str) and workspace_id.strip() else None,
    )


class CreativeBindingResolver:
    """Resolve creative bindings against canonical entity identity and explicit scope."""

    def resolve_project(
        self,
        binding: ProjectBinding,
        *,
        entities: Sequence[Mapping[str, Any]],
    ) -> BindingResolution:
        entity_map = {
            entity_id: entity for entity in entities if (entity_id := _entity_scope(entity)[0])
        }
        missing = sorted(set(binding.target_entity_ids) - set(entity_map))
        if missing:
            return BindingResolution(
                status=ArtifactStatus.HELD,
                errors=(f"unknown target entity ids: {', '.join(missing)}",),
                conflicts=tuple(missing),
                hold_reason="entity_unknown",
                receipt={"binding_id": binding.binding_id, "project_id": binding.project_id},
            )
        missing_workspace = sorted(
            entity_id
            for entity_id in binding.target_entity_ids
            if _entity_scope(entity_map[entity_id])[1] is None
        )
        if missing_workspace:
            return BindingResolution(
                status=ArtifactStatus.HELD,
                errors=(f"target entities lack workspace scope: {', '.join(missing_workspace)}",),
                conflicts=tuple(missing_workspace),
                hold_reason="workspace_missing",
                receipt={"binding_id": binding.binding_id, "project_id": binding.project_id},
            )
        foreign = sorted(
            entity_id
            for entity_id in binding.target_entity_ids
            if entity_map[entity_id]["workspace_id"] != binding.workspace_id
        )
        if foreign:
            return BindingResolution(
                status=ArtifactStatus.HELD,
                errors=(f"target entities cross workspace boundary: {', '.join(foreign)}",),
                conflicts=tuple(foreign),
                hold_reason="workspace_mismatch",
                receipt={"binding_id": binding.binding_id, "project_id": binding.project_id},
            )
        return BindingResolution(
            status=ArtifactStatus.SUCCESS,
            project_binding=binding,
            receipt={
                "binding_id": binding.binding_id,
                "project_id": binding.project_id,
                "workspace_id": binding.workspace_id,
                "target_entity_ids": list(binding.target_entity_ids),
            },
        )

    def resolve_field(
        self,
        *,
        project_binding: ProjectBinding,
        field_binding: FieldBinding,
        field_version: CreativeFieldVersion,
        entities: Sequence[Mapping[str, Any]],
        artifact_type: str | None = None,
        channel: str | None = None,
        at_time: str | None = None,
        existing_bindings: Iterable[FieldBinding] = (),
    ) -> BindingResolution:
        project_result = self.resolve_project(project_binding, entities=entities)
        if project_result.status is not ArtifactStatus.SUCCESS:
            return project_result
        if field_binding.project_id != project_binding.project_id:
            return BindingResolution(
                status=ArtifactStatus.HELD,
                errors=("field binding project does not match project binding",),
                hold_reason="project_mismatch",
            )
        if field_binding.context_id != project_binding.context_id:
            return BindingResolution(
                status=ArtifactStatus.HELD,
                errors=("field binding context does not match project context",),
                hold_reason="context_mismatch",
            )
        if field_binding.field_version_id != field_version.version_id:
            return BindingResolution(
                status=ArtifactStatus.HELD,
                errors=("field binding references a different field version",),
                hold_reason="version_mismatch",
            )
        if field_version.project_id != project_binding.project_id:
            return BindingResolution(
                status=ArtifactStatus.HELD,
                errors=("field version project does not match project binding",),
                hold_reason="project_mismatch",
            )
        if field_binding.status not in {LifecycleStatus.ACTIVE, LifecycleStatus.ACCEPTED}:
            return BindingResolution(
                status=ArtifactStatus.HELD,
                errors=("field binding is not active",),
                hold_reason="binding_inactive",
            )
        entity_map = {
            entity_id: entity for entity in entities if (entity_id := _entity_scope(entity)[0])
        }
        missing = sorted(set(field_binding.target_entity_ids) - set(entity_map))
        if missing:
            return BindingResolution(
                status=ArtifactStatus.HELD,
                errors=(f"unknown field target entity ids: {', '.join(missing)}",),
                conflicts=tuple(missing),
                hold_reason="entity_unknown",
            )
        missing_workspace = sorted(
            entity_id
            for entity_id in field_binding.target_entity_ids
            if _entity_scope(entity_map[entity_id])[1] is None
        )
        if missing_workspace:
            return BindingResolution(
                status=ArtifactStatus.HELD,
                errors=(f"field targets lack workspace scope: {', '.join(missing_workspace)}",),
                conflicts=tuple(missing_workspace),
                hold_reason="workspace_missing",
            )
        foreign = sorted(
            entity_id
            for entity_id in field_binding.target_entity_ids
            if entity_map[entity_id]["workspace_id"] != project_binding.workspace_id
        )
        if foreign:
            return BindingResolution(
                status=ArtifactStatus.HELD,
                errors=(f"field targets cross workspace boundary: {', '.join(foreign)}",),
                conflicts=tuple(foreign),
                hold_reason="workspace_mismatch",
            )
        valid_from = _parse_time(field_binding.valid_from)
        valid_until = _parse_time(field_binding.valid_until)
        if (field_binding.valid_from and valid_from is None) or (
            field_binding.valid_until and valid_until is None
        ):
            return BindingResolution(
                status=ArtifactStatus.HELD,
                errors=("field binding has invalid validity time",),
                hold_reason="time_invalid",
            )
        requested_time = _parse_time(at_time)
        if at_time and requested_time is None:
            return BindingResolution(
                status=ArtifactStatus.HELD,
                errors=("requested binding time is invalid",),
                hold_reason="time_invalid",
            )
        if requested_time and (
            (valid_from and requested_time < valid_from)
            or (valid_until and requested_time > valid_until)
        ):
            return BindingResolution(
                status=ArtifactStatus.UNAVAILABLE,
                errors=("field binding is outside its validity interval",),
                hold_reason="time_outside_binding",
            )
        if (
            artifact_type
            and field_binding.artifact_type_selectors
            and artifact_type not in field_binding.artifact_type_selectors
        ):
            return BindingResolution(
                status=ArtifactStatus.UNAVAILABLE,
                errors=("field binding does not select this artifact type",),
                hold_reason="artifact_selector_miss",
            )
        if (
            channel
            and field_binding.channel_selectors
            and channel not in field_binding.channel_selectors
        ):
            return BindingResolution(
                status=ArtifactStatus.UNAVAILABLE,
                errors=("field binding does not select this channel",),
                hold_reason="channel_selector_miss",
            )
        conflicts = self._precedence_conflicts(field_binding, existing_bindings)
        if conflicts:
            return BindingResolution(
                status=ArtifactStatus.HELD,
                errors=("field binding precedence is ambiguous",),
                conflicts=conflicts,
                hold_reason="precedence_ambiguous",
            )
        relationship = RelationshipFrame(
            frame_id=f"creative-field-application:{field_binding.binding_id}",
            frame_type_id="world://relation/creative-field-application",
            context_id=project_binding.context_id,
            role_bindings=(
                RoleBinding(role_id="project", record_ids=(project_binding.project_id,)),
                RoleBinding(role_id="field_version", record_ids=(field_version.version_id,)),
                RoleBinding(role_id="target_entities", record_ids=field_binding.target_entity_ids),
            ),
            status="active",
            derivation_id=f"binding-resolution:{field_binding.binding_id}",
        )
        return BindingResolution(
            status=ArtifactStatus.SUCCESS,
            project_binding=project_binding,
            field_binding=field_binding,
            relationship_frame=relationship,
            receipt={
                "binding_id": field_binding.binding_id,
                "field_version_id": field_version.version_id,
                "context_id": project_binding.context_id,
                "precedence": field_binding.precedence,
            },
        )

    @staticmethod
    def _precedence_conflicts(
        selected: FieldBinding, existing: Iterable[FieldBinding]
    ) -> tuple[str, ...]:
        conflicts: list[str] = []
        selected_targets = set(selected.target_entity_ids)
        for binding in existing:
            if (
                binding.binding_id == selected.binding_id
                or binding.project_id != selected.project_id
            ):
                continue
            if not selected_targets.intersection(binding.target_entity_ids):
                continue
            if (
                selected.artifact_type_selectors
                and binding.artifact_type_selectors
                and not set(selected.artifact_type_selectors).intersection(
                    binding.artifact_type_selectors
                )
            ):
                continue
            if (
                selected.channel_selectors
                and binding.channel_selectors
                and not set(selected.channel_selectors).intersection(binding.channel_selectors)
            ):
                continue
            if (
                binding.precedence == selected.precedence
                and binding.field_version_id != selected.field_version_id
            ):
                conflicts.append(binding.binding_id)
        return tuple(sorted(conflicts))


__all__ = ["BindingResolution", "CreativeBindingResolver"]
