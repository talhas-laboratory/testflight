# TASK-001-record-the-concept-lab-v1-decision: Record the Concept Lab v1 decision

Status: done
Owner: codex
Current gate: implementation

## Problem

The approved Concept Lab boundary must become a durable product decision before implementation can
introduce new domain, workspace, operator, or skill modules.

Dependencies: none.

Required reading:

- `AGENT_INDEX.md`
- `docs/plans/2026-09-08-concept-lab-v1-implementation-plan.md`
- `workspaces/testflight-product/product-decisions/artifacts/module-contract.yaml`
- `workspaces/testflight-product/product-decisions/artifacts/decision-catalog.yaml`
- `docs/decisions/0003-brand-canonical-model-and-cognee-projection.md`
- `docs/decisions/0006-content-substrate-and-world-compilation.md`

## Scope

In:

- Add ADR 0007 recording the sovereign Lab, skill-first entry, explicit packet bridge, proposal-only
  formation, human promotion, and v1 deferrals.
- Register the decision in the existing product-decisions child and product parent registries.
- Record the Concept Lab product capability as `planned_v1` without claiming implementation.
- Update only the exact files listed below plus this board's state files.

Exact implementation files:

- `docs/decisions/0007-concept-lab-formation-workspace.md`
- `workspaces/testflight-product/product-decisions/artifacts/decision-catalog.yaml`
- `workspaces/testflight-product/product-decisions/artifacts/source_manifest.yaml`
- `workspaces/testflight-product/product-decisions/resource_registry.json`
- `workspaces/testflight-product/product-definition/artifacts/capability-inventory.yaml`
- `workspaces/testflight-product/product-definition/artifacts/source_manifest.yaml`
- `workspaces/testflight-product/product-definition/resource_registry.json`
- `workspaces/testflight-product/resource_registry.json`
- `workspaces/testflight-product/artifacts/registration-receipt.json`

Out:

- Domain contracts, workspace scaffolding, operators, skills, bridge instances, or runtime code.
- Reconsidering the fixed v1 decisions in the controlling plan.

## Acceptance Criteria

- ADR 0007 names ownership and both bridge directions.
- ADR distinguishes source, interpretation, theory, formation proposal, accepted product state, and
  runtime state.
- `decision-catalog.yaml` records `accepted_for_v1_implementation` with user authority and source.
- Capability inventory says `planned_v1`, with no implementation reference that does not exist.
- Product workspace validation passes and all new registry URLs resolve.

## Plan

- Claim the task and append an update.
- Write the ADR from the controlling plan; do not invent a broader platform promise.
- Update decision and capability records with proposal/implementation status precision.
- Register sources following existing metadata shapes.
- Run targeted product workspace validation, record results, and commit only this task.

Failure mode: an ADR or capability record implies that the Lab, skill, bridge, or runtime already
exists. If existing decision authority cannot represent the user's authorization, stop with
`hold` rather than inventing an authority grant.

Verification commands:

- `uv run python scripts/validate_testflight_product_workspace.py`
- `uv run python scripts/audit_testflight_product_routes.py --summary`
- `git diff --check`

## Verification Evidence

- Initial Product validation failed as expected after adding ADR 0007 to the product-definition
  source manifest without its matching registry record: `source manifest and registry differ:
  product-definition`. Root cause: the Product validator requires exact set equality between a child
  source manifest and its registry URLs. The matching ADR registry record has been added.
- The second Product validation run failed with `registration receipt registry hash mismatch:
  parent`. Root cause: the registration receipt stores byte-level hashes for each registry; the
  parent, product-definition, and product-decisions registries changed as part of this task. Their
- `uv run python scripts/validate_testflight_product_workspace.py` passed: 42 entities, 9 child
  modules, and 16 sources; no live projection changed.
- `uv run python scripts/audit_testflight_product_routes.py --summary` passed: 10/10 route
  checks, zero routing errors, and no live retrieval certification asserted.
- `git diff --check` passed.

## Updates

- Created: `2026-09-08T09:53:07.958094+00:00`
- Claimed: `2026-09-08T10:05:00Z` by codex.
- Completed: `2026-09-08T10:18:00Z` by codex.

## Handoff Notes

- TASK-002 is ready: it may define the domain-level contracts using ADR 0007 and the controlling
  plan. Do not make other tasks ready.
