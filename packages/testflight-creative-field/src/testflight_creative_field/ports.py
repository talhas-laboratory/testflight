"""Persistence ports for the creative domain.

The creative package defines contracts only. Filesystem, SQLite, object storage and model
providers implement these protocols at their respective adapter boundaries.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, TypeVar

from .models import BoardRevision, CreativeRecord


@dataclass(frozen=True, slots=True)
class BlobReference:
    """A content-addressed binary reference; the bytes live outside the record store."""

    content_hash: str
    size: int
    media_type: str
    uri: str
    source_hash: str | None = None
    derivative_kind: str | None = None


RecordT = TypeVar("RecordT", bound=CreativeRecord)


class CreativeRecordRepository(Protocol):
    """Append/read port for immutable creative records."""

    def append(self, record: CreativeRecord, *, project_id: str | None = None) -> None: ...

    def append_many(self, records: Sequence[CreativeRecord]) -> None: ...

    def get(self, model: type[RecordT], record_id: str) -> RecordT | None: ...

    def list(self, model: type[RecordT], *, project_id: str | None = None) -> list[RecordT]: ...

    def put_board_revision(
        self, revision: BoardRevision, *, expected_revision: int | None = None
    ) -> None: ...

    def replay_board(self, moodboard_id: str) -> Sequence[BoardRevision]: ...


class BinaryAssetStore(Protocol):
    """Port for content-addressed source and derived media."""

    def put(self, content: bytes, *, media_type: str) -> BlobReference: ...

    def put_derived(
        self,
        content: bytes,
        *,
        media_type: str,
        source_hash: str,
        derivative_kind: str,
    ) -> BlobReference: ...
