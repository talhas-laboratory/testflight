# TASK-005-implement-provider-neutral-operator-execution-an: Implement provider-neutral operator execution and routing

Status: done
Owner: talha
Current gate: implementation

## Problem

The current intelligence model port cannot execute general versioned operators with multimodal
capabilities, preflight routing and client packs.

## Scope

In:

- Create `packages/testflight-operator-runtime` contracts and execution coordinator.
- Implement capability manifests, routes, preflight, typed validation and receipts.
- Add fake and OpenAI-compatible provider adapters without provider imports in domain code.

Out:

- Creative transformation semantics, generation connectors and automatic promotion.

## Acceptance Criteria

- Providers are replaceable against the same operator fixtures.
- Failed preflight causes zero provider calls.
- Receipts contain redacted effective configuration and disclosure references.
- Semantic failures remain local and never use a deterministic semantic fallback.

## Plan

- Extract the smallest reusable provider seam from context intelligence.
- Route by operator, modality, policy, capability, budget and availability.
- Validate outputs before returning proposals.
- Test timeout, cancellation, retry/idempotency and provider mismatch.

## Verification Evidence

- `pnpm --filter @testflight/operator-runtime check` — TypeScript strict check passed.
- `pnpm --filter @testflight/operator-runtime test` — 7 tests passed (preflight zero-call, fake/provider replacement, idempotency, schema failure, OpenAI-compatible seam, retry and cancellation).
- Runtime receipt test confirms API credentials are redacted and disclosure references are carried.

## Updates

- Created: `2026-09-03T16:28:24.774832+00:00`
- 2026-09-03: added provider-neutral operator runtime package with capability preflight, typed output validation, policy routing, idempotent retries, cancellation/timeout handling and OpenAI-compatible/fake adapters.
- 2026-09-03: OpenAI-compatible routing now forwards an explicit `reasoning_effort` configuration;
  Luna can run with `modelId: gpt-5.6-luna` and `reasoning_effort: max` without changing domain code.

## Changed Files

- `packages/testflight-operator-runtime/package.json`
- `packages/testflight-operator-runtime/tsconfig.json`
- `packages/testflight-operator-runtime/tsconfig.build.json`
- `packages/testflight-operator-runtime/tsconfig.test.json`
- `packages/testflight-operator-runtime/src/contracts.ts`
- `packages/testflight-operator-runtime/src/providers.ts`
- `packages/testflight-operator-runtime/src/runtime.ts`
- `packages/testflight-operator-runtime/src/index.ts`
- `packages/testflight-operator-runtime/test/runtime.test.ts`
- `packages/testflight-operator-runtime/README.md`

## Residual Risks

- Provider adapters currently compile JSON payloads; modality-specific media upload and policy enforcement must be supplied by the application/connector boundary.
- Operator definitions are manually registered in TypeScript; a later loader can project validated YAML contracts without making YAML runtime state canonical.

## Handoff Notes

- Dependencies: TASK-001, TASK-004. Update `upstreams/registry.yaml` before new dependencies.
