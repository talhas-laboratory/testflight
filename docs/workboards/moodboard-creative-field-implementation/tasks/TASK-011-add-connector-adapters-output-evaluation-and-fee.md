# TASK-011-add-connector-adapters-output-evaluation-and-fee: Add connector adapters output evaluation and feedback

Status: done
Owner: talha
Current gate: implementation

## Problem

The system needs a capability-honest route from CreativeContextPacket to external tools and back
into reviewable evaluation/feedback without granting adapters semantic authority.

## Scope

In:

- Implement one text and one image target capability manifest and adapter.
- Implement GenerationPacket, disclosure preflight, invocation receipt and normalized output.
- Run creative evaluation and route feedback into minimal change/staleness proposals.

Out:

- Broad provider marketplace, autonomous publishing and automatic field updates.

## Acceptance Criteria

- Adapters receive only supported controls and permitted grounding assets.
- Every call has an exact disclosure and invocation receipt.
- Evaluation separates field fidelity, task fitness, execution quality and target limitations.
- Feedback cannot mutate field/world state without review.

## Plan

- Define adapter conformance suite and fake targets first.
- Implement packet translation, preflight, invocation and normalization.
- Execute evaluation operator independently of generator where practical.
- Connect feedback to dependency/staleness analysis.

## Verification Evidence

- `uv run --package testflight-adapter-creative-connectors pytest adapters/creative-connectors/tests -q` — 3 passed.
- `uv run --package testflight-creative-field pytest packages/testflight-creative-field/tests -q` — 20 passed.
- `uv run ruff check packages/testflight-creative-field adapters/creative-connectors apps/creative-studio` — all checks passed.
- Connector tests verify supported modality/control packets, disclosure and asset rights preflight, normalized text/image outputs and normalized provider failure.
- Evaluation tests verify separate fidelity/fitness/execution dimensions, disagreement preservation and proposal-only feedback.

## Updates

- Created: `2026-09-03T16:28:24.775532+00:00`
- 2026-09-03: added text/image capability manifests and adapters, GenerationPacket compiler, disclosure/asset preflight, normalized output receipts and provider-evaluation/feedback workflow.

## Changed Files

- `adapters/creative-connectors/pyproject.toml`
- `adapters/creative-connectors/src/testflight_adapter_creative_connectors/descriptor.py`
- `adapters/creative-connectors/src/testflight_adapter_creative_connectors/connectors.py`
- `adapters/creative-connectors/src/testflight_adapter_creative_connectors/__init__.py`
- `adapters/creative-connectors/tests/test_connectors.py`
- `packages/testflight-creative-field/src/testflight_creative_field/evaluation.py`
- `packages/testflight-creative-field/src/testflight_creative_field/__init__.py`
- `packages/testflight-creative-field/tests/test_evaluation.py`
- `pyproject.toml`

## Residual Risks

- Targets are provider-neutral injected transports; real external API adapters and media upload limits remain a deployment choice.
- Evaluation semantic quality is supplied by the operator runtime; local code only validates required dimensions, lineage and statuses.

## Handoff Notes

- Dependencies: TASK-005, TASK-009, TASK-010. Registry update precedes external dependencies.
