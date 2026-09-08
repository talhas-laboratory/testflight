# TASK-005-add-concept-lab-transformation-operators: Add Concept Lab transformation operators

Status: backlog
Owner: unassigned
Current gate: intake

## Problem

Codex needs inspectable, reusable transformations between source material, theory, technical
formation, and reverse explanation rather than relying on an informal prompt posture.

Dependencies: TASK-002.

Required reading:

- Controlling plan and Concept Lab contracts.
- `reasoning/README.md`, `reasoning/operator-contract.yaml`, and `reasoning/operators/index.yaml`.
- Existing `creative-observation-extraction`, `creative-field-synthesis`,
  `ontology-conflation`, `boundary-conflation`, and `evaluation-schema` operators.

## Scope

In:

- Add `concept-extraction@1`, `theory-synthesis@1`, `formation-projection@1`, and
  `formation-trace@1` as portable transformational operators.
- Register a Concept Lab route in the operator catalog.
- Compose existing guardrails rather than repeating them inside each operator.
- Declare inputs, context, procedures, return types, invariants, forbidden shortcuts, hold states,
  failure modes, and independent evaluators.

Exact implementation files:

- `reasoning/operators/concept-extraction.yaml`
- `reasoning/operators/theory-synthesis.yaml`
- `reasoning/operators/formation-projection.yaml`
- `reasoning/operators/formation-trace.yaml`
- `reasoning/operators/index.yaml`
- Existing operator catalog tests only where registration assertions require updates.

Out:

- Provider prompts, runtime execution definitions, workflow YAML, persistence, or domain-specific
  Biotic content.

## Acceptance Criteria

- All operators validate against the portable contract.
- Forward operators preserve source anchors, branch identity, abstraction, and uncertainty.
- Formation requires an explicit selected branch and target; otherwise returns `ask` or `hold`.
- Trace reports missing edges and never reconstructs unsupported theory.
- Each operator separates schema, invariants, semantics, and usefulness evaluators.

## Plan

- Claim after TASK-002 is done.
- Draft one operator at a time and validate before continuing.
- Keep procedures observable and implementation-neutral.
- Register the smallest coherent composition route.
- Run operator tests and commit one task.

Failure mode: an operator converts a plausible interpretation into fact, flattens branches, or
claims a reversible trace that source IDs cannot support.

Verification commands:

- `uv run python scripts/validate_reasoning_operators.py`
- `uv run pytest tests/test_reasoning_operators.py -q`
- `git diff --check`

## Verification Evidence

- Not run yet.

## Updates

- Created: `2026-09-08T09:53:07.958983+00:00`

## Handoff Notes

- On completion, make TASK-006 ready if TASK-003 is also done.
