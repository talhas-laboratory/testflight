# TASK-004-author-creative-operators-and-semantic-gold-fixt: Author creative operators and semantic gold fixtures

Status: done
Owner: talha
Current gate: implementation

## Problem

The creative transformations and quality criteria are described externally but are not yet
versioned Testflight operators or executable fixtures.

## Scope

In:

- Add eight creative-field operator contracts and registry entries.
- Add output schemas, hold behavior, guardrail composition and evaluator definitions.
- Create gold fixtures for intent, tension, outlier, translation, isolation, correction, no-hit,
  rights, authority and capability degradation.

Out:

- Provider runtime and live inference.

## Acceptance Criteria

- Operator validation passes and every output field has evidence/authority semantics.
- Gold fixtures distinguish schema validity from semantic correctness.
- Embedded instructions in imported content cannot change operator procedure.
- Missing evidence produces partial/held/no-hit rather than invented content.

## Plan

- Author fixtures before prompts or provider implementations.
- Define deterministic assertions and independent semantic rubrics.
- Register contracts in `reasoning/operators/index.yaml`.
- Extend reasoning operator validation and tests.

## Verification Evidence

- `uv run python scripts/validate_reasoning_operators.py` — 24 operators validated.
- `uv run pytest tests/test_reasoning_operators.py -q` — 4 passed.
- `uv run ruff check tests/test_reasoning_operators.py scripts/validate_reasoning_operators.py` — all checks passed.

## Updates

- Created: `2026-09-03T16:28:24.774614+00:00`
- 2026-09-03: added eight creative transformational/control operators and eleven semantic gold fixtures, including rights, authority, no-hit and embedded-instruction cases.

## Changed Files

- `reasoning/operators/index.yaml`
- `reasoning/operators/creative-observation-extraction.yaml`
- `reasoning/operators/creative-reference-interpretation.yaml`
- `reasoning/operators/creative-field-synthesis.yaml`
- `reasoning/operators/creative-review-versioning.yaml`
- `reasoning/operators/creative-project-binding.yaml`
- `reasoning/operators/creative-field-projection.yaml`
- `reasoning/operators/creative-connector-packet.yaml`
- `reasoning/operators/creative-output-evaluation.yaml`
- `reasoning/fixtures/creative-field/gold.yaml`
- `scripts/validate_reasoning_operators.py`
- `tests/test_reasoning_operators.py`

## Residual Risks

- These contracts are validated as portable YAML and fixtures; an executable operator runtime and provider-routing implementation remain pending.
- Semantic rubric evaluation remains fixture metadata until the dedicated operator runtime and evaluator adapters are implemented.

## Handoff Notes

- Dependencies: TASK-001, TASK-002. Client lenses are configuration unless procedure differs.
