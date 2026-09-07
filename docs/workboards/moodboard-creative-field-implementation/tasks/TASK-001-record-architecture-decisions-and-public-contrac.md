# TASK-001-record-architecture-decisions-and-public-contrac: Record architecture decisions and public contracts

Status: ready
Owner: talha
Current gate: done

## Problem

The approved external profile must become an explicit Testflight ADR and versioned public handoff
schemas before implementation begins.

## Scope

In:

- Add the Testflight ADR and contract inventory.
- Resolve ownership, statuses, package boundaries and compatibility policy.

Out:

- Implement domain models, storage, operators, adapters or UI.

## Acceptance Criteria

- ADR records the three-object separation and application-profile boundary.
- Every canonical object has one lifecycle owner and proposal producer.
- Contracts from `BoardSnapshot@1` through `CreativeEvaluation@1` have schemas and statuses.
- Open provider, licensing, UI and threshold decisions remain explicit.

## Plan

- Read the implementation plan and approved system design.
- Add `docs/decisions/0005-moodboard-creative-field-profile.md`.
- Add a machine-readable contract inventory for downstream tasks.

## Verification Evidence

- `uv run python -c '...yaml.safe_load(...)...'` — passed; 14 contracts parsed.
- `uv run python scripts/validate_reasoning_operators.py` — passed; 16 operators validated.
- `uv run pytest tests/test_reasoning_operators.py -q` — passed; 2 tests.
- trailing-whitespace scan over changed task/ADR/contract files — passed.
- Residual risk: concrete Pydantic/TypeScript implementations and provider choices remain in later tasks.

## Updates

- Created: `2026-09-03T16:28:24.774248+00:00`
- 2026-09-03: claimed by talha; implementation started.
- 2026-09-03: ADR and contract inventory added; targeted validation passed; task closed.

## Handoff Notes

- Changed files: `docs/decisions/0005-moodboard-creative-field-profile.md`,
  `docs/contracts/creative-field-contracts.yaml`, board state files.
- Done gate satisfied; downstream tasks may use the contract inventory.
