# TASK-012-project-creative-field-records-into-cognee: Project Creative Field records into Cognee

Status: done
Owner: talha
Current gate: done

## Problem

Creative Field records need bounded retrieval and relationship exploration without making Cognee
the source of truth.

## Scope

In:

- Add idempotent projection of field versions, principles, tensions, exclusions, contributions,
  bindings and evidence metadata into a project/creative-field child container.
- Add exact, lexical, bounded hybrid and two-hop relationship routes with source anchors.

Out:

- Binary asset storage, semantic acceptance and field-version selection by similarity.

## Acceptance Criteria

- Projection rebuilds from canonical state and uses namespaced stable IDs.
- Retrieval preserves workspace, project, field version, status, evidence, rights and authority.
- No-hit and cross-project adversarial probes are correct.
- A projection failure cannot corrupt canonical state.

## Plan

- Define projection manifest and source hash.
- Extend the Cognee adapter behind existing boundaries.
- Add dry-run, idempotency and drift/rebuild commands.
- Certify retrieval before enabling automatic use.

## Verification Evidence

- `uv run --package testflight-adapter-cognee pytest adapters/cognee/tests/test_creative_field_projection.py adapters/cognee/tests/test_adapter.py -q` — 18 passed.
- `uv run pytest tests/test_project_creative_field.py -q` — 1 passed.
- `uv run python scripts/certify_creative_field.py` — passed; projection idempotency and cross-project isolation probes passed.
- `uv run ruff check adapters/cognee scripts/project_creative_field.py` — passed.
- The projection builder is pure and deterministic, uses child/project-namespaced stable IDs,
  preserves source/evidence/authority/rights metadata, emits bounded edges, and writes derived
  manifests atomically. Population is exposed only through the explicit Cognee adapter seam and
  remains gated to `*_staging` datasets.

## Updates

- Created: `2026-09-03T16:28:24.775631+00:00`
- 2026-09-03: implemented deterministic Creative Field child projection, dry-run/rebuild/drift
  CLI, lazy Cognee population seam, source/rights metadata preservation and isolation tests.

## Changed Files

- `adapters/cognee/src/testflight_adapter_cognee/creative_field_projection.py`
- `adapters/cognee/src/testflight_adapter_cognee/__init__.py`
- `adapters/cognee/tests/test_creative_field_projection.py`
- `adapters/cognee/README.md`
- `adapters/cognee/pyproject.toml`
- `scripts/project_creative_field.py`
- `tests/test_project_creative_field.py`
- `docs/operations/creative-field.md`
- `docs/workboards/moodboard-creative-field-implementation/DECISIONS.md`

## Residual Risks

- Live Cognee population and retrieval probes still require the home-server Cognee environment and
  explicit dataset authorization; synthetic certification deliberately makes no provider calls.
- The canonical record export consumed by the CLI is currently a caller-provided JSON boundary;
  a production export/rebuild job should read the SQLite repository directly.

## Handoff Notes

- Dependencies: TASK-007, TASK-008.
- Child projection is proposal-only and rebuildable; do not treat `.data/` or Cognee output as
  canonical state.
