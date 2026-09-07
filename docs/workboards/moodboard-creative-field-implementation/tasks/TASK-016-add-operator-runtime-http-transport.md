# TASK-016-add-operator-runtime-http-transport: Add operator-runtime HTTP transport

Status: done
Owner: talha
Current gate: done

## Problem

The Creative Field coordinator had a Python executor seam, but Creative Studio had no transport to
the existing TypeScript operator runtime and its provider routing/receipts.

## Scope

In:

- expose the TypeScript runtime through bounded local `POST /execute` and `GET /health` endpoints;
- normalize invocation and receipt fields across the Python/TypeScript boundary;
- enforce required scope, disclosure references, operator identity/version and body bounds;
- add a Python `HttpOperatorExecutor` with transport-only behavior;
- test output, scope, receipt, health, malformed input and size-limit behavior.

Out:

- provider credentials/configuration and operator-definition loading;
- process supervision, authentication and public network exposure;
- Creative Studio analysis command or background job persistence;
- live model-provider calls.

## Acceptance Criteria

- A valid invocation reaches `OperatorRuntime` and returns its typed outcome and redacted receipt.
- The Python adapter emits the runtime's expected context and disclosure fields without provider
  imports.
- Invalid scope/disclosure/body input is rejected before provider execution.
- Runtime health and transport failures are observable and do not become semantic fallbacks.
- Existing runtime and repository release checks remain green.

## Verification Evidence

- `pnpm --filter @testflight/operator-runtime test` — 10 TypeScript tests passed, including runtime
  HTTP scope/output/receipt, health and body-limit tests.
- `uv run pytest apps/creative-studio/tests/test_operator_http.py packages/testflight-creative-field/tests/test_orchestration.py -q` — 7 Python tests passed.
- `uv run ruff format --check apps/creative-studio packages/testflight-creative-field` — passed.
- `uv run ruff check apps/creative-studio packages/testflight-creative-field` — passed.
- `make check` — passed: 128 Python tests, all TypeScript checks/tests, validators, certification
  and Compose validation. The environment reports a non-blocking Node 22 versus repository
  `>=24` engine warning.

## Changed Files

- `packages/testflight-operator-runtime/src/http.ts`
- `packages/testflight-operator-runtime/src/index.ts`
- `packages/testflight-operator-runtime/test/runtime.test.ts`
- `packages/testflight-operator-runtime/README.md`
- `apps/creative-studio/src/testflight_creative_studio/operator_http.py`
- `apps/creative-studio/src/testflight_creative_studio/__init__.py`
- `apps/creative-studio/tests/test_operator_http.py`
- `docs/workboards/moodboard-creative-field-implementation/DECISIONS.md`

## Residual Risks

- The runtime has no production launcher or operator-definition loader yet.
- The endpoint is intentionally local and unauthenticated; the next composition-root task must
  keep it off public interfaces and add supervision/authentication if deployed remotely.
- No live model-provider call was made.

## Handoff Notes

The next increment should load the versioned YAML operator contracts into runtime definitions,
configure a capability manifest/provider pack, and expose an idempotent Creative Studio analysis
command that invokes `CreativeFieldRunCoordinator` through this adapter.
