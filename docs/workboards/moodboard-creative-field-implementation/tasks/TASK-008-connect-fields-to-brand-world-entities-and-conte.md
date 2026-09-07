# TASK-008-connect-fields-to-brand-world-entities-and-conte: Connect fields to Brand-world entities and contexts

Status: done
Owner: talha
Current gate: implementation

## Problem

The field must attach easily and explicitly to the Brand world without copying Brand records or
becoming a disconnected creative database.

## Scope

In:

- Implement `ProjectBinding`, `FieldBinding` and CreativeFieldApplication relationship frames.
- Resolve exact workspace, context, branch, entities, time, scope and precedence.
- Extend Brand ontology only for relationships that express world meaning.

Out:

- Artifact packet compilation, generation and global taste inheritance.

## Acceptance Criteria

- One project selection scopes all board/field records.
- Fields bind to Brand, Offering, Product, Audience, Campaign, Channel and artifact families.
- Cross-workspace, incompatible-time and ambiguous-precedence cases hold or reject.
- Bindings reference canonical IDs and remain replayable.

## Plan

- Define binding contracts and ontology relations.
- Add deterministic binding resolver and diagnostics.
- Integrate with existing Context, RepresentationBinding and RelationshipFrame records.
- Add isolation, precedence, time and ambiguity tests.

## Verification Evidence

- `uv run --package testflight-creative-field pytest packages/testflight-creative-field/tests -q` — 15 passed.
- `uv run ruff check packages/testflight-creative-field` — all checks passed.
- Binding tests cover canonical entity resolution, relationship-frame creation, cross-workspace isolation, validity windows and precedence ambiguity.

## Updates

- Created: `2026-09-03T16:28:24.775244+00:00`
- 2026-09-03: implemented deterministic project/field binding resolution and a `CreativeFieldApplication` relationship frame over canonical entity IDs.

## Changed Files

- `packages/testflight-creative-field/src/testflight_creative_field/bindings.py`
- `packages/testflight-creative-field/src/testflight_creative_field/__init__.py`
- `packages/testflight-creative-field/tests/test_bindings.py`

## Residual Risks

- Entity lookup is currently a typed mapping port; integration with the live Brand-world repository and temporal relation store remains for the context compiler task.
- Relationship frames are emitted locally and are not yet projected into Cognee or the artifact context packet.

## Handoff Notes

- Dependencies: TASK-002, TASK-007.
