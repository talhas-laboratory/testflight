# TASK-006-build-reference-observation-and-interpretation-w: Build reference observation and interpretation workflow

Status: done
Owner: talha
Current gate: implementation

## Problem

The system cannot yet turn bounded image/text evidence into reviewable observations and
project-specific reference roles.

## Scope

In:

- Implement `observe-reference` and `interpret-reference-role` application workflows.
- Preserve media anchors, alternatives, carry-forward and anti-transfer proposals.
- Compose project purpose, local board context and permitted Brand-world context.

Out:

- Cross-board synthesis, automatic acceptance and additional modalities.

## Acceptance Criteria

- Every observation has an exact evidence anchor.
- Interpretation separates visible content from project meaning.
- High-impact ambiguity produces alternatives or one discriminating question.
- Provider failure retains the board and returns a typed non-success result.

## Plan

- Build deterministic preparation and bounded context assembly.
- Execute operators through the provider-neutral runtime.
- Validate and persist proposal/receipt pairs.
- Add intent, rights, prompt-injection and failure fixtures.

## Verification Evidence

- `uv run --package testflight-creative-field pytest packages/testflight-creative-field/tests/test_models.py packages/testflight-creative-field/tests/test_workflows.py -q` — 9 passed.
- `uv run ruff check packages/testflight-creative-field` — all checks passed.
- Workflow tests cover exact anchors, untrusted annotations, rights holds, provider failure, alternatives and proposal-only interpretation.

## Updates

- Created: `2026-09-03T16:28:24.775048+00:00`
- 2026-09-03: implemented bounded observation and interpretation workflow seams with typed proposal validation and explicit non-success outcomes.

## Changed Files

- `packages/testflight-creative-field/src/testflight_creative_field/workflows.py`
- `packages/testflight-creative-field/src/testflight_creative_field/__init__.py`
- `packages/testflight-creative-field/tests/test_workflows.py`

## Residual Risks

- The Python executor seam needs a production JSON bridge to the TypeScript operator runtime; fake executors cover this boundary until that bridge is added.
- Cross-modal media decoding and exact image/audio/video region extraction remain adapter responsibilities.

## Handoff Notes

- Dependencies: TASK-003, TASK-004, TASK-005.
