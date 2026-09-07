import asyncio
from datetime import UTC, datetime

from testflight_adapter_sqlite_workflow_runtime import (
    SqliteWorkflowRuntimeStore,
    descriptor,
    health_probe,
)
from testflight_core import Capability, HealthState
from testflight_workflows import (
    ResultStatus,
    RunPhase,
    StepResult,
    WorkflowRunRecord,
)


def test_store_persists_runs_and_idempotency(tmp_path):
    store = SqliteWorkflowRuntimeStore(tmp_path / "runtime.sqlite3")
    now = datetime.now(UTC)
    record = WorkflowRunRecord(
        run_id="run:one",
        workflow_id="workflow://example",
        workflow_version=1,
        principal_id="agent:one",
        phase=RunPhase.QUEUED,
        created_at=now,
        updated_at=now,
    )

    async def exercise():
        await store.put_run(record)
        assert await store.get_run("run:one") == record

        result = StepResult(status=ResultStatus.SUCCESS, output={"ok": True})
        await store.put("key:one", result)
        await store.put("key:one", StepResult(status=ResultStatus.FAILED))
        assert await store.get("key:one") == result

    asyncio.run(exercise())


def test_adapter_descriptor_and_health_probe():
    assert descriptor.capabilities == {Capability.MEMORY}
    assert health_probe().state is HealthState.AVAILABLE
