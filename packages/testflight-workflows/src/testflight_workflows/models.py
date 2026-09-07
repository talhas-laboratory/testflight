"""Versioned provider-neutral workflow contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class WorkflowLifecycle(StrEnum):
    DRAFT = "draft"
    CANDIDATE = "candidate"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class StepKind(StrEnum):
    RETRIEVE = "retrieve"
    RESOLVE_ENTITIES = "resolve_entities"
    OPERATOR = "operator"
    TRANSFORM = "transform"
    ACTION = "action"
    LOOP = "loop"


class ErrorPolicy(StrEnum):
    FAIL = "fail"
    HOLD = "hold"
    CONTINUE = "continue"


class ResultStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    HOLD = "hold"
    FAILED = "failed"


class RunPhase(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"


class ConditionOperator(StrEnum):
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    TRUTHY = "truthy"
    FALSY = "falsy"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    CONTAINS = "contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"


class AgentAccess(ContractModel):
    """Who may discover and invoke a workflow."""

    public: bool = False
    agent_ids: tuple[str, ...] = ()
    roles: tuple[str, ...] = ()

    @model_validator(mode="after")
    def require_audience(self) -> AgentAccess:
        if not self.public and not self.agent_ids and not self.roles:
            raise ValueError("agent access must be public or name at least one agent or role")
        return self


class KnowledgeAccess(ContractModel):
    """Maximum knowledge visibility for the complete workflow run."""

    workspace_ids: tuple[str, ...] = Field(min_length=1)
    container_ids: tuple[str, ...] = ()
    entity_ids: tuple[str, ...] = ()
    entity_types: tuple[str, ...] = ()
    branch_ids: tuple[str, ...] = ()
    perspective_ids: tuple[str, ...] = ()
    data_classifications: tuple[str, ...] = ("internal",)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    max_results: int = Field(default=25, ge=1, le=100)
    max_graph_hops: int = Field(default=0, ge=0, le=2)
    allow_cross_workspace: bool = False

    @model_validator(mode="after")
    def valid_interval(self) -> KnowledgeAccess:
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValueError("knowledge valid_from must not be after valid_to")
        if len(self.workspace_ids) > 1 and not self.allow_cross_workspace:
            raise ValueError("multiple workspaces require allow_cross_workspace")
        return self


class WorkflowAuthority(ContractModel):
    """Authority automatically granted after workflow access succeeds."""

    capabilities: tuple[str, ...] = ()
    action_ids: tuple[str, ...] = ()
    credential_refs: tuple[str, ...] = ()
    proposal_write: bool = False
    canonical_write: bool = False
    external_action: bool = False


class StepAccess(ContractModel):
    """A step's subset of the workflow knowledge envelope."""

    workspace_ids: tuple[str, ...] = ()
    container_ids: tuple[str, ...] = ()
    entity_ids: tuple[str, ...] = ()
    entity_types: tuple[str, ...] = ()


class RetryPolicy(ContractModel):
    max_attempts: int = Field(default=1, ge=1, le=5)
    retry_on: tuple[str, ...] = ("transient", "timeout")
    backoff_seconds: float = Field(default=0, ge=0, le=60)


class PromptContract(ContractModel):
    """Versioned prompt and runtime route for one model-backed step."""

    id: str
    version: int = Field(ge=1)
    system: str = Field(min_length=1)
    user: str = Field(min_length=1)
    output_schema: dict[str, Any]
    operator_id: str = "runtime://testflight/workflow/prompt-step"
    operator_version: int = Field(default=1, ge=1)
    modality: str = "text/plain"
    configuration: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def reject_secret_configuration(self) -> PromptContract:
        secret_names = {"api_key", "apikey", "credential", "password", "secret", "token"}

        def visit(value: Any) -> bool:
            if isinstance(value, dict):
                return any(
                    str(key).lower() in secret_names or visit(item) for key, item in value.items()
                )
            if isinstance(value, list | tuple):
                return any(visit(item) for item in value)
            return False

        if visit(self.configuration):
            raise ValueError("prompt configuration may contain references, not secret values")
        return self


class StepInstruction(ContractModel):
    """Human-readable node behavior with an optional executable prompt."""

    id: str
    version: int = Field(ge=1)
    objective: str = Field(min_length=1)
    rules: tuple[str, ...] = ()
    prompt: PromptContract | None = None


class Condition(ContractModel):
    ref: str
    operator: ConditionOperator
    value: Any = None


