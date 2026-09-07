# TASK-022-evaluate-output-and-persist-feedback-proposals: Evaluate output and persist feedback proposals

Status: done
Owner: talha
Current gate: done

## Problem

Generated output had a durable receipt but no application seam that could evaluate field fidelity,
exclusions, task fitness and execution quality without silently changing the accepted field.

## Scope

In:

- register the output-evaluation operator in the executable creative runtime pack;
- add an `evaluate_output` command that reconstructs the bounded request/field/projection/packet;
- send bounded output evidence to the provider-neutral `OperatorExecutor`;
- persist typed `CreativeEvaluation` and `FeedbackRecord` proposals and replay them by output ID;
- preserve evaluator receipts, disagreements and separate quality dimensions in state.

Out:

- automatic acceptance of feedback;
- mutation or replacement of an accepted `CreativeFieldVersion`;
- human feedback editor UI;
- calibration of a live provider's semantic rubric.

## Acceptance Criteria

- Evaluation requires a project-scoped generated output and all upstream packet records.
- The runtime validates the output-evaluation result shape before the domain workflow accepts it.
- Field fidelity, exclusions, task fitness and execution quality remain separate fields.
- Feedback is proposal-only, carries output/evaluation lineage, and survives restart/replay.
- Repeating evaluation for an output does not invoke the operator twice.
- Existing creative-field, runtime, connector and full release gates remain green.

## Verification Evidence

- `pnpm --filter @testflight/operator-runtime check` and `pnpm --filter @testflight/operator-runtime test` — TypeScript check and 11 runtime tests passed.
- `uv run pytest packages/testflight-creative-field/tests adapters/creative-connectors/tests apps/creative-studio/tests -q` — focused creative suite passed, including output evaluation, feedback lineage and replay.
- `make check` — passed: 134 Python tests, all TypeScript checks/tests, validators, certification
  and Compose validation. The environment reports a non-blocking Node 22 versus repository
  `>=24` engine warning.
- `git diff --check` and JSONL update validation — passed after board update.

## Changed Files

- `packages/testflight-creative-field/src/testflight_creative_field/evaluation.py`
- `packages/testflight-creative-field/src/testflight_creative_field/__init__.py`
- `packages/testflight-creative-field/src/testflight_creative_field/models.py`
- `packages/testflight-operator-runtime/src/creative.ts`
- `packages/testflight-operator-runtime/test/runtime.test.ts`
- `apps/creative-studio/src/testflight_creative_studio/server.py`
- `apps/creative-studio/tests/test_server.py`
- `docs/workboards/moodboard-creative-field-implementation/DECISIONS.md`

## Residual Risks

- Evaluation currently depends on an injected provider-neutral executor; no live evaluator provider
  or rubric calibration is enabled.
- Feedback remains proposal-only and has no UI promotion workflow.
- Client-specific operator packs and live Brand-world lookup remain explicit future inputs.

## Handoff Notes

Next, load the versioned YAML operator contracts and client-specific packs into the runtime, then
replace explicit world-view payloads with a bounded live Brand-world/context-intelligence resolver.
