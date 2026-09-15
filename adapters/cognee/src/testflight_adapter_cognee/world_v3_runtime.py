"""Single-writer runtime for durable World v3 graph rebuild requests."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol

from testflight_world import WorldProjectionJob, WorldSnapshot

from .world_v3_projection import (
    build_world_v3_projection,
    populate_world_v3_projection,
    validate_world_v3_projection,
    write_world_v3_projection_manifest,
)


class WorldProjectionOutbox(Protocol):
    def claim_projection_job(self) -> WorldProjectionJob | None: ...

    def complete_projection_job(
        self, job_id: str, *, error: str | None = None
    ) -> WorldProjectionJob: ...


class CanonicalWorldReader(Protocol):
    def snapshot(self, workspace_id: str, branch_id: str) -> WorldSnapshot: ...


class WorldV3ProjectionWorker:
    """Projects accepted state serially; this class never mutates canonical World records."""

    def __init__(
        self,
        *,
        outbox: WorldProjectionOutbox,
        world: CanonicalWorldReader,
        manifest_root: Path,
        dataset_prefix: str = "testflight_world_v3",
    ) -> None:
        self._outbox = outbox
        self._world = world
        self._manifest_root = manifest_root
        self._dataset_prefix = dataset_prefix

    async def run_once(self) -> dict[str, str | int] | None:
        job = self._outbox.claim_projection_job()
        if job is None:
            return None
        try:
            snapshot = self._world.snapshot(job.workspace_id, job.branch_id)
            if not snapshot.records:
                raise ValueError("accepted World snapshot is empty")
            if snapshot.snapshot_root != job.source_snapshot_root:
                raise ValueError(
                    "canonical World changed before projection; a newer projection job is required"
                )
            dataset_name = self._dataset_name(job)
            manifest = build_world_v3_projection(
                snapshot.records,
                workspace_id=job.workspace_id,
                branch_id=job.branch_id,
                dataset_name=dataset_name,
                source_revision=job.source_revision,
                snapshot_root_value=job.source_snapshot_root,
                lifecycle_scope=("accepted",),
            )
            validate_world_v3_projection(manifest)
            manifest_path = (
                self._manifest_root
                / _safe_name(job.workspace_id)
                / _safe_name(job.branch_id)
                / f"{_safe_name(job.source_revision)}.json"
            )
            write_world_v3_projection_manifest(manifest, manifest_path)
            receipt = await populate_world_v3_projection(manifest)
            self._outbox.complete_projection_job(job.job_id)
            return {**receipt, "job_id": job.job_id, "manifest_path": str(manifest_path)}
        except Exception as error:
            self._outbox.complete_projection_job(job.job_id, error=str(error))
            raise

    def _dataset_name(self, job: WorldProjectionJob) -> str:
        scope_hash = hashlib.sha256(
            f"{job.workspace_id}|{job.branch_id}|{job.source_revision}".encode()
        ).hexdigest()[:20]
        return f"{self._dataset_prefix}_{scope_hash}_staging"


def _safe_name(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


__all__ = ["CanonicalWorldReader", "WorldProjectionOutbox", "WorldV3ProjectionWorker"]
