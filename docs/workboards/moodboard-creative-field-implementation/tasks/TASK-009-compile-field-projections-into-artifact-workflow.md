# TASK-009-compile-field-projections-into-artifact-workflow: Compile field projections into artifact workflows

Status: done
Owner: talha
Current gate: implementation

## Problem

Artifact operators need one bounded packet that joins Brand-world facts with project-specific
creative meaning while preserving their different authority and provenance.

## Scope

In:

- Implement `CreativeRequest`, request resolution, `FieldProjection` and `CreativeContextPacket`.
- Compose exact `ResolvedWorldView`, applicable visual language and field projection.
- Add text/image lens mappings, local overrides, omissions and sufficiency results.

Out:

- Provider-specific generation syntax and canonical field mutation.

## Acceptance Criteria

- Identical resolved inputs produce identical projections and receipts.
- World claims and creative principles retain separate evidence/authority.
- Text and image projections preserve deep principles without literal copying.
- Packets are bounded, permission-filtered and reject scope mismatch.

## Plan

- Extend context-intelligence contracts without putting field synthesis in that package.
- Resolve world and field independently, then compose under policy.
- Implement `project-field` and packet validation.
- Add partial/no-hit, budget, override and staleness behavior.

## Verification Evidence

- `uv run --package testflight-creative-field pytest packages/testflight-creative-field/tests -q` — 18 passed.
- `uv run ruff check packages/testflight-creative-field` — all checks passed.
- Projection tests cover field/request resolution, world-view composition, visual-language linkage, target modality rejection, unsupported-dimension omissions and disclosure requirements.

## Updates

- Created: `2026-09-03T16:28:24.775344+00:00`
- 2026-09-03: implemented request resolution, target-specific FieldProjection and CreativeContextPacket composition with explicit omissions, conflicts, grounding and disclosure receipt.

## Changed Files

- `packages/testflight-creative-field/src/testflight_creative_field/projection.py`
- `packages/testflight-creative-field/src/testflight_creative_field/__init__.py`
- `packages/testflight-creative-field/tests/test_projection.py`

## Residual Risks

- The compiler consumes a mapping-shaped world-view result; the existing TypeScript/Python world-view bridge still needs a production adapter and end-to-end integration.
- Target capability manifests currently describe dimension limitations declaratively; provider-specific control translation is the connector task.

## Handoff Notes

- Dependencies: TASK-004, TASK-005, TASK-008.
