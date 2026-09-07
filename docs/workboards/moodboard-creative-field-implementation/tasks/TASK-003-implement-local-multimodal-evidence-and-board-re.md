# TASK-003-implement-local-multimodal-evidence-and-board-re: Implement local multimodal evidence and board revision storage

Status: done
Owner: talha
Current gate: implementation

## Problem

The current repository stores text evidence and accepted Brand assertions but cannot replay
multimodal board state or retain binary client assets safely outside Git.

## Scope

In:

- Add a content-addressed local evidence adapter for bytes and derived thumbnails.
- Extend SQLite persistence for projects, boards, revisions, placements, annotations, licences,
  proposals, reviews and versions.
- Add optimistic concurrency and replay.

Out:

- Cloud object storage, collaborative editing and Cognee indexing.

## Acceptance Criteria

- Duplicate bytes share storage while retaining distinct source identities.
- Board revisions replay identically and conflicting writes fail atomically.
- Runtime assets/databases remain outside Git under configured data root.
- Corrections preserve prior records and dependency lineage.

## Plan

- Define repository ports in the domain package.
- Implement filesystem and SQLite adapters with migrations.
- Add event replay and snapshot builders.
- Add recovery, corruption and permission failure tests.

## Verification Evidence

- `uv run --package testflight-adapter-sqlite-semantic pytest adapters/sqlite-semantic/tests/test_repository.py adapters/sqlite-semantic/tests/test_creative_repository.py -q` — 6 passed.
- `uv run --package testflight-adapter-sqlite-semantic ruff check adapters/sqlite-semantic packages/testflight-creative-field --fix` — all checks passed after import/format fixes.
- `uv sync --all-groups` — workspace dependency resolution completed.

## Updates

- Created: `2026-09-03T16:28:24.774508+00:00`
- 2026-09-03: implemented content-addressed source/derivative storage, immutable creative record persistence and optimistic board revision replay.

## Changed Files

- `packages/testflight-creative-field/src/testflight_creative_field/ports.py`
- `packages/testflight-creative-field/src/testflight_creative_field/__init__.py`
- `adapters/sqlite-semantic/src/testflight_adapter_sqlite_semantic/blob_store.py`
- `adapters/sqlite-semantic/src/testflight_adapter_sqlite_semantic/creative_repository.py`
- `adapters/sqlite-semantic/src/testflight_adapter_sqlite_semantic/__init__.py`
- `adapters/sqlite-semantic/pyproject.toml`
- `adapters/sqlite-semantic/tests/test_creative_repository.py`

## Residual Risks

- The local store has no cloud replication, collaborative merge UI or background thumbnail generation yet.
- Board replay currently relies on SQLite JSON functions; adapter certification should verify the deployed SQLite runtime exposes JSON1.

## Handoff Notes

- Dependencies: TASK-001, TASK-002. Never commit real client material or runtime databases.