class WorkflowStep(ContractModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    kind: StepKind
    handler: str
    description: str
    instruction: StepInstruction | None = None
    needs: tuple[str, ...] = ()
    arguments: dict[str, Any] = Field(default_factory=dict)
    when: tuple[Condition, ...] = ()
    access: StepAccess = Field(default_factory=StepAccess)
    capabilities: tuple[str, ...] = ()
    action_ids: tuple[str, ...] = ()
    timeout_seconds: float = Field(default=120, gt=0, le=3600)
    retry: RetryPolicy = Field(default_factory=RetryPolicy)
    on_error: ErrorPolicy = ErrorPolicy.FAIL
    idempotency_key: str | None = None
    foreach: str | None = None
    max_iterations: int | None = Field(default=None, ge=1, le=100)
    loop_concurrency: int = Field(default=1, ge=1, le=20)

    @model_validator(mode="after")
    def kind_requirements(self) -> WorkflowStep:
        if self.kind is StepKind.ACTION and not self.idempotency_key:
            raise ValueError(f"action step {self.id!r} requires idempotency_key")
        if self.kind is StepKind.LOOP and (not self.foreach or not self.max_iterations):
            raise ValueError(f"loop step {self.id!r} requires foreach and max_iterations")
        if self.kind is not StepKind.LOOP and (self.foreach or self.max_iterations):
            raise ValueError("foreach and max_iterations are only valid for loop steps")
        return self


class WorkflowDefinition(ContractModel):
    schema_version: int = Field(default=1, ge=1)
    id: str
    version: int = Field(ge=1)
    lifecycle: WorkflowLifecycle = WorkflowLifecycle.CANDIDATE
    name: str
    description: str
    tags: tuple[str, ...] = ()
    access: AgentAccess
    knowledge: KnowledgeAccess
    authority: WorkflowAuthority
    inputs_schema: dict[str, Any]
    outputs_schema: dict[str, Any]
    steps: tuple[WorkflowStep, ...] = Field(min_length=1)
    outputs: dict[str, Any]
    max_concurrency: int = Field(default=4, ge=1, le=20)
    run_timeout_seconds: float = Field(default=900, gt=0, le=86400)
    allow_dynamic_steps: bool = False

    @model_validator(mode="after")
    def fixed_graph_only(self) -> WorkflowDefinition:
        if self.allow_dynamic_steps:
            raise ValueError(
                "dynamic step injection is not supported; publish a new workflow version"
            )
        return self


class WorkflowPrincipal(ContractModel):
    id: str
    roles: tuple[str, ...] = ()


class WorkflowGrant(ContractModel):
    grant_id: str
    principal_id: str
    workflow_id: str
    workflow_version: int
    granted_at: datetime
    expires_at: datetime | None = None


class StepResult(ContractModel):
    status: ResultStatus
    output: Any = None
    error: str | None = None
    error_code: str | None = None
    receipt: dict[str, Any] = Field(default_factory=dict)


class StepReceipt(ContractModel):
    step_id: str
    handler: str
    status: ResultStatus
    attempts: int
    started_at: datetime
    finished_at: datetime
    idempotent_replay: bool = False
    error: str | None = None
    handler_receipt: dict[str, Any] = Field(default_factory=dict)


class WorkflowRunResult(ContractModel):
    run_id: str
    workflow_id: str
    workflow_version: int
    principal_id: str
    grant_id: str
    status: ResultStatus
    outputs: dict[str, Any] = Field(default_factory=dict)
    step_results: dict[str, StepResult] = Field(default_factory=dict)
    receipts: tuple[StepReceipt, ...] = ()
    errors: tuple[str, ...] = ()


class WorkflowRunRecord(ContractModel):
    run_id: str
    workflow_id: str
    workflow_version: int
    principal_id: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    phase: RunPhase
    created_at: datetime
    updated_at: datetime
    result: WorkflowRunResult | None = None


__all__ = [
    "AgentAccess",
    "Condition",
    "ConditionOperator",
    "ContractModel",
    "ErrorPolicy",
    "KnowledgeAccess",
    "ResultStatus",
    "RunPhase",
    "RetryPolicy",
    "PromptContract",
    "StepAccess",
    "StepInstruction",
    "StepKind",
    "StepReceipt",
    "StepResult",
    "WorkflowAuthority",
    "WorkflowDefinition",
    "WorkflowGrant",
    "WorkflowLifecycle",
    "WorkflowPrincipal",
    "WorkflowRunResult",
    "WorkflowRunRecord",
    "WorkflowStep",
]
