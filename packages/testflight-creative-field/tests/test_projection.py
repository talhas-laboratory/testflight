from testflight_creative_field import (
    ArtifactStatus,
    CreativeContextCompiler,
    CreativeFieldVersion,
    CreativeRequest,
    DimensionState,
    FieldBinding,
    LifecycleStatus,
    Principle,
    TargetCapabilityManifest,
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
        dimension_states=(
            DimensionState(
                dimension_id="visual",
                summary="restrained contrast",
                source_contribution_ids=("contribution:one",),
            ),
            DimensionState(
                dimension_id="material",
                summary="soft tactility",
                source_contribution_ids=("contribution:two",),
            ),
        ),
        lifecycle_status=LifecycleStatus.ACCEPTED,
        source_contribution_ids=("contribution:one", "contribution:two"),
        created_at="2026-09-03T00:00:00Z",
    )


def _request() -> CreativeRequest:
    return CreativeRequest(
        request_id="request:one",
        project_id="project:one",
        task_type="create",
        artifact_type="hero-image",
        modality="image",
        target="image-provider",
        permission_context={"disclosure_manifest_id": "disclosure:one"},
    )


def _binding() -> FieldBinding:
    return FieldBinding(
        binding_id="field-binding:one",
        project_id="project:one",
        field_version_id="field:one@1",
        target_entity_ids=("brand:one",),
        context_id="context:one",
        authority_grant_id="grant:one",
    )


def _target() -> TargetCapabilityManifest:
    return TargetCapabilityManifest(
        target_id="image-provider",
        adapter_version="1",
        accepted_modalities=("image",),
        controls={"unsupported_dimension_ids": ["material"]},
        privacy_policy_id="policy:one",
    )


def test_compiler_resolves_request_and_composes_field_with_world_view() -> None:
    compiler = CreativeContextCompiler()
    resolved = compiler.resolve_request(
        request=_request(),
        project_binding_id="project-binding:one",
        field_binding=_binding(),
        field_version=_version(),
        world_view_request_id="world-view-request:one",
        target_capability_manifest_id="image-provider",
        lens="hero-image",
    )
    assert resolved.status is ArtifactStatus.SUCCESS
    assert resolved.resolved_request is not None
    result = compiler.compile(
        resolved_request=resolved.resolved_request,
        request=_request(),
        field_version=_version(),
        field_binding=_binding(),
        world_view={
            "view_id": "world-view:one",
            "status": "hit",
            "selected_record_ids": ["brand:one", "campaign:one"],
            "citations": ["evidence:brand"],
        },
        target_manifest=_target(),
        disclosure_manifest_id="disclosure:one",
        visual_language_revision_ids=("visual-language:one@2",),
    )
    assert result.status is ArtifactStatus.PARTIAL
    assert result.projection is not None
    assert result.projection.dimension_mappings.keys() == {"visual"}
    assert any("material" in item for item in result.projection.omissions)
    assert result.packet is not None
    assert result.packet.resolved_world_view_id == "world-view:one"
    assert result.packet.visual_language_revision_ids == ("visual-language:one@2",)
    assert "brand:one" in result.packet.selected_record_ids


def test_compiler_holds_on_missing_world_view_or_binding_mismatch() -> None:
    compiler = CreativeContextCompiler()
    resolved = compiler.resolve_request(
        request=_request(),
        project_binding_id="project-binding:one",
        field_binding=_binding(),
        field_version=_version(),
        world_view_request_id="world-view-request:one",
        target_capability_manifest_id="image-provider",
        lens="hero-image",
    ).resolved_request
    assert resolved is not None
    missing_world = compiler.compile(
        resolved_request=resolved,
        request=_request(),
        field_version=_version(),
        field_binding=_binding(),
        world_view={"status": "no_hit"},
        target_manifest=_target(),
        disclosure_manifest_id="disclosure:one",
    )
    mismatch = compiler.resolve_request(
        request=_request().model_copy(update={"project_id": "project:other"}),
        project_binding_id="project-binding:one",
        field_binding=_binding(),
        field_version=_version(),
        world_view_request_id="world-view-request:one",
        target_capability_manifest_id="image-provider",
        lens="hero-image",
    )
    assert missing_world.status is ArtifactStatus.HELD
    assert missing_world.packet is None
    assert mismatch.status is ArtifactStatus.HELD


def test_compiler_does_not_use_semantic_defaults_for_unsupported_modality() -> None:
    compiler = CreativeContextCompiler()
    resolved = compiler.resolve_request(
        request=_request().model_copy(update={"modality": "video"}),
        project_binding_id="project-binding:one",
        field_binding=_binding(),
        field_version=_version(),
        world_view_request_id="world-view-request:one",
        target_capability_manifest_id="image-provider",
        lens="hero-image",
    ).resolved_request
    assert resolved is not None
    result = compiler.compile(
        resolved_request=resolved,
        request=_request().model_copy(update={"modality": "video"}),
        field_version=_version(),
        field_binding=_binding(),
        world_view={"view_id": "world-view:one", "status": "hit"},
        target_manifest=_target(),
        disclosure_manifest_id="disclosure:one",
    )
    assert result.status is ArtifactStatus.UNAVAILABLE
    assert result.projection is None
