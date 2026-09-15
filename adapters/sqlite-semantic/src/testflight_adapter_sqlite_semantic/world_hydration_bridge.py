"""One-shot canonical hydration bridge for graph-guided Context Compiler reads."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from testflight_world import WorldService

from .world_repository import SQLiteWorldRepository


def hydrate(request: dict[str, Any]) -> dict[str, Any]:
    operation = request.get("operation", "hydrate")
    database = request.get("worldDb")
    workspace_id = request.get("workspaceId")
    branch_id = request.get("branchId")
    snapshot_root = request.get("snapshotRoot")
    record_ids = request.get("recordIds")
    if not isinstance(database, str) or not database:
        raise ValueError("worldDb is required")
    if not isinstance(workspace_id, str) or not isinstance(branch_id, str):
        raise ValueError("workspaceId and branchId are required")
    with SQLiteWorldRepository(Path(database)) as repository:
        snapshot = WorldService(repository).snapshot(workspace_id, branch_id)
    if operation == "snapshot":
        return {"snapshotRoot": snapshot.snapshot_root, "records": []}
    if operation != "hydrate":
        raise ValueError("operation must be snapshot or hydrate")
    if not isinstance(snapshot_root, str) or len(snapshot_root) != 64:
        raise ValueError("snapshotRoot must be a canonical snapshot root")
    if not isinstance(record_ids, list) or any(not isinstance(value, str) for value in record_ids):
        raise ValueError("recordIds must be an array of strings")
    if snapshot.snapshot_root != snapshot_root:
        raise ValueError("canonical snapshot root no longer matches the requested projection")
    requested = set(record_ids)
    records = [
        record.model_dump(mode="json") for record in snapshot.records if record.id in requested
    ]
    return {"snapshotRoot": snapshot.snapshot_root, "records": records}


def main() -> int:
    try:
        request = json.loads(sys.stdin.read())
        if not isinstance(request, dict):
            raise ValueError("request must be an object")
        print(json.dumps(hydrate(request), ensure_ascii=False))
        return 0
    except Exception as error:  # noqa: BLE001 - JSON process boundary
        print(f"canonical hydration failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
