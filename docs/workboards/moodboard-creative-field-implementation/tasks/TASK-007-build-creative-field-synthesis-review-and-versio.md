# TASK-007-build-creative-field-synthesis-review-and-versio: Build Creative Field synthesis review and version lifecycle

Status: done
Owner: talha
Current gate: implementation

## Problem

Reference interpretations cannot yet become a coherent, reviewable and immutable project field.

## Scope

In:

- Implement comparison and field-synthesis workflows.
- Add review decisions, semantic diffs, immutable versions, branches and targeted staleness.
- Preserve dominant/secondary patterns, roles, outliers, tensions, conflicts, exclusions and gaps.

Out:

- Field mixing UI, artifact projection and provider connectors.

## Acceptance Criteria

- Synthesis never averages away tensions or outliers.
- Approval creates a new immutable version and activation remains separate.
- Corrections invalidate exactly affected dependents.
- Field reconstruction and version diff are deterministic.

## Plan

- Execute compare/synthesize operators over eligible contributions.
- Run grounding and semantic-quality gates.
- Implement review and version commands with optimistic concurrency.
- Add reconstruction, branch and correction tests.

## Verification Evidence

- `uv run --package testflight-creative-field pytest packages/testflight-creative-field/tests -q` — 12 passed.
- `uv run ruff check packages/testflight-creative-field` — all checks passed.
- Lifecycle tests cover tension preservation, lineage, deterministic diffing, authority-gated immutable versions, correction successors and selective dependent staleness.

## Updates

- Created: `2026-09-03T16:28:24.775147+00:00`
- 2026-09-03: implemented Creative Field synthesis, review/version lifecycle, deterministic reconstruction/diff and selective dependent staleness helper.

## Changed Files

- `packages/testflight-creative-field/src/testflight_creative_field/lifecycle.py`
- `packages/testflight-creative-field/src/testflight_creative_field/__init__.py`
- `packages/testflight-creative-field/tests/test_lifecycle.py`

## Residual Risks

- Version persistence and optimistic review concurrency still rely on the SQLite adapter integration; this task only builds the deterministic lifecycle service.
- Semantic quality remains evaluator/provider driven; local code validates structure, lineage and explicit lifecycle gates.

## Handoff Notes

- Dependencies: TASK-002, TASK-004, TASK-006.
