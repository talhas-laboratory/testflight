# TASK-021-invoke-target-and-persist-output-receipt: Invoke a target and persist output receipt

Status: done
Owner: talha
Current gate: done

## Problem

Creative Studio could compile a target-specific `GenerationPacket`, but had no bounded seam for an
authorized target call or durable generated-output receipt.

## Scope

In:

- add canonical `InvocationReceipt` and `CreativeOutput` records;
- add an authority-gated `invoke_generation` command using target adapters registered by target ID;
- normalize text/binary output into the content-addressed blob store and persist output metadata;
- make invocation IDs idempotent and hydrate the latest invocation after restart;
- expose project-scoped generated-output retrieval through the existing HTTP server;
- preserve target failures as failed/held receipts without mutating the Creative Field.

Out:

- live provider SDKs or credentials;
- automatic target selection;
- model-based output evaluation and feedback routing;
- a rich projection/generation UI.

## Acceptance Criteria

- A prepared packet cannot invoke without an authority grant, a configured adapter, and output
  storage.
- A successful text/image adapter call stores normalized output bytes and an immutable receipt with
  packet, disclosure, capability, grounding and authority metadata.
- Repeating an invocation ID replays the persisted receipt without a second adapter call.
- Adapter/provider failure is represented as a failed receipt with no fabricated output.
- Output retrieval is project-scoped and restart hydration preserves the invocation state.
- Existing creative-field, connector and full release gates remain green.

## Verification Evidence

- `uv run pytest packages/testflight-creative-field/tests adapters/creative-connectors/tests apps/creative-studio/tests -q` — focused creative suite passed.
- `make check` — passed: 134 Python tests, all TypeScript checks/tests, validators, certification
  and Compose validation. The environment reports a non-blocking Node 22 versus repository
  `>=24` engine warning.
- `git diff --check` and JSONL update validation — passed after board update.

## Changed Files

- `packages/testflight-creative-field/src/testflight_creative_field/models.py`
- `adapters/sqlite-semantic/src/testflight_adapter_sqlite_semantic/creative_repository.py`
- `apps/creative-studio/src/testflight_creative_studio/server.py`
- `apps/creative-studio/tests/test_server.py`
- `apps/creative-studio/README.md`
- `packages/testflight-creative-field/README.md`

## Residual Risks

- Target adapters are currently injected callables around local text/image adapters; no live
  provider integration is enabled.
- Output evaluation and feedback-driven selective invalidation remain the next semantic loop.
- Client-specific operator packs and live Brand-world lookup are still explicit inputs.

## Handoff Notes

Next, add a bounded output-evaluation command that invokes the existing evaluation operator,
persists `CreativeEvaluation`/`FeedbackRecord` proposals, and never mutates the accepted field.
