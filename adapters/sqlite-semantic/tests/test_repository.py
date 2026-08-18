import hashlib
from datetime import UTC, datetime

import pytest
from testflight_adapter_sqlite_semantic import SemanticRepository
from testflight_brand import BrandAssertion
from testflight_semantic import EpistemicStatus, EvidenceEnvelope, Perspective


def test_repository_preserves_evidence_and_deduplicates_assertion(tmp_path) -> None:
    content = "The brand promises reliable progress."
    envelope = EvidenceEnvelope(
        source_id="source-1",
        workspace_id="workspace-1",
        content_hash=hashlib.sha256(content.encode()).hexdigest(),
        source_uri="fixture://brand/intent",
        recorded_time=datetime.now(UTC),
    )
    assertion = BrandAssertion(
        assertion_id="assertion-1",
        workspace_id="workspace-1",
        brand_id="brand-1",
        subject_id="brand-1",
        predicate="has_component",
        object_id="component-promise",
        relationship_definition_id="has_component",
        perspective=Perspective.INTENDED,
        epistemic_status=EpistemicStatus.NORMATIVE,
        evidence_ids=("source-1",),
        recorded_at=datetime.now(UTC),
        status="accepted",
    )

    with SemanticRepository(tmp_path / "semantic.sqlite3") as repository:
        repository.put_envelope(envelope, content)
        repository.append_assertions([assertion, assertion])
        records = repository.list_assertions("workspace-1", "brand-1")

    assert len(records) == 1
    assert records[0].evidence_ids == ("source-1",)


def test_repository_rejects_unaccepted_assertion(tmp_path) -> None:
    assertion = BrandAssertion(
        assertion_id="assertion-held",
        workspace_id="workspace-1",
        brand_id="brand-1",
        subject_id="brand-1",
        predicate="has_component",
        object_id="component-promise",
        relationship_definition_id="has_component",
        perspective=Perspective.OBSERVED,
        epistemic_status=EpistemicStatus.HYPOTHESIZED,
        recorded_at=datetime.now(UTC),
        status="held",
    )

    with (
        SemanticRepository(tmp_path / "semantic.sqlite3") as repository,
        pytest.raises(ValueError, match="only accepted"),
    ):
        repository.append_assertions([assertion])


def test_repository_rejects_mutating_an_evidence_envelope(tmp_path) -> None:
    content = "immutable evidence"
    envelope = EvidenceEnvelope(
        source_id="source-immutable",
        workspace_id="workspace-1",
        content_hash=hashlib.sha256(content.encode()).hexdigest(),
        source_uri="fixture://brand/immutable",
        recorded_time=datetime.now(UTC),
    )

    with SemanticRepository(tmp_path / "semantic.sqlite3") as repository:
        repository.put_envelope(envelope, content)
        with pytest.raises(ValueError, match="immutable"):
            repository.put_envelope(
                envelope.model_copy(update={"source_uri": "fixture://brand/changed"}), content
            )
