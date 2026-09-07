# TASK-002-create-the-creative-field-domain-package-and-ont: Create the creative-field domain package and ontology

Status: done
Owner: talha
Current gate: implementation

## Problem

Creative-domain objects currently have no canonical package or validated lifecycle contracts.

## Scope

In:

- Create `packages/testflight-creative-field` with Pydantic models and validators.
- Add project/board, interpretation, field, binding and runtime record families.
- Add a creative ontology module and extensible dimension registry.

Out:

- Provider calls, persistence implementation, Cognee projection and UI.

## Acceptance Criteria

- Models preserve project, context, authority, evidence and derivation.
- Accepted field versions are immutable and proposals are distinct types/statuses.
- Unknown dimensions round-trip without becoming actionable.
- Package has dependency-free tests and exports.

## Plan

- Implement record families in dependency order.
- Reuse semantic kernel types by reference rather than inheritance.
- Add validators for identity, scope, versions, relationships and review states.
- Add synthetic fixtures for one project and board.

## Verification Evidence

- `uv run --package testflight-creative-field pytest packages/testflight-creative-field/tests/test_models.py -q` — 5 passed.
- `uv run --package testflight-creative-field ruff check packages/testflight-creative-field` — all checks passed.
- `uv run --package testflight-creative-field python -c 'import testflight_creative_field as m; print(m.FieldDimension)'` — package import passed.
- `uv sync --all-groups` — workspace lock/install resolved with the new member.

## Updates

- Created: `2026-09-03T16:28:24.774374+00:00`
- 2026-09-03: claimed by talha after TASK-001 contract gate passed.
- 2026-09-03: implemented provider-neutral records, ontology manifest/dimensions, registry loader, workspace membership and tests.

## Changed Files

- `packages/testflight-creative-field/pyproject.toml`
- `packages/testflight-creative-field/src/testflight_creative_field/models.py`
- `packages/testflight-creative-field/src/testflight_creative_field/registry.py`
- `packages/testflight-creative-field/src/testflight_creative_field/__init__.py`
- `packages/testflight-creative-field/tests/test_models.py`
- `packages/testflight-creative-field/README.md`
- `domains/creative-field/manifest.yaml`
- `domains/creative-field/dimensions.yaml`
- `pyproject.toml`

## Residual Risks

- The domain records are intentionally persistence-neutral; storage, operator execution and projection gates are still pending.
- Cross-record authority and scope checks will be enforced at application/service boundaries once repositories and workflows exist.

## Handoff Notes

- Dependencies: TASK-001. Do not place creative-domain meaning in `testflight-semantic`.
