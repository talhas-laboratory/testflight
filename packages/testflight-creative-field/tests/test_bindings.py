from testflight_creative_field import (
    ArtifactStatus,
    CreativeBindingResolver,
    CreativeFieldVersion,
    FieldBinding,
    LifecycleStatus,
    Principle,
    ProjectBinding,
)


def _project() -> ProjectBinding:
    return ProjectBinding(
        binding_id="project-binding:one",
        project_id="project:one",
        workspace_id="workspace:one",
        context_id="context:one",
        target_entity_ids=("brand:one", "offering:one"),
        branch_id="branch:main",
        privacy_policy_id="policy:one",
        authority_grant_id="grant:one",
    )


def _version() -> CreativeFieldVersion:
    return CreativeFieldVersion(
        field_id="field:one",
        version_id="field:one@1",
        project_id="project:one",
        principles=(
            Principle(
                principle_id="principle:one",
                statement="Keep precise warmth",
                dimension_ids=("visual",),
                source_contribution_ids=("contribution:one",),
            ),
        ),
        lifecycle_status=LifecycleStatus.ACCEPTED,
        created_at="2026-09-03T00:00:00Z",
    )


def _field(**updates) -> FieldBinding:
    values = {
        "binding_id": "field-binding:one",
        "project_id": "project:one",
        "field_version_id": "field:one@1",
        "target_entity_ids": ("brand:one",),
        "context_id": "context:one",
        "authority_grant_id": "grant:one",
    }
    values.update(updates)
    return FieldBinding(**values)


def _entities():
    return (
        {"entity_id": "brand:one", "workspace_id": "workspace:one", "kind": "brand"},
        {"entity_id": "offering:one", "workspace_id": "workspace:one", "kind": "offering"},
    )


def test_binding_resolves_to_canonical_entities_and_relationship_frame() -> None:
    result = CreativeBindingResolver().resolve_field(
        project_binding=_project(),
        field_binding=_field(),
        field_version=_version(),
        entities=_entities(),
    )
    assert result.status is ArtifactStatus.SUCCESS
    assert result.relationship_frame is not None
    assert result.relationship_frame.frame_type_id == "world://relation/creative-field-application"
    assert {item.role_id for item in result.relationship_frame.role_bindings} == {
        "project",
        "field_version",
        "target_entities",
    }


def test_cross_workspace_and_time_mismatch_hold_or_unavailable() -> None:
    foreign = CreativeBindingResolver().resolve_field(
        project_binding=_project(),
        field_binding=_field(target_entity_ids=("brand:foreign",)),
        field_version=_version(),
        entities=(*_entities(), {"entity_id": "brand:foreign", "workspace_id": "workspace:other"}),
    )
    outside_time = CreativeBindingResolver().resolve_field(
        project_binding=_project(),
        field_binding=_field(valid_from="2026-10-01T00:00:00Z"),
        field_version=_version(),
        entities=_entities(),
        at_time="2026-09-03T00:00:00Z",
    )
    assert foreign.status is ArtifactStatus.HELD
    assert outside_time.status is ArtifactStatus.UNAVAILABLE


def test_same_precedence_overlapping_versions_hold_as_ambiguous() -> None:
    selected = _field()
    conflicting = _field(binding_id="field-binding:two", field_version_id="field:one@2")
    result = CreativeBindingResolver().resolve_field(
        project_binding=_project(),
        field_binding=selected,
        field_version=_version(),
        entities=_entities(),
        existing_bindings=(conflicting,),
    )
    assert result.status is ArtifactStatus.HELD
    assert result.hold_reason == "precedence_ambiguous"
    assert result.conflicts == ("field-binding:two",)
