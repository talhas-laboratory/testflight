from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.populate_reasoning_operator_workspace import (  # noqa: E402
    build_documents,
    validate_workspace,
)


def test_workspace_manifest_and_metadata_are_valid() -> None:
    validated = validate_workspace(REPO_ROOT)

    assert validated["manifest"]["id"] == "world://workspace/reasoning-operators"
    assert validated["manifest"]["cognee"]["dataset_name"] == "testflight_reasoning_operators"
    assert len(validated["catalog"]["operators"]) == 16


def test_workspace_materialization_is_bounded_and_provenance_bearing() -> None:
    documents = build_documents(REPO_ROOT)

    assert len(documents) == 26
    assert len({document.document_id for document in documents}) == len(documents)
    assert all("WORKSPACE_ID:" in document.text for document in documents)
    assert all("SOURCE_HASH:" in document.text for document in documents)
    assert all(document.metadata["source_url"].startswith("repo://") for document in documents)


def test_workspace_materialization_is_deterministic() -> None:
    first = build_documents(REPO_ROOT)
    second = build_documents(REPO_ROOT)

    assert [(item.document_id, item.text) for item in first] == [
        (item.document_id, item.text) for item in second
    ]
