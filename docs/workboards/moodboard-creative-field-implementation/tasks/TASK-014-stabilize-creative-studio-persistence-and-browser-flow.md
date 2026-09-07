# TASK-014-stabilize-creative-studio-persistence-and-browser-flow: Stabilize Creative Studio persistence and browser flow

Status: done
Owner: talha
Current gate: done

## Problem

The initial Creative Studio slice could lose uploads or display in-memory ghost references under
real threaded HTTP use, and it did not replay its board or review state after restart.

## Scope

In:

- synchronize the SQLite repository and serialize Studio commands;
- commit asset, rights record, and board revision atomically;
- hydrate board, annotations, and review decisions from canonical records;
- enforce upload/body bounds and project-scoped blob reads;
- render real image blobs and report command failures in the UI;
- carry explicit image media parts through the OpenAI-compatible provider seam;
- verify the path with HTTP, concurrency, restart, provider, and browser tests.

Out:

- inventing semantic observations or a Creative Field from an image;
- automatic field acceptance;
- production provider routing, live model calls, or additional modalities.

## Acceptance Criteria

- Failed persistence does not publish a new UI snapshot.
- Concurrent uploads produce contiguous durable board revisions without ghost records.
- A restart restores the current board, annotations, review decision, and blobs.
- Unreferenced hashes and nonexistent license identities are rejected at the command boundary.
- Explicit image media parts preserve JSON context and map to OpenAI-compatible `image_url`
  content.
- The complete repository release gate remains green.

## Verification Evidence

- `uv run pytest apps/creative-studio/tests/test_server.py adapters/sqlite-semantic/tests/test_creative_repository.py -q` — 13 passed.
- `pnpm --filter @testflight/operator-runtime test` — 8 passed.
- `uv run ruff format --check apps/creative-studio` — passed.
- `uv run ruff check apps/creative-studio` — passed.
- `make check` — passed: 121 Python tests, all TypeScript checks/tests, validators,
  certification and Compose validation. The environment reports a non-blocking Node 22 versus
  repository `>=24` engine warning.
- Browser smoke with two openly licensed Wikimedia image files — uploads rendered as `<img>`
  thumbnails; SQLite contained two `ReferenceAsset` and two `SourceLicenseRecord` records; an
  annotation and accepted review persisted; restart replay restored references, annotation,
  revision and accepted status; blob GET returned the original bytes and `image/jpeg`.
- Screenshots: `output/playwright/creative-studio-fixed-desktop.png`,
  `output/playwright/creative-studio-fixed-restart.png`,
  `output/playwright/creative-studio-fixed-mobile.png`.

## Changed Files

- `adapters/sqlite-semantic/src/testflight_adapter_sqlite_semantic/creative_repository.py`
- `apps/creative-studio/src/testflight_creative_studio/server.py`
- `apps/creative-studio/src/testflight_creative_studio/static/index.html`
- `apps/creative-studio/src/testflight_creative_studio/static/app.js`
- `apps/creative-studio/src/testflight_creative_studio/static/styles.css`
- `apps/creative-studio/tests/test_server.py`
- `packages/testflight-operator-runtime/src/providers.ts`
- `packages/testflight-operator-runtime/test/runtime.test.ts`
- `docs/plans/2026-09-03-moodboard-creative-field-stabilization.md`

## Residual Risks

- Creative Studio still exposes a review command but does not yet invoke the observation,
  interpretation, synthesis, projection, or connector workflows; that production bridge remains
  a follow-up once provider routing and client operator packs are configured.
- The browser run used local temporary runtime data and did not make a live model-provider call.
- Home-server synchronization remains held behind its independently dirty checkout.

## Handoff Notes

The stabilized local vertical slice is safe for real-file smoke testing. The next semantic task is
to add an explicit Creative Studio-to-operator-runtime bridge that produces reviewable,
evidence-linked proposals without mutating the canonical Brand world automatically.
