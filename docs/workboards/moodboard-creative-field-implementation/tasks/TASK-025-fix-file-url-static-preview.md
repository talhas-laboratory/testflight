# TASK-025-fix-file-url-static-preview: Restore styled Creative Studio preview when opened as a file

Status: done
Owner: talha
Current gate: done

## Problem

The static Creative Studio page was opened directly from the filesystem during review. Its
root-relative stylesheet and script URLs resolved to `/styles.css` and `/app.js` at the filesystem
root, so the browser showed unstyled HTML. The same page is normally served at `/` by the Creative
Studio HTTP server.

## Scope

In:

- make the static stylesheet and script references resolve relative to `index.html`;
- keep HTTP-served behavior unchanged;
- make file previews render the visual shell and show a clear live-server notice;
- prevent file previews from attempting API commands or state fetches;
- add a regression test for the asset references and file-preview guard.

Out:

- making a filesystem page a live Creative Studio client;
- changing API routes, persistence or server-side command behavior.

## Acceptance Criteria

- Opening the static `index.html` directly loads `styles.css` and `app.js`.
- File previews show the styled Creative Studio shell and explain that live data requires HTTP.
- HTTP-served Creative Studio still loads state and keeps existing interactions.
- Static JavaScript syntax, focused tests and release gates pass.

## Verification Evidence

- `node --check apps/creative-studio/src/testflight_creative_studio/static/app.js` — passed.
- Chromium screenshot of the direct `file://` page — styled shell rendered; preview-only notice visible.
- Chromium screenshot of `http://127.0.0.1:8791/` — HTTP page rendered with persisted state and no regression.
- `uv run pytest apps/creative-studio/tests/test_server.py -q` — 22 server tests passed.

## Changed Files

- `apps/creative-studio/src/testflight_creative_studio/static/index.html`
- `apps/creative-studio/src/testflight_creative_studio/static/app.js`
- `apps/creative-studio/tests/test_server.py`

## Handoff Notes

Use the HTTP server URL for uploads, analysis, review and artifact handoff. A direct file URL is a
useful static visual preview only.
