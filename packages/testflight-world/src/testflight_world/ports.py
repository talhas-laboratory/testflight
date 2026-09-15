"""Ports for canonical Brand World v3 persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from testflight_semantic import AuthorityGrant

from .models import WorldChangeSet, WorldHistoryEntry, WorldProjectionJob, WorldReview


class AuthorityGrantResolver(Protocol):
    """Resolve immutable authority grants by exact identity."""

    def resolve(self, grant_id: str) -> AuthorityGrant | None: ...


class WorldRepository(Protocol):
    def put_proposal(self, change_set: WorldChangeSet) -> None: ...

    def get_proposal(self, proposal_id: str) -> WorldChangeSet | None: ...

    def replace_proposal(self, change_set: WorldChangeSet) -> None: ...

    def accept_proposal(
        self,
        change_set: WorldChangeSet,
        history_entries: tuple[WorldHistoryEntry, ...],
        projection_job: WorldProjectionJob,
    ) -> None: ...

    def claim_projection_job(self) -> WorldProjectionJob | None: ...

    def complete_projection_job(
        self, job_id: str, *, error: str | None = None
    ) -> WorldProjectionJob: ...

    def active_projection_job(
        self, workspace_id: str, branch_id: str
    ) -> WorldProjectionJob | None: ...

    def append_history(self, entry: WorldHistoryEntry) -> None: ...

    def append_review(self, review: WorldReview) -> None: ...

    def reviews(self, proposal_id: str) -> tuple[WorldReview, ...]: ...

    def history(
        self,
        record_id: str,
        *,
        workspace_id: str | None = None,
        branch_id: str | None = None,
        recorded_at: datetime | None = None,
    ) -> tuple[WorldHistoryEntry, ...]: ...

    def snapshot(
        self,
        workspace_id: str,
        branch_id: str,
        *,
        recorded_at: datetime | None = None,
    ) -> tuple[WorldHistoryEntry, ...]: ...


__all__ = ["AuthorityGrantResolver", "WorldRepository"]
