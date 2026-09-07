# TASK-004-build-deterministic-multimodal-normalization-pip: Build deterministic multimodal normalization pipeline

Status: ready
Owner: unassigned
Current gate: readiness

## Problem

The new Content contracts need a provider-free normalization pipeline that establishes media
identity, time bases, segments, track alignment, and source-anchored observations before any live
multimodal provider is introduced.

## Scope

In:

- Add processor ports and deterministic fixture-backed implementations.
- Normalize source bundles into ContentUnit, MediaTrack, ContentSegment, observation, and relation
  records.
- Preserve unavailable modalities, segmentation uncertainty, and derivation receipts.
- Prove replay/idempotency and cross-modal anchor continuity.

Out:

- Instagram acquisition or API integration.
- Model-provider calls, semantic interpretation, social ontology, or World projection.
- Production media transcoding beyond the smallest adapter boundary.

## Acceptance Criteria

- Synthetic three-reel fixture normalizes into a valid ContentBundle.
- Replayed input produces stable equivalent records without duplicate occurrences.
- Time, text, spatial, and cross-modal anchors resolve to source records.
- Unavailable media remains explicit and never becomes invented observations.
- Processor failures return typed partial/hold outcomes with derivation evidence.

## Plan

- Read Content contracts and fixture validator.
- Define processor ports and normalization result type.
- Implement fixture-backed normalizers and deterministic anchor checks.
- Add continuity/idempotency tests and run full workspace verification.

## Verification Evidence

- Not run yet; task is implementation-ready.

## Updates

- Created: `2026-09-04T10:45:41.539220+00:00`
- Intake/readiness defined after TASK-002 contract completion: `2026-09-04T11:02:00Z`

## Handoff Notes

- Start from `packages/testflight-content` and `reasoning/fixtures/content/multimodal-profile.yaml`.
