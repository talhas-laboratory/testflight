"""Deterministic identities for resolved, canonical World snapshots."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable

from testflight_semantic import WorldRecordType

from .models import WorldSnapshotLeaf


def canonical_record_hash(record: WorldRecordType) -> str:
    """Hash exact canonical content; never a provider projection or generated summary."""

    payload = json.dumps(
        record.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def snapshot_leaves(records: Iterable[WorldRecordType]) -> tuple[WorldSnapshotLeaf, ...]:
    return tuple(
        WorldSnapshotLeaf(
            record_id=record.id,
            record_version=record.record_version,
            canonical_record_hash=canonical_record_hash(record),
        )
        for record in sorted(records, key=lambda item: (item.id, item.record_version))
    )


def snapshot_root(
    *,
    workspace_id: str,
    branch_id: str,
    lifecycle_scope: Iterable[str],
    leaves: Iterable[WorldSnapshotLeaf],
) -> str:
    """Versioned root over sorted leaves; shaped for a future Merkle implementation."""

    payload = {
        "version": 1,
        "workspace_id": workspace_id,
        "branch_id": branch_id,
        "lifecycle_scope": sorted(set(lifecycle_scope)),
        "leaves": [
            leaf.model_dump(mode="json") for leaf in sorted(leaves, key=lambda leaf: leaf.record_id)
        ],
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


__all__ = ["canonical_record_hash", "snapshot_leaves", "snapshot_root"]
