from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from populate_brand_research_workspace import (  # noqa: E402
    build_documents,
    validate_pack,
)


def test_projection_pack_validates_without_credentials() -> None:
    validated = validate_pack()
    documents = build_documents(validated=validated)

    assert validated["corpus"]["source_count"] == 24
    assert validated["fixtures"]["status"] == "certified"
    assert len(documents) >= 10
    assert all(
        document.metadata["projection_role"] == "research_evidence_or_candidate"
        for document in documents
    )


def test_projection_document_ids_are_deterministic() -> None:
    first = build_documents()
    second = build_documents()

    assert [document.document_id for document in first] == [
        document.document_id for document in second
    ]
    assert [document.metadata["source_hash"] for document in first] == [
        document.metadata["source_hash"] for document in second
    ]


def test_projection_is_gated_before_cognee_population() -> None:
    validated = validate_pack()

    assert validated["manifest"]["cognee"]["population_status"] == "pack_only_until_certified"
