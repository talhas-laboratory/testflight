from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.populate_testflight_product_workspace import build_documents  # noqa: E402
from scripts.validate_testflight_product_workspace import validate_workspace  # noqa: E402


def test_product_workspace_family_is_structurally_valid() -> None:
    report = validate_workspace(REPO_ROOT)

    assert report["status"] == "pass"
    assert report["workspace_id"] == "world://workspace/testflight-product"
    assert report["module_count"] == 9
    assert report["entity_count"] >= 40
    assert report["relationship_count"] >= 10
    assert report["source_count"] >= 15
    assert report["design_revision"] == "0.1.0"
    assert report["live_projection_changed"] is False


def test_product_projection_is_deterministic_and_workspace_scoped() -> None:
    first = build_documents(REPO_ROOT)
    second = build_documents(REPO_ROOT)

    assert [(item.document_id, item.text) for item in first] == [
        (item.document_id, item.text) for item in second
    ]
    assert len({item.document_id for item in first}) == len(first)
    assert all(item.metadata["workspace_id"] == item.workspace_id for item in first)
    assert all(item.source_url.startswith("repo://") for item in first)
    assert all("SOURCE_HASH:" in item.text for item in first)
    assert all(
        item.metadata["document_role"] in {"content", "policy", "registry", "report"}
        for item in first
    )
    assert all(item.metadata["container_scope"] in {"parent", "child"} for item in first)


def test_product_children_use_isolated_staging_datasets() -> None:
    report = validate_workspace(REPO_ROOT)
    datasets = [module["dataset_name"] for module in report["modules"]]

    assert len(datasets) == len(set(datasets))
    assert all(dataset.endswith("_staging") for dataset in datasets)
