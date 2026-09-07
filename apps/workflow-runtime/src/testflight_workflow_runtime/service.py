"""Shared workflow runtime application service."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from testflight_workflows import (
    ResultStatus,
    RunPhase,
    WorkflowCatalog,
    WorkflowEngine,
    WorkflowPrincipal,
    WorkflowRunRecord,
    WorkflowRunResult,
    WorkflowRunStore,
)


class WorkflowRuntimeService:
    def __init__(
        self, *, catalog: WorkflowCatalog, engine: WorkflowEngine, run_store: WorkflowRunStore
    ) -> None:
        self.catalog = catalog
        self.engine = engine
        self.run_store = run_store
        self._tasks: dict[str, asyncio.Task[WorkflowRunRecord]] = {}

    def discover(self, principal: WorkflowPrincipal) -> tuple[dict[str, Any], ...]:
        return self.catalog.discover(principal)

    async def start_run(
        self,
        *,
        principal: WorkflowPrincipal,
        workflow_id: str,
        workflow_version: int,
        run_id: str,
        inputs: Mapping[str, Any],
    ) -> WorkflowRunRecord:
        workflow = self.catalog.get(principal, workflow_id, workflow_version)
        if workflow is None:
            raise ValueError("workflow is unavailable or access is denied")
        input_errors = self.engine.validator.validate(inputs, workflow.inputs_schema)
        if input_errors:
            raise ValueError("; ".join(input_errors))
        existing = await self.run_store.get_run(run_id)
        if existing:
            if (
                existing.principal_id != principal.id
                or existing.workflow_id != workflow_id
                or existing.workflow_version != workflow_version
                or existing.inputs != dict(inputs)
            ):
                raise ValueError("run id is already bound to another invocation")
            return existing
        now = datetime.now(UTC)
        record = WorkflowRunRecord(
            run_id=run_id,
            workflow_id=workflow_id,
            workflow_version=workflow_version,
            principal_id=principal.id,
            inputs=dict(inputs),
            phase=RunPhase.QUEUED,
            created_at=now,
            updated_at=now,
        )
        await self.run_store.put_run(record)
        task = asyncio.create_task(self._execute(record, principal))
        self._tasks[run_id] = task
        task.add_done_callback(lambda _task: self._tasks.pop(run_id, None))
        return record

    async def run_and_wait(
        self,
        *,
        principal: WorkflowPrincipal,
        workflow_id: str,
        workflow_version: int,
        run_id: str,
        inputs: Mapping[str, Any],
    ) -> WorkflowRunRecord:
        record = await self.start_run(
            principal=principal,
            workflow_id=workflow_id,
            workflow_version=workflow_version,
            run_id=run_id,
            inputs=inputs,
        )
        if record.phase is RunPhase.COMPLETED:
            return record
        task = self._tasks.get(run_id)
        if task is None:
            task = asyncio.create_task(self._execute(record, principal))
            self._tasks[run_id] = task
            task.add_done_callback(lambda _task: self._tasks.pop(run_id, None))
        return await task

    async def get_run(self, principal: WorkflowPrincipal, run_id: str) -> WorkflowRunRecord | None:
        record = await self.run_store.get_run(run_id)
        return record if record and record.principal_id == principal.id else None

    async def _execute(
        self, record: WorkflowRunRecord, principal: WorkflowPrincipal
    ) -> WorkflowRunRecord:
        running = record.model_copy(
            update={"phase": RunPhase.RUNNING, "updated_at": datetime.now(UTC)}
        )
        await self.run_store.put_run(running)
        try:
            result = await self.engine.execute(
                principal=principal,
                workflow_id=record.workflow_id,
                workflow_version=record.workflow_version,
                run_id=record.run_id,
                inputs=record.inputs,
            )
        except Exception as error:  # noqa: BLE001 - normalize composition boundary failures.
            result = WorkflowRunResult(
                run_id=record.run_id,
                workflow_id=record.workflow_id,
                workflow_version=record.workflow_version,
                principal_id=record.principal_id,
                grant_id=f"grant:{record.run_id}",
                status=ResultStatus.FAILED,
                errors=(str(error),),
            )
        completed = running.model_copy(
            update={
                "phase": RunPhase.COMPLETED,
                "updated_at": datetime.now(UTC),
                "result": result,
            }
        )
        await self.run_store.put_run(completed)
        return completed


__all__ = ["WorkflowRuntimeService"]
