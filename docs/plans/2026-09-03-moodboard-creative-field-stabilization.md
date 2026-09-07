# Moodboard / Creative Field stabilization scope

**Date:** 2026-09-03  
**Status:** implemented and verified

## Goal

Make the current Creative Studio vertical slice safe to exercise with real reference files. A
successful command must be durable, project-scoped, replayable after restart, and visible in the
board without losing the original bytes or the review trail.

## In scope

- synchronize the append-only SQLite adapter and serialize Studio commands;
- commit a reference and its board revision as one transaction;
- hydrate the current board and review state from canonical records on startup;
- persist field review decisions as `ReviewDecision` records;
- serve only referenced content-addressed blobs through a project-scoped endpoint;
- render image references in the board and handle command failures in the UI;
- capture an explicit upload rights declaration as a `SourceLicenseRecord` when provided;
- bound HTTP and decoded upload sizes;
- encode optional image media parts in the OpenAI-compatible operator adapter;
- add HTTP-level and provider-payload regression tests.

## Explicit non-goals

This pass does not invent a semantic field from an image, auto-accept model proposals, or silently
turn a review flag into an empty `CreativeFieldVersion`. The existing observation, interpretation,
synthesis, projection, and connector contracts remain the semantic boundary. A production bridge
from Creative Studio into those workflows remains a follow-up once provider routing and client
operator packs are configured.

## Invariants

1. Failed persistence does not publish a new in-memory snapshot.
2. A restart reconstructs the latest board revision and review decisions from canonical storage.
3. Blob access is limited to hashes referenced by the current project.
4. Uploads without a rights declaration remain evidence but cannot claim a generation permission.
5. Raw media remains evidence; the provider receives it only through an explicit multimodal media
   part and retains the ordinary JSON context alongside it.
6. Review records preserve actor, rationale, action, target, and derivation metadata.

## Verification

- unit tests cover repository concurrency/atomicity and Studio hydration;
- HTTP tests cover upload, annotation, review, blob access, invalid payloads, and restart replay;
- TypeScript tests assert image media is translated to `image_url` content and text context remains
  present;
- `make check` remains the release gate;
- a Playwright smoke run uploads two openly licensed images, checks rendered thumbnails, annotates
  one reference, accepts the field, restarts the server, and verifies the state is retained.
