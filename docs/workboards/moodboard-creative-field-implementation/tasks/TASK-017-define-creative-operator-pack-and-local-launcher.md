# TASK-017-define-creative-operator-pack-and-local-launcher: Define the creative operator pack and local launcher

Status: done
Owner: talha
Current gate: done

## Problem

The operator runtime transport existed, but the first Creative Field operators were not registered
as executable runtime capabilities and there was no documented, no-secret composition-root
launcher for a configured compatible provider.

## Scope

In:

- register observation, interpretation and synthesis operator IDs with conservative structural
  validators and multimodal capability declarations;
- expose a local launcher that configures one compatible provider, runtime policy and bounded HTTP
  transport from environment variables without importing credentials into tracked files;
- add build, health and missing-credential smoke coverage and document the local runtime contract.

Out:

- loading semantic procedure text from YAML into provider prompts;
- client-specific operator packs and live provider calls;
- Creative Studio analysis command, background jobs or human review/version promotion;
- public exposure or remote authentication for the local runtime endpoint.

## Acceptance Criteria

- The runtime exposes stable Creative Field operator IDs, accepted modalities and output gates.
- The launcher requires an explicit provider base URL and named credential environment variable,
  defaults to Luna with bounded retry/timeout policy, and never logs credential values.
- The local endpoint starts, answers `/health`, and remains private by default.
- Runtime package tests, launcher syntax/startup smoke, and the repository release gate pass.

## Verification Evidence

- `pnpm --filter @testflight/operator-runtime test` — 11 TypeScript tests passed, including the
  creative operator pack and HTTP transport.
- `node --check scripts/serve_operator_runtime.mjs` — passed.
- launcher smoke with a temporary sentinel API-key value, a dummy compatible base URL and port
  18781 — `/health` returned `{\"status\":\"ok\"}`; logs contained provider/model only and no
  credential.
- launcher missing configuration smoke — exits with `TESTFLIGHT_OPERATOR_BASE_URL is required`.
- `make check` — passed: 128 Python tests, all TypeScript checks/tests, validators, certification
  and Compose validation. The environment reports a non-blocking Node 22 versus repository
  `>=24` engine warning.

## Changed Files

- `packages/testflight-operator-runtime/src/creative.ts`
- `packages/testflight-operator-runtime/src/index.ts`
- `packages/testflight-operator-runtime/test/runtime.test.ts`
- `packages/testflight-operator-runtime/README.md`
- `scripts/serve_operator_runtime.mjs`
- `Makefile`
- `.env.example`
- `docs/workboards/moodboard-creative-field-implementation/DECISIONS.md`

## Residual Risks

- Structural validators intentionally do not replace the semantic YAML procedure/evaluator
  contracts; the next runtime increment must load or compile those contracts explicitly.
- The launcher is local and unauthenticated by design; process supervision and remote deployment
  policy remain composition-root work.
- No live model-provider call was made.

## Handoff Notes

The next increment should add a configured Creative Studio analysis command that creates a stable
run ID, constructs `HttpOperatorExecutor`, invokes `CreativeFieldRunCoordinator`, persists run
state and exposes proposal/review status without promoting proposals automatically.
