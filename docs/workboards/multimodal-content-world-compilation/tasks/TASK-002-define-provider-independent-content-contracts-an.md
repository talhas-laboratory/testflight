# TASK-002-define-provider-independent-content-contracts-an: Define provider-independent Content contracts and package boundary

Status: done
Owner: codex
Current gate: done

## Problem

The accepted Content planes and certified fixture need immutable, provider-independent domain
contracts before processors, social interpretation, or platform adapters can be implemented.

## Scope

In:

- Add `packages/testflight-content` with immutable contracts for source, tracks, segments,
  observations, cross-modal relations, occurrences, pattern candidates, interpretation frames,
  transformation recipes, and derivation/evaluator receipts.
- Add validation for identity, anchors, time ranges, scope, epistemic status, and recurrence.
- Add package documentation, exports, workspace registration, and focused tests.

Out:

- Media decoding or model/provider integrations.
- Social-specific ontology and interpretations.
- World projection, persistence adapter, UI, or live acquisition.

## Acceptance Criteria

- Package imports no platform, provider, retrieval, persistence, or UI implementation.
- Models validate the certified fixture's invariants without copying fixture-specific semantics.
- Cross-record validation rejects unknown anchors and invalid independent recurrence.
- Public exports and package boundary are documented.
- Focused unit tests and repository registry checks pass.

## Plan

- Define minimal Pydantic models composed by stable IDs.
- Add a bundle-level validator for cross-record invariants.
- Add fixture-to-contract loading in tests.
- Register the workspace package without adding an external runtime dependency.
- Run focused tests, lint, registry validation, and diff checks.

## Verification Evidence

- Passed: `uv run ruff format --check packages/testflight-content/src packages/testflight-content/tests`.
- Passed: `uv run ruff check packages/testflight-content/src packages/testflight-content/tests`.
- Passed: `uv lock --check` — workspace lock resolves 164 packages.
- Passed: `uv run python scripts/validate_registry.py` — 3 pinned upstreams.
- Passed: `uv run python scripts/validate_multimodal_content_fixtures.py`.
- Passed: `uv run --all-packages pytest packages/testflight-content/tests/test_models.py -q` — 9 tests.
- Passed: `uv run --all-packages pytest tests/test_multimodal_content_fixtures.py -q` — 5 tests.
- Passed: `uv run --all-packages pytest` — 157 tests.
- Passed: targeted `git diff --check`.
- Changed artifacts: `packages/testflight-content/`, root `pyproject.toml`, `uv.lock` workspace
  membership, and TASK-002 board records.
- Residual risk: contracts use provider-neutral string timestamps and external blob references;
  byte-level media continuity and processor behavior belong to TASK-004.

## Updates

- Created: `2026-09-04T10:45:41.538895+00:00`
- Intake and readiness defined after Phase 0 certification: `2026-09-04T10:51:14Z`
- Implementation, verification, and done gate complete: `2026-09-04T11:02:00Z`

## Handoff Notes

- Complete. TASK-004 can implement deterministic processors against these contracts and fixtures.
- Claimed by codex: `2026-09-04T10:53:00Z`.
