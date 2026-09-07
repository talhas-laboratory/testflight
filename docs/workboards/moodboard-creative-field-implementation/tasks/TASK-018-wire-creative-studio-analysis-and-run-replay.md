# TASK-018-wire-creative-studio-analysis-and-run-replay: Wire Creative Studio analysis and run replay

Status: done
Owner: talha
Current gate: done

## Problem

The Creative Field coordinator and runtime transport were available, but Creative Studio could
only capture references and record a generic review decision. There was no application command
that started analysis, surfaced its proposal, or restored the result after a restart.

## Scope

In:

- add a proposal-only `analyze_field` command and UI action;
- construct the coordinator from project-scoped dimensions and the transport executor at the
  Creative Studio composition root;
- persist a canonical `CreativeFieldRun` record with stage receipts and result status;
- derive a stable default run ID from the moodboard revision and replay it without provider work;
- hydrate the analysis/proposal state after process restart while preserving later review state.

Out:

- background queue, cancellation or progress streaming;
- accepted field version creation, Brand-world binding or artifact projection;
- semantic YAML loading/client packs or live provider calls.

## Acceptance Criteria

- A configured store's `analyze_field` command runs observation, interpretation and synthesis in
  order and persists typed proposal records plus a run record.
- The command always carries project scope and remains proposal-only; no field version is created.
- Repeating the same board-revision run does not call the executor again.
- A fresh Creative Studio process restores the run and proposal state from SQLite, and an existing
  review decision is not overwritten by hydration.
- The HTTP command boundary and UI action expose the result; missing runtime configuration returns a
  held outcome without mutating canonical state.

## Verification Evidence

- `uv run pytest apps/creative-studio/tests -q` — 16 Creative Studio tests passed, including
  direct and HTTP analysis, replay, restart hydration, review preservation and configuration hold.
- `uv run pytest apps/creative-studio/tests packages/testflight-creative-field/tests adapters/sqlite-semantic/tests -q` — 49 focused tests passed.
- `uv run ruff format --check apps/creative-studio packages/testflight-creative-field adapters/sqlite-semantic` — passed.
- `uv run ruff check apps/creative-studio packages/testflight-creative-field adapters/sqlite-semantic` — passed.
- `make check` — passed: 131 Python tests, all TypeScript checks/tests, validators, certification
  and Compose validation. The environment reports a non-blocking Node 22 versus repository
  `>=24` engine warning.

## Changed Files

- `packages/testflight-creative-field/src/testflight_creative_field/models.py`
- `packages/testflight-creative-field/README.md`
- `adapters/sqlite-semantic/src/testflight_adapter_sqlite_semantic/creative_repository.py`
- `apps/creative-studio/src/testflight_creative_studio/server.py`
- `apps/creative-studio/src/testflight_creative_studio/static/index.html`
- `apps/creative-studio/src/testflight_creative_studio/static/app.js`
- `apps/creative-studio/tests/test_server.py`
- `.env.example`

## Residual Risks

- The command is synchronous and keeps the UI request open during provider execution; a job API is
  the next operational increment.
- The review button still records a generic decision and does not yet call
  `CreativeFieldLifecycle.review_and_version` with an authority grant.
- Semantic YAML procedure loading/client packs and real provider calls remain intentionally out of
  this slice.

## Handoff Notes

Next, add an authority-aware review/version command that targets the persisted proposal, creates an
immutable `CreativeFieldVersion`, and exposes its status to the field view. Then add explicit
`ProjectBinding`/`FieldBinding` resolution before artifact projection.
