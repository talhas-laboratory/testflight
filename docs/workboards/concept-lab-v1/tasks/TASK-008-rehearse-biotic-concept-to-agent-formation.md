# TASK-008-rehearse-biotic-concept-to-agent-formation: Rehearse Biotic concept-to-agent formation

Status: backlog
Owner: unassigned
Current gate: intake

## Problem

V1 needs one realistic proof that a prior founder conversation can become theory, ontology and
agent-traversal proposals, and a reversible technical formation without corrupting brand or
Product workspace truth.

Dependencies: TASK-007.

Required reading:

- All Concept Lab contracts and fixtures.
- `workspaces/brand-hellobiotic-research/content-strategy/artifacts/founder-brief-2026-09-08.md`
- `workspaces/brand-hellobiotic-research/content-strategy/artifacts/relational-content-model.yaml`
- `workspaces/brand-hellobiotic-research/content-strategy/artifacts/newsletter-agent-charter.yaml`
- The bridge and Product module contracts.

## Scope

In:

- Populate the `relational-content` child with source references, concept fragments, competing
  theory branches where appropriate, and one selected branch for formation.
- Produce a formation packet containing an ontology proposal, traversal policy, and newsletter
  agent-composition proposal.
- Produce the reverse trace from those technical proposals to the founder brief.
- Add exact, intent, adversarial-navigation, and no-hit probes for this child.

Exact implementation path:

- `workspaces/concept-lab/relational-content/` artifacts, registry, probes, and receipt only.
- Product workspace receives no accepted mutation in this task.

Out:

- Publishing content, implementing the newsletter workflow, generalizing the theory to other
  brands, live retrieval population, or asserting customer/scientific truth.

## Acceptance Criteria

- The proof preserves the founder brief as strategic direction, not customer evidence.
- “Vegan” remains an ethical/sourcing attribute rather than a biological mechanism.
- Traversal begins from person/context/field/tension before optionally reaching brand/product.
- FormationPacket is proposal-only and names exact Product targets.
- ReverseTrace resolves every technical rule to theory and source or reports an explicit gap.
- Concept Lab validator and targeted tests pass.

## Plan

- Claim only after TASK-007.
- Register source references through the explicit brand-to-Lab boundary; do not copy unsupported
  inferred facts.
- Execute the four operator procedures as an inspectable fixture transformation.
- Run independent deterministic evaluation and record limitations.
- Commit the proof case separately.

Failure mode: a polished technical artifact conceals missing source lineage or promotes the
relational model beyond its founder-hypothesis status.

Verification commands:

- `uv run python scripts/validate_concept_lab.py`
- `uv run pytest tests/test_concept_lab.py -q`
- child-container structural validation for `relational-content`
- `git diff --check`

## Verification Evidence

- Not run yet.

## Updates

- Created: `2026-09-08T09:53:07.959504+00:00`

## Handoff Notes

- On completion, make TASK-009 ready. State explicitly that live retrieval is uncertified.
