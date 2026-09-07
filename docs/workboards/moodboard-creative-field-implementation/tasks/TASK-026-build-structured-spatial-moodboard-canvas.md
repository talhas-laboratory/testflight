# TASK-026 — Build a durable structured spatial Moodboard canvas

Status: done

## Scope

Replace the auto-fill moodboard grid with a spatial canvas that exposes the existing placement
model, preserves source and annotation cues, and allows explicit named visual clusters. Keep the
artifact bridge available, but out of the primary curation surface.

## Acceptance criteria

- Dragging a reference persists an immutable next `BoardRevision` with a project-scoped
  `Placement` update.
- A user can explicitly create and assign named `ReferenceCluster` records; a cluster is never
  inferred from card proximity.
- Restart replay restores placement and cluster data.
- Old compact linear layouts render legibly and are normalized only when a user saves a layout.
- Source type and annotation state remain visible on each card.
- Artifact controls are initially collapsed and remain available on explicit request.

## Verification

- Focused Creative Studio server tests cover layout persistence, replay, and held invalid layout.
- A local Chromium flow creates a cluster, drags a card, confirms persistence, and captures a
  screenshot.
- `make check` passes.

## Completion evidence

- Focused Creative Studio suite: 24 passing tests, including durable placement and cluster replay.
- Local Chromium exercised explicit cluster creation, pointer drag persistence, source/annotation
  signals, and the collapsed artifact workflow; screenshots are in `output/playwright/`.
- Full `make check` passed: 159 Python tests, 12 operator-runtime tests, 18 context-intelligence
  tests, all static and registry checks, and Creative Field certification.
