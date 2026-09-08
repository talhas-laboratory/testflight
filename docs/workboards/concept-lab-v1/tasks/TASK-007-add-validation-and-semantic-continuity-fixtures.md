# TASK-007-add-validation-and-semantic-continuity-fixtures: Add validation and semantic continuity fixtures

Status: done
Owner: codex
Current gate: implementation

## Problem

Structural validation alone cannot prove that meaning, branch identity, evidence, authority, and
reverse trace survive the full Concept Lab transformation chain.

Dependencies: TASK-002, TASK-003, TASK-004, TASK-005, and TASK-006.

Required reading:

- All implemented Concept Lab contracts, workspace files, bridge records, operators, and skill.
- Existing child-container, operator, skill-catalog, Product-workspace, and federation tests.
- `reasoning/operators/evaluation-schema.yaml`.

## Scope

In:

- Add a deterministic Concept Lab validator for identity, refs, lifecycle, bridge, formation, and
  reverse-trace invariants.
- Add provider-free fixtures for supported, ambiguous, missing-source, unauthorized-bridge,
  out-of-domain, and broken-reverse-trace cases.
- Test semantic continuity separately from schema parsing.
- Test skill mode routing by observable selected mode/output contract, not exact prose.

Expected implementation paths:

- `scripts/validate_concept_lab.py`
- `tests/test_concept_lab.py`
- `reasoning/fixtures/concept-lab/`
- No package changes; the v1 validator consumes canonical YAML/JSON files directly.

Out:

- Live model evaluation, prompt snapshot tests, embedding retrieval, external stores, or subjective
  scoring presented as certification.

## Acceptance Criteria

- Supported fixture completes source → theory → formation → reverse trace with all IDs resolvable.
- Ambiguous fixture retains at least two branches.
- Missing source and unauthorized bridge fixtures return typed failures.
- Product target routing rejects unknown modules.
- Schema, invariants, semantics, usefulness, and residual risks are separate results.
- Targeted tests and existing repository checks pass.

## Plan

- Claim after all dependencies are done.
- Write fixtures before validator logic to fix expected behavior.
- Implement deterministic checks without reproducing domain reasoning.
- Add one failure at a time and prove the validator diagnoses it.
- Record test output and commit one task.

Failure mode: tests assert wording or let the producer's own `pass` flag count as validation.

Verification commands:

- `uv run python scripts/validate_concept_lab.py`
- `uv run pytest tests/test_concept_lab.py -q`
- existing operator, federation, child-container, and skill-catalog tests
- `git diff --check`

## Verification Evidence

- `uv run python scripts/validate_concept_lab.py` passed: five continuity cases.
- `uv run pytest tests/test_concept_lab.py -q` passed.

## Updates

- Created: `2026-09-08T09:53:07.959342+00:00`
- Claimed: `2026-09-08T11:22:00Z` by codex.
- Completed: `2026-09-08T11:28:00Z` by codex.

## Handoff Notes

- On completion, make TASK-008 ready.
