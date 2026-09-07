# TASK-003-create-synthetic-multimodal-profile-fixtures-and: Create synthetic multimodal profile fixtures and Phase 0 gates

Status: done
Owner: codex
Current gate: done

## Problem

The Content architecture needs a provider-free golden corpus that proves multimodal anchoring,
independent recurrence, counterexamples, missing modalities, branch outcomes, and honest holds.

## Scope

In:

- Define one synthetic profile with three short reels and shared profile metadata.
- Include synchronized video, audio, transcript, caption, OCR, keyframe, and metadata descriptions.
- Include one recurring multimodal pattern, meaningful variation, and one counterexample.
- Define expected observations, interpretations, pattern scope, omissions, holds, and no-hits.
- Add deterministic fixture validation.

Out:

- Real media generation or downloaded social content.
- Live provider/model calls.
- Production Content models, persistence, or Instagram acquisition.

## Acceptance Criteria

- Fixture is synthetic, self-contained, rights-safe, and provider-free.
- Every expected observation resolves to a declared temporal/textual/source anchor.
- Recurrent pattern evidence spans independent reels and retains a counterexample.
- At least one unavailable modality, one rights hold, one unsupported inference hold, and one no-hit
  are explicit expected outcomes.
- Validator rejects missing anchors, unknown references, duplicate IDs, and invalid recurrence.
- Tests pass without credentials or network access.

## Plan

- Inspect existing fixture and validation conventions.
- Define the fixture schema and one golden profile corpus.
- Add a deterministic validation script and tests.
- Run focused tests and format/diff checks.

## Verification Evidence

- Passed: `make content-fixtures` — 3 units, 11 observations, 1 scoped pattern, and 4
  gate cases certified.
- Passed: `uv run pytest tests/test_multimodal_content_fixtures.py -q` — 5 tests.
- Passed: `uv run ruff format --check scripts/validate_multimodal_content_fixtures.py tests/test_multimodal_content_fixtures.py`.
- Passed: `uv run ruff check scripts/validate_multimodal_content_fixtures.py tests/test_multimodal_content_fixtures.py`.
- Passed: targeted `git diff --check`.
- Changed artifacts: `reasoning/fixtures/content/multimodal-profile.yaml`,
  `scripts/validate_multimodal_content_fixtures.py`,
  `tests/test_multimodal_content_fixtures.py`, and the additive `content-fixtures` Make target.
- Residual risk: fixture media is represented structurally rather than as encoded audio/video bytes;
  byte-level continuity belongs to TASK-004.

## Updates

- Created: `2026-09-04T10:45:41.539063+00:00`
- Claimed by codex and advanced through intake/readiness: `2026-09-04T10:47:48Z`
- Implementation and focused verification complete: `2026-09-04T10:51:14Z`

## Handoff Notes

- Complete. TASK-002 may now implement contracts against this fixture without provider calls.
