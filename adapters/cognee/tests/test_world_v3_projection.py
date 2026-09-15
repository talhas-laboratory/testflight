import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from testflight_adapter_cognee.context_retrieval_bridge import (
    search_world_v3_projection,
    world_v3_manifest_edges,
    world_v3_projection_items,
)
from testflight_adapter_cognee.world_v3_projection import (
    bounded_world_v3_traversal,
    build_world_v3_projection,
    compare_world_v3_projection_drift,
    world_v3_projection_to_datapoints,
    write_world_v3_projection_manifest,
)
from testflight_world import WorldChangeSet

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = ROOT / "workspaces/brand-hellobiotic-research/v3/proposed-public-research-branch.json"
WORKSPACE = "world://workspace/brand/hellobiotic-research"
BRANCH = "public-research-v3"


def _records():
    return WorldChangeSet.model_validate(json.loads(BUNDLE.read_text(encoding="utf-8"))).records


def _projection():
    return build_world_v3_projection(
        _records(),
        workspace_id=WORKSPACE,
        branch_id=BRANCH,
        dataset_name="testflight_brand_hellobiotic_v3_preview_staging",
        source_revision="biotic-proposal-v3-fixture",
        lifecycle_scope=("proposed",),
    )


def test_biotic_v3_projection_is_complete_deterministic_and_role_preserving() -> None:
    first = _projection()
    second = _projection()

    assert len(_records()) == 56
    assert first.source_hash == second.source_hash
    assert first.nodes == second.nodes
    assert first.custom_edges == second.custom_edges
    assert {node.record_id for node in first.nodes}.issuperset(record.id for record in _records())
    assert first.custom_edges
    assert all(
        edge[3]["source_revision"] == "biotic-proposal-v3-fixture" for edge in first.custom_edges
    )
    assert any(edge[2] == "SUPPORTED_BY" for edge in first.custom_edges)
    assert any(edge[2] == "EXCERPT_OF" for edge in first.custom_edges)


def test_projection_points_are_semantically_indexed_and_dataset_scoped() -> None:
    manifest = _projection()
    points = world_v3_projection_to_datapoints(manifest)

    assert points
    assert all(point.dataset_name == manifest.dataset_name for point in points)
    assert all(point.metadata["index_fields"] == ["label", "text"] for point in points)


def test_candidate_filter_enforces_dataset_module_and_world_scope() -> None:
    manifest = _projection()
    identity_module = "world://ontology/module/brand-world/identity"
    node = next(
        item for item in manifest.nodes if item.metadata.get("module_id") == identity_module
    )
    raw = {
        "dataset_name": manifest.dataset_name,
        "record_id": node.record_id,
        "record_version": node.record_version,
        "metadata_json": json.dumps(node.metadata),
        "score": 0.9,
    }
    request = {
        "datasetName": manifest.dataset_name,
        "workspaceId": WORKSPACE,
        "branchId": BRANCH,
        "lifecycleStatuses": ["proposed"],
        "moduleIds": [identity_module],
    }

    assert [item["recordId"] for item in world_v3_projection_items([raw], request)] == [
        node.record_id
    ]
    assert world_v3_projection_items([{**raw, "dataset_name": "another_staging"}], request) == []
    assert (
        world_v3_projection_items(
            [raw], {**request, "moduleIds": ["world://ontology/module/brand-world/offering"]}
        )
        == []
    )


def test_world_v3_search_reads_typed_projection_indexes(monkeypatch) -> None:
    calls: list[str] = []

    class Vector:
        async def search(self, collection_name: str, **_kwargs):
            calls.append(collection_name)
            return [
                SimpleNamespace(
                    id="00000000-0000-0000-0000-000000000001",
                    score=0.25,
                    payload={"record_id": "entity:biotic"},
                )
            ]

    async def vector_engine():
        return Vector()

    import cognee.infrastructure.databases.vector as vector_module

    monkeypatch.setattr(vector_module, "get_vector_engine_async", vector_engine)
    results = asyncio.run(search_world_v3_projection("microbiome care", 4))

    assert calls == ["WorldV3DataPoint_label", "WorldV3DataPoint_text"]
    assert results == [{"record_id": "entity:biotic", "score": 0.8}]


def test_projection_rejects_unscoped_or_non_staging_population_targets() -> None:
    with pytest.raises(ValueError, match="lifecycle scope"):
        build_world_v3_projection(
            _records(),
            workspace_id=WORKSPACE,
            branch_id=BRANCH,
            dataset_name="testflight_brand_hellobiotic_v3_preview_staging",
            source_revision="revision",
            lifecycle_scope=(),
        )
    with pytest.raises(ValueError, match="isolated"):
        build_world_v3_projection(
            _records(),
            workspace_id=WORKSPACE,
            branch_id=BRANCH,
            dataset_name="production",
            source_revision="revision",
            lifecycle_scope=("proposed",),
        )


def test_projection_manifest_is_atomic_and_traversal_is_hard_bounded(tmp_path: Path) -> None:
    manifest = _projection()
    path = tmp_path / "projection" / "manifest.json"
    write_world_v3_projection_manifest(manifest, path)
    previous = json.loads(path.read_text(encoding="utf-8"))
    assert compare_world_v3_projection_drift(manifest, previous)["status"] == "up_to_date"
    assert bounded_world_v3_traversal(manifest, source_record_id="entity:biotic", max_hops=2)
    with pytest.raises(ValueError, match="max_hops"):
        bounded_world_v3_traversal(manifest, source_record_id="entity:biotic", max_hops=3)


def test_manifest_expansion_returns_only_bounded_declared_edges(tmp_path: Path) -> None:
    manifest = _projection()
    path = tmp_path / "world-v3-projection.json"
    write_world_v3_projection_manifest(manifest, path)

    root, edges = world_v3_manifest_edges(
        {
            "manifestPath": str(path),
            "workspaceId": WORKSPACE,
            "branchId": BRANCH,
            "lifecycleStatuses": ["proposed"],
            "maximumGraphEdges": 2,
            "maximumGraphHops": 2,
            "allowedRelationTypeIds": ["world://ontology/brand-world/relation/offers"],
            "seedRecordIds": ["entity:biotic"],
        },
        [],
    )

    assert root == manifest.snapshot_root
    assert 0 < len(edges) <= 2
    assert all(edge["edgeClass"] in {"canonical_relation", "canonical_reference"} for edge in edges)
    assert any(
        "entity:biotic" in {edge["sourceRecordId"], edge["targetRecordId"]} for edge in edges
    )
