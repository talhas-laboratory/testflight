from pathlib import Path

import pytest
from testflight_creative_field import (
    BoardRevision,
    CreativeFieldVersion,
    FieldBinding,
    FieldDimension,
    LifecycleStatus,
    Placement,
    ProjectBinding,
    ReferenceCluster,
    ReviewAction,
    ReviewDecision,
    load_dimension_registry,
)


def test_board_revision_requires_placements_to_reference_board_assets() -> None:
    with pytest.raises(ValueError, match="outside the revision"):
        BoardRevision(
            board_revision_id="board-revision:1",
            moodboard_id="moodboard:1",
            project_id="project:1",
            revision=1,
            reference_asset_ids=("asset:known",),
            placements=(
                Placement(
                    placement_id="placement:1",
                    asset_id="asset:unknown",
                    x=0,
                    y=0,
                    width=1,
                    height=1,
                ),
            ),
            created_at="2026-09-03T00:00:00Z",
            created_by="user:1",
        )


def test_field_version_is_immutable_and_cannot_parent_itself() -> None:
    with pytest.raises(ValueError, match="cannot parent itself"):
        CreativeFieldVersion(
            field_id="field:1",
            version_id="field:1@1",
            project_id="project:1",
            parent_version_ids=("field:1@1",),
            created_at="2026-09-03T00:00:00Z",
        )


def test_bindings_preserve_explicit_project_scope_and_authority() -> None:
    project = ProjectBinding(
        binding_id="project-binding:1",
        project_id="project:1",
        workspace_id="world://workspace/brand/example",
        context_id="context:example",
        target_entity_ids=("brand:example",),
        branch_id="branch:main",
        privacy_policy_id="policy:local",
        authority_grant_id="grant:project",
    )
    field = FieldBinding(
        binding_id="field-binding:1",
        project_id=project.project_id,
        field_version_id="field:1@1",
        target_entity_ids=("campaign:example",),
        context_id=project.context_id,
        authority_grant_id="grant:field",
    )
    assert field.project_id == project.project_id
    assert field.status is LifecycleStatus.ACTIVE


def test_cluster_and_review_records_are_typed_and_immutable() -> None:
    cluster = ReferenceCluster(
        cluster_id="cluster:1",
        project_id="project:1",
        label="warm references",
        asset_ids=("asset:1", "asset:2"),
    )
    review = ReviewDecision(
        review_id="review:1",
        target_id=cluster.cluster_id,
        action=ReviewAction.ACCEPT,
        actor_id="user:1",
        rationale="The grouping is intentional.",
        created_at="2026-09-03T00:00:00Z",
    )
    assert review.action is ReviewAction.ACCEPT
    with pytest.raises(ValueError):
        cluster.model_copy(update={"asset_ids": ("asset:1", "asset:1")}).unique_assets()


def test_dimension_registry_loads_extensible_dimensions() -> None:
    dimensions = load_dimension_registry(Path("domains/creative-field/dimensions.yaml"))
    assert len(dimensions) == 10
    assert all(isinstance(item, FieldDimension) for item in dimensions)
