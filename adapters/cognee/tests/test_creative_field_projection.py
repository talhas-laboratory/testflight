from pathlib import Path

import pytest
from testflight_adapter_cognee.creative_field_projection import (
    bounded_creative_field_traversal,
    build_creative_field_projection,
    compare_projection_drift,
    read_projection_manifest,
    write_projection_manifest,
)
from testflight_creative_field import (
    CreativeFieldVersion,
    FieldBinding,
    LifecycleStatus,
    Principle,
    ProjectBinding,
    ReferenceAsset,
    ReferenceContribution,
    SourceLicenseRecord,
)


def _records() -> list[object]:
    license_record = SourceLicenseRecord(
        license_record_id="license:one",
        source_id="source:one",
        permitted_use=("reference",),
        disclosure_allowed=False,
        generation_allowed=False,
        retention_policy="project-lifetime",
        limitations=("do not send to generation target",),
    )
    asset = ReferenceAsset(
        asset_id="asset:one",
        project_id="project:one",
        source_id="source:one",
        media_type="image/jpeg",
        label="soft reference",
        content_hash="sha256:one",
        source_uri="blob://sha256:one",
        license_record_id="license:one",
        recorded_at="2026-09-03T00:00:00Z",
    )
    contribution = ReferenceContribution(
        contribution_id="contribution:one",
        interpretation_id="interpretation:one",
        reference_asset_id=asset.asset_id,
        dimension_id="material",
        role="tactility",
        transfer_instruction="preserve softness",
        anti_transfer_instruction="do not reproduce the object",
        evidence_refs=("region:one",),
        derivation_id="derivation:one",
    )
    principle = Principle(
        principle_id="principle:one",
        statement="Use precise form with soft tactility.",
        dimension_ids=("material",),
        source_contribution_ids=(contribution.contribution_id,),
    )
    version = CreativeFieldVersion(
        field_id="field:one",
        version_id="field:one@1",
        project_id="project:one",
        principles=(principle,),
        source_contribution_ids=(contribution.contribution_id,),
        lifecycle_status=LifecycleStatus.ACTIVE,
        created_at="2026-09-03T00:00:00Z",
    )
    project_binding = ProjectBinding(
        binding_id="project-binding:one",
        project_id="project:one",
        workspace_id="world://workspace/one",
        context_id="context:one",
        target_entity_ids=("entity:one",),
        branch_id="branch:one",
        privacy_policy_id="privacy:one",
        authority_grant_id="grant:one",
    )
    field_binding = FieldBinding(
        binding_id="field-binding:one",
        project_id="project:one",
        field_version_id=version.version_id,
        target_entity_ids=("entity:one",),
        context_id="context:one",
        authority_grant_id="grant:one",
    )
    return [license_record, asset, contribution, principle, version, project_binding, field_binding]


def test_projection_is_deterministic_namespaced_and_preserves_rights() -> None:
    kwargs = {
        "child_workspace_id": "world://workspace/one/creative-field",
        "parent_workspace_id": "world://workspace/one",
        "project_id": "project:one",
        "dataset_name": "testflight_creative_field_one_staging",
    }
    first = build_creative_field_projection(_records(), **kwargs)
    second = build_creative_field_projection(_records(), **kwargs)

    assert first.source_hash == second.source_hash
    assert [item.document_id for item in first.documents] == [
        item.document_id for item in second.documents
    ]
    assert all(
        item.metadata["child_workspace_id"] == kwargs["child_workspace_id"]
        for item in first.documents
    )
    asset = next(item for item in first.documents if item.record_id == "asset:one")
    assert asset.metadata["rights"]["generation_allowed"] is False
    assert asset.metadata["promotion_status"] == "proposal_only"
    assert first.custom_edges
    assert any(edge[3]["target_record_id"] == "principle:one" for edge in first.custom_edges)


def test_projection_rejects_cross_project_records_and_non_staging_targets() -> None:
    with pytest.raises(ValueError, match="project boundary"):
        build_creative_field_projection(
            [
                ReferenceAsset(
                    asset_id="asset:foreign",
                    project_id="project:foreign",
                    source_id="source:foreign",
                    media_type="image/jpeg",
                    label="foreign",
                    content_hash="sha256:foreign",
                    source_uri="blob://foreign",
                    recorded_at="2026-09-03T00:00:00Z",
                )
            ],
            child_workspace_id="child",
            parent_workspace_id="parent",
            project_id="project:one",
            dataset_name="creative_field_production_staging",
        )
    with pytest.raises(ValueError, match="isolated"):
        build_creative_field_projection(
            _records(),
            child_workspace_id="child",
            parent_workspace_id="parent",
            project_id="project:one",
            dataset_name="creative_field_production",
        )


def test_projection_manifest_supports_atomic_rebuild_and_drift(tmp_path: Path) -> None:
    kwargs = {
        "child_workspace_id": "child",
        "parent_workspace_id": "parent",
        "project_id": "project:one",
        "dataset_name": "creative_field_one_staging",
    }
    manifest = build_creative_field_projection(_records(), **kwargs)
    path = tmp_path / "projection" / "manifest.json"
    write_projection_manifest(manifest, path)
    loaded = read_projection_manifest(path)
    assert compare_projection_drift(manifest, loaded)["status"] == "up_to_date"

    changed_records = [
        record.model_copy(update={"statement": "Changed."})
        if isinstance(record, Principle)
        else record
        for record in _records()
    ]
    changed = build_creative_field_projection(changed_records, **kwargs)
    drift = compare_projection_drift(changed, loaded)
    assert drift["status"] == "drifted"
    assert "principle:one" in drift["changed_record_ids"]


def test_projection_traversal_is_explicit_and_hard_bounded() -> None:
    manifest = build_creative_field_projection(
        _records(),
        child_workspace_id="child",
        parent_workspace_id="parent",
        project_id="project:one",
        dataset_name="creative_field_one_staging",
    )
    edges = bounded_creative_field_traversal(
        manifest,
        source_record_id="field:one@1",
        max_hops=2,
    )
    assert edges
    with pytest.raises(ValueError, match="max_hops"):
        bounded_creative_field_traversal(
            manifest,
            source_record_id="field:one@1",
            max_hops=3,
        )
