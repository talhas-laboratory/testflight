# TASK-024-expose-artifact-handoff-in-creative-studio: Expose the artifact handoff in the UI

Status: done
Owner: talha
Current gate: done

## Problem

The accepted Creative Field could already be projected, prepared, invoked and evaluated through
commands, but Creative Studio did not expose that handoff to a client without manually constructing
raw API payloads.

## Scope

In:

- add an explicit Artifact Bridge panel to the Creative Studio page;
- collect workspace, context, branch, entity, privacy, authority, request, lens and disclosure
  inputs before projection;
- build a conservative target capability manifest for packet preparation;
- expose prepare, invoke and evaluate actions with visible status/receipt identifiers;
- keep missing authority, target adapters, scope and accepted-field state as backend holds;
- preserve the existing editorial visual language and narrow-screen layout.

Out:

- implicit scope or authority defaults;
- automatic target adapter registration;
- feedback promotion or field mutation from the UI;
- audio/video-specific target controls.

## Acceptance Criteria

- A client can enter the explicit project/world/target fields and submit `project_field` from the
  Creative Studio page.
- The same page can prepare a `GenerationPacket`, invoke a configured adapter and request output
  evaluation without bypassing backend gates.
- The current context/target/evaluation status and identifiers are visible after each successful
  command.
- The panel remains usable at desktop and narrow mobile widths and does not expose credentials.
- Static JavaScript syntax, HTTP page serving, focused tests and full release gates pass.

## Verification Evidence

- `node --check apps/creative-studio/src/testflight_creative_studio/static/app.js` — passed.
- `playwright screenshot -b chromium --full-page http://127.0.0.1:8791 output/playwright/creative-studio-full.png` — rendered desktop page inspected.
- `playwright screenshot -b chromium --viewport-size="390,844" --full-page http://127.0.0.1:8791 output/playwright/creative-studio-mobile.png` — narrow layout rendered and inspected. The CLI's `playwright-cli` wrapper was unavailable; the installed Playwright CLI used Chromium instead.
- `uv run pytest apps/creative-studio/tests/test_server.py -q` — 21 server tests passed, including artifact controls served from `/`.
- `make check` — passed: 142 Python tests, all TypeScript checks/tests, validators, certification and Compose validation. The environment reports a non-blocking Node 22 versus repository `>=24` engine warning.

## Changed Files

- `apps/creative-studio/src/testflight_creative_studio/static/index.html`
- `apps/creative-studio/src/testflight_creative_studio/static/app.js`
- `apps/creative-studio/src/testflight_creative_studio/static/styles.css`
- `apps/creative-studio/tests/test_server.py`

## Residual Risks

- Production still requires a configured target adapter and out-of-band provider credentials.
- The UI uses a conservative image/text target manifest and does not yet model all provider
  capability controls.
- There is no collaborative multi-user canvas or feedback-promotion editor yet.

## Handoff Notes

The next increment should add a configured target-adapter registry/capability discovery endpoint
and a credentialed Luna-max smoke in a controlled environment, then consider async jobs for larger
boards.
