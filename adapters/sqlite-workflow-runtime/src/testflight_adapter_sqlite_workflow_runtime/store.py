"""Durable workflow runtime records backed by SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from testflight_workflows import StepResult, WorkflowRunRecord


class SqliteWorkflowRuntimeStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    run_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    workflow_version INTEGER NOT NULL,
                    principal_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS workflow_idempotency (
                    idempotency_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                );
                """
            )

    async def get_run(self, run_id: str) -> WorkflowRunRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM workflow_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
        return WorkflowRunRecord.model_validate_json(row[0]) if row else None

    async def put_run(self, record: WorkflowRunRecord) -> None:
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT workflow_id, workflow_version, principal_id FROM workflow_runs "
                "WHERE run_id = ?",
                (record.run_id,),
            ).fetchone()
            identity = (record.workflow_id, record.workflow_version, record.principal_id)
            if existing and tuple(existing) != identity:
                raise ValueError("run id is already bound to a different workflow or principal")
            connection.execute(
                """
                INSERT INTO workflow_runs
                    (
                        run_id, workflow_id, workflow_version, principal_id,
                        phase, payload, updated_at
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    phase = excluded.phase,
                    payload = excluded.payload,
                    updated_at = excluded.updated_at
                """,
                (
                    record.run_id,
                    record.workflow_id,
                    record.workflow_version,
                    record.principal_id,
                    record.phase.value,
                    record.model_dump_json(),
                    record.updated_at.isoformat(),
                ),
            )

    async def get(self, key: str) -> StepResult | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM workflow_idempotency WHERE idempotency_key = ?", (key,)
            ).fetchone()
        return StepResult.model_validate_json(row[0]) if row else None

    async def put(self, key: str, result: StepResult) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO workflow_idempotency "
                "(idempotency_key, payload) VALUES (?, ?)",
                (key, result.model_dump_json()),
            )


__all__ = ["SqliteWorkflowRuntimeStore"]
