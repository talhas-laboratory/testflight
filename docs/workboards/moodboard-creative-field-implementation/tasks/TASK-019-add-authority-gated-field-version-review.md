# TASK-019-add-authority-gated-field-version-review: Add authority-gated field version review

Status: done
Owner: talha
Current gate: done

## Problem

Creative Studio could display a proposal and record a review action, but accepting a proposal did
not call the existing lifecycle gate or create an immutable `CreativeFieldVersion`.

## Scope

In:

- resolve the current persisted proposal from project-scoped state;
- require an explicit authority grant for acceptance;
- construct a correctly targeted `ReviewDecision`, call `CreativeFieldLifecycle.review_and_version`,
  and atomically persist the decision plus immutable version;
- keep hold/revise proposal-level and restore accepted version state on replay/restart;
- expose authority configuration through the Creative Studio composition root.

Out:

- replacement-proposal editing UI for modify reviews;
- ProjectBinding/FieldBinding creation and artifact projection;
- remote authorization service or automatic authority inference.

## Acceptance Criteria

- A proposal can become a version only with an explicit authority grant and lifecycle validation.
- Acceptance without a grant is held and creates no version.
- Repeated acceptance of the same proposal is idempotent and does not create a second version.
- The accepted version remains proposal-derived, immutable and project-scoped; restart hydration
  preserves its status and version ID.
- Existing generic review behavior and release checks remain green.

## Verification Evidence

- `uv run pytest apps/creative-studio/tests -q` — 17 Creative Studio tests passed, including
  authority hold, immutable version creation, idempotent replay and restart hydration.
- `make check` — passed: 132 Python tests, all TypeScript checks/tests, validators, certification
  and Compose validation. The environment reports a non-blocking Node 22 versus repository
  `>=24` engine warning.

## Changed Files

- `packages/testflight-creative-field/src/testflight_creative_field/models.py`
- `apps/creative-studio/src/testflight_creative_studio/server.py`
- `apps/creative-studio/README.md`
- `apps/creative-studio/tests/test_server.py`
- `.env.example`
- `docs/workboards/moodboard-creative-field-implementation/DECISIONS.md`

## Residual Risks

- The current UI still needs a richer review editor for modifying/splitting/merging proposals.
- Accepted versions are not yet explicitly bound to Brand-world entities or artifact workflows.
- The authority grant is configuration text at this boundary; a real authorization provider is
  future infrastructure.

## Handoff Notes

Next, resolve explicit `ProjectBinding` and `FieldBinding` records for an accepted version, then
compile a target-neutral `FieldProjection` and `CreativeContextPacket` for an artifact request.
