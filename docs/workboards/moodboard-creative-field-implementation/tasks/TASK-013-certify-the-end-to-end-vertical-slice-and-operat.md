# TASK-013-certify-the-end-to-end-vertical-slice-and-operat: Certify the end-to-end vertical slice and operations

Status: review
Owner: talha
Current gate: review

## Problem

The feature is not complete until technical, semantic, governance, operational and user-outcome
claims are verified together.

## Scope

In:

- Add workspace validation, certification command, operational setup and end-to-end fixtures.
- Run all contract, replay, operator, integration, adapter, browser and leakage tests.
- Document deployment, backups, rebuilds, provider failure and rollback.
- Execute the comparative product-value experiment when a real project is available.

Out:

- Expansion to additional modalities, collaboration, mobile and field mixing.

## Acceptance Criteria

- All program release gates have recorded evidence.
- The full source-to-artifact-to-feedback trace is reconstructable.
- Cognee and derived caches rebuild from canonical data.
- Home-server deployment passes dependency-free health and bounded live smoke tests.
- `make check` passes and residual risks are documented.

## Plan

- Add validation/certification scripts and Make targets.
- Run synthetic end-to-end scenario before live provider smoke tests.
- Verify local data paths, redaction, backup and recovery.
- Record product experiment protocol/results separately from technical pass status.

## Verification Evidence

- `uv run --all-packages python scripts/certify_creative_field.py` — passed; board replay,
  observation/interpretation/synthesis, authority-gated versioning, binding, context packet,
  connector output, evaluation/feedback, projection idempotency and cross-project isolation all
  reconstruct successfully without provider calls.
- `make check` — passed: formatting/lint, registry/operator/secret checks, TypeScript checks,
  114 Python tests, all TypeScript tests, Brand workspace validators, Creative Field certification
  and Compose validation.
- `ssh -o BatchMode=yes -o ConnectTimeout=10 home-server true` — passed.
- Home-server existing Cognee environment dependency-free health — passed (`HealthState.AVAILABLE`).
- Creative Studio temporary HTTP smoke — passed (`GET /api/state` returned the scoped project,
  moodboard, empty field and event envelope).
- `make sync-server` was not run: the home-server checkout has independent uncommitted changes,
  and the sync script correctly refuses to replace or merge a dirty checkout.

## Updates

- Created: `2026-09-03T16:28:24.775723+00:00`
- 2026-09-03: synthetic end-to-end certification runner added; repository-wide checks and
  home-server smoke verification remain in progress.
- 2026-09-03: local release gates passed; task moved to review with remote deployment explicitly
  held behind the dirty-checkout boundary.

## Changed Files

- `scripts/certify_creative_field.py`
- `scripts/project_creative_field.py`
- `Makefile`
- `scripts/setup_server_cognee.sh`
- `tests/test_project_creative_field.py`
- `tests/test_reasoning_operator_workspace.py`
- `scripts/populate_reasoning_operator_workspace.py`
- `workspaces/reasoning-operators/WORKSPACE.yaml`
- `workspaces/reasoning-operators/README.md`
- `workspaces/reasoning-operators/resource_registry.json`
- `docs/operations/creative-field.md`
- `docs/workboards/moodboard-creative-field-implementation/DECISIONS.md`

## Residual Risks

- The new Creative Field code has not been synchronized to or live-smoke-tested on home-server;
  that requires an authorized clean checkout or an explicit temporary deployment target.
- Real model-provider calls, multimodal decoding, production export directly from SQLite and the
  comparative product-value experiment remain intentionally unrun.

## Handoff Notes

- Dependencies: TASK-001 through TASK-012. No task may be waived by this integration task.
- Local implementation is ready for review. To deploy, preserve the home-server working tree,
  synchronize a clean checkout, install `packages/testflight-creative-field` before the Cognee
  adapter, then run the staging projection and retrieval certification before promotion.
