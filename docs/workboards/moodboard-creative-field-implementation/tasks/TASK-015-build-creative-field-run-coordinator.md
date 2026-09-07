# TASK-015-build-creative-field-run-coordinator: Build the Creative Field run coordinator

Status: done
Owner: talha
Current gate: done

## Problem

The typed observation, interpretation, and synthesis workflows exist independently, but no
provider-neutral component composes them from a persisted board revision into durable proposals.

## Scope

In:

- add a synchronous `CreativeFieldRunCoordinator` to the creative-domain package;
- load the latest project-scoped board, references, licenses, annotations, and dimensions;
- run observation, interpretation, and field synthesis through `OperatorExecutor`;
- persist typed proposal records and preserve per-stage receipts and non-success outcomes;
- prevent cross-project records, missing rights, missing references, and empty boards from reaching
  semantic operators;
- add fake-executor integration tests.

Out:

- HTTP job endpoints, background queue, or websocket progress;
- TypeScript runtime transport and live model-provider calls;
- human review/versioning UI and Brand-world artifact execution;
- automatic promotion of any proposal to canonical accepted meaning.

## Acceptance Criteria

- A valid board produces persisted `ObservedFeature`, `ReferenceInterpretation`,
  `ReferenceContribution`, and `CreativeFieldProposal` records.
- Every operator request includes project scope, evidence/disclosure references, and an operation
  key derived from the run.
- A held or failed stage produces no fabricated downstream records and retains its receipt.
- Missing source rights, missing assets, empty boards, and foreign-project boards are held before
  provider execution.
- The coordinator remains usable with a fake executor and a repository adapter without importing a
  provider SDK.

## Plan

- Define the coordinator result and stage outcome structures.
- Implement latest-board loading and typed record persistence.
- Add success, rights hold, provider failure, and scope-isolation tests.
- Run package tests, lint, and the repository release gate.

## Verification Evidence

- `uv run pytest packages/testflight-creative-field/tests/test_orchestration.py -q` — 5 passed.
- `uv run pytest packages/testflight-creative-field/tests -q -rA` — 25 passed, including existing
  lifecycle, projection, binding, workflow and evaluation cases.
- `uv run ruff format --check packages/testflight-creative-field/src packages/testflight-creative-field/tests/test_orchestration.py` — passed.
- `uv run ruff check packages/testflight-creative-field/src packages/testflight-creative-field/tests/test_orchestration.py` — passed.
- `make check` — passed: 126 Python tests, all TypeScript checks/tests, validators, certification
  and Compose validation. The environment reports a non-blocking Node 22 versus repository
  `>=24` engine warning.

The success fixture verified five ordered operator calls over a two-reference board, project scope
and disclosure references on every request, and durable typed observation, interpretation,
contribution and field-proposal records. Rights, foreign-project, empty-board and provider-failure
fixtures verified preflight holds, no fabricated downstream records and receipt preservation.

## Changed Files

- `packages/testflight-creative-field/src/testflight_creative_field/orchestration.py`
- `packages/testflight-creative-field/src/testflight_creative_field/ports.py`
- `packages/testflight-creative-field/src/testflight_creative_field/__init__.py`
- `packages/testflight-creative-field/src/testflight_creative_field/README.md`
- `packages/testflight-creative-field/tests/test_orchestration.py`
- `docs/workboards/moodboard-creative-field-implementation/DECISIONS.md`

## Residual Risks

- Run state is synchronous and not yet durable as a separate job record; retries and progress API
  belong to the next increment.
- The operator executor is still a Python seam; no live TypeScript runtime or provider is invoked.

## Handoff Notes

The next increment should implement the Python adapter to a local TypeScript operator-runtime
service and expose an idempotent Creative Studio analysis command. This coordinator is the stable
domain seam for that transport; it must remain free of provider SDK imports.
