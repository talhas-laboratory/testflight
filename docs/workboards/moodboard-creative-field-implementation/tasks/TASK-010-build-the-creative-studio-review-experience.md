# TASK-010-build-the-creative-studio-review-experience: Build the Creative Studio review experience

Status: done
Owner: talha
Current gate: implementation

## Problem

Human review is necessary for semantic authority, but Brand Lab is intentionally read-only and
cannot provide the board-to-field correction workflow.

## Scope

In:

- Create `apps/creative-studio` as a write-capable composition root.
- Implement project/board, Reference Inspector, Field View, diff/approval, binding, projection,
  packet and evaluation surfaces.
- Reuse Brand Lab server/snapshot patterns where contracts permit.

Out:

- Advanced infinite canvas, collaboration, mobile-native app and Harness graph view.

## Acceptance Criteria

- User completes board -> correction -> field -> binding -> projection without schema knowledge.
- Proposed and approved meaning are visually distinct.
- Conflicts, gaps, unavailable runs, provenance and omissions are inspectable.
- UI commands call owning services and never mutate private storage directly.

## Plan

- Build accessible HTML/CSS/JS or chosen minimal frontend over typed application commands.
- Add explicit error and stale-state handling.
- Add browser tests for the vertical slice.
- Capture review screenshots and manual usability evidence.

## Verification Evidence

- `uv run --package testflight-creative-studio pytest apps/creative-studio/tests -q` — 4 passed.
- `uv run ruff check apps/creative-studio adapters/creative-connectors packages/testflight-creative-field` — all checks passed.
- Static Creative Studio includes keyboard-focusable drop zone, project scope header, board, inspector/annotation form, field status, workflow receipt strip and responsive mobile layout.
- Server commands are routed through `StudioStore`; UI never opens SQLite or blob paths directly.

## Updates

- Created: `2026-09-03T16:28:24.775434+00:00`
- 2026-09-03: added write-capable Creative Studio composition root with content-addressed upload path, command API, project-scoped board state, annotation/review commands and responsive editorial UI.

## Changed Files

- `apps/creative-studio/pyproject.toml`
- `apps/creative-studio/src/testflight_creative_studio/__init__.py`
- `apps/creative-studio/src/testflight_creative_studio/server.py`
- `apps/creative-studio/src/testflight_creative_studio/static/index.html`
- `apps/creative-studio/src/testflight_creative_studio/static/app.js`
- `apps/creative-studio/src/testflight_creative_studio/static/styles.css`
- `apps/creative-studio/tests/test_server.py`
- `pyproject.toml`

## Residual Risks

- The UI currently exposes command-level capture/annotation/review; operator runs and full field proposal inspector will be connected as the production API surface matures.
- Browser automation and visual QA are still pending for the release certification task.

## Handoff Notes

- Dependencies: TASK-003, TASK-006, TASK-007, TASK-008, TASK-009.
