# TASK-001-record-the-content-substrate-architecture-decisi: Record the Content substrate architecture decision and semantic glossary

Status: done
Owner: codex
Current gate: done

## Problem

The accepted post-build Content architecture needs a durable decision and shared vocabulary before
new packages or mappings are introduced.

## Scope

In:

- Record the Content substrate boundary as ADR 0006.
- Define the semantic planes and legal transitions between them.
- Link the accepted architecture and existing Creative Field/World contracts.

Out:

- Python/TypeScript model implementation.
- Multimodal processors, provider adapters, persistence migrations, or runtime calls.
- Changes to the accepted Brand or Creative Field ontologies.

## Acceptance Criteria

- ADR identifies the implementation baseline, decision, consequences, and rejected alternatives.
- Glossary distinguishes evidence, observation, normalized Content, interpretation, module
  knowledge, World proposal, accepted World, retrieval, steering, and action.
- Each permitted cross-plane transition names its handoff and authority.
- Existing architecture remains referenced rather than duplicated.

## Plan

- Read the accepted architecture and current semantic/Creative Field contracts.
- Add ADR 0006.
- Add the semantic-plane glossary and transition table.
- Verify links, terminology coverage, and working-tree scope.

## Verification Evidence

- Passed: `rg -n "Evidence|Observation|Normalized Content|Interpretation|World Projection Proposal|Reasoning Steering" docs/decisions/0006-content-substrate-and-world-compilation.md docs/contracts/content-semantic-planes.md`
- Passed: `git diff --check -- docs/decisions/0006-content-substrate-and-world-compilation.md docs/contracts/content-semantic-planes.md`
- Passed link-target existence checks for the accepted design, glossary, reasoning README, Creative
  Field README, and context-intelligence README.
- Changed artifacts: `docs/decisions/0006-content-substrate-and-world-compilation.md`,
  `docs/contracts/content-semantic-planes.md`.
- Residual risk: terminology still requires implementation proof against synthetic fixtures.

## Updates

- Created: `2026-09-04T10:45:41.538731+00:00`
- Claimed by codex and advanced through intake/readiness: `2026-09-04T10:46:06Z`
- Implementation and verification complete: `2026-09-04T10:47:48Z`

## Handoff Notes

- Complete. Follow-up contract and fixture work is tracked by TASK-002 and TASK-003.
