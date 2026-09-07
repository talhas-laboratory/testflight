import hashlib

import pytest
from testflight_adapter_sqlite_semantic import (
    ContentAddressedBlobStore,
    CreativeRepository,
    RevisionConflictError,
)
from testflight_creative_field import BoardRevision, Placement, ReferenceAsset


def _asset(asset_id: str, source_id: str, content_hash: str) -> ReferenceAsset:
    return ReferenceAsset(
        asset_id=asset_id,
        project_id="project:creative",
        source_id=source_id,
        media_type="image/png",
        label=asset_id,
        content_hash=content_hash,
        source_uri=f"blob://sha256/{content_hash}",
        recorded_at="2026-09-03T00:00:00Z",
    )


def _revision(revision: int, asset_id: str) -> BoardRevision:
    return BoardRevision(
        board_revision_id=f"board-revision:{revision}",
        moodboard_id="moodboard:creative",
        project_id="project:creative",
        revision=revision,
        reference_asset_ids=(asset_id,),
        placements=(
            Placement(
                placement_id=f"placement:{revision}",
                asset_id=asset_id,
                x=0,
                y=0,
                width=100,
                height=100,
            ),
        ),
        created_at=f"2026-09-03T00:0{revision}:00Z",
        created_by="user:creative",
    )


def test_content_addressed_store_deduplicates_bytes_and_tracks_derivatives(tmp_path) -> None:
    store = ContentAddressedBlobStore(tmp_path / "runtime-data")
    content = b"client reference bytes"
    source = store.put(content, media_type="image/png")
    duplicate = store.put(content, media_type="image/png")
    derivative = store.put_derived(
        b"thumbnail bytes",
        media_type="image/webp",
        source_hash=source.content_hash,
        derivative_kind="thumbnail",
    )

    assert source == duplicate
    assert source.content_hash == hashlib.sha256(content).hexdigest()
    assert source.uri.startswith("blob://sha256/")
    assert derivative.source_hash == source.content_hash
    assert store.read(source.content_hash) == content
    assert source.size != derivative.size


def test_creative_repository_keeps_distinct_source_identities_for_duplicate_bytes(tmp_path) -> None:
    content_hash = hashlib.sha256(b"same bytes").hexdigest()
    with CreativeRepository(tmp_path / "creative.sqlite3") as repository:
        repository.append(_asset("asset:one", "upload:one", content_hash))
        repository.append(_asset("asset:two", "upload:two", content_hash))
        records = repository.list(ReferenceAsset, project_id="project:creative")

    assert [item.source_id for item in records] == ["upload:one", "upload:two"]
    assert records[0].content_hash == records[1].content_hash


def test_board_revisions_replay_and_reject_stale_writes_atomically(tmp_path) -> None:
    with CreativeRepository(tmp_path / "creative.sqlite3") as repository:
        first = _revision(1, "asset:one")
        second = _revision(2, "asset:two")
        repository.put_board_revision(first)
        with pytest.raises(RevisionConflictError, match="expected 0"):
            repository.put_board_revision(second, expected_revision=0)
        assert repository.latest_board_revision("moodboard:creative") == 1
        repository.put_board_revision(second, expected_revision=1)
        assert repository.replay_board("moodboard:creative") == [first, second]
