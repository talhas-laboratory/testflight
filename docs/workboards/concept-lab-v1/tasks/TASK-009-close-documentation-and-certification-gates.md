# TASK-009-close-documentation-and-certification-gates: Close documentation and certification gates

Status: backlog
Owner: unassigned
Current gate: intake

## Problem

After the proof case, repository navigation, Product status, receipts, and verification evidence
must agree so future agents can discover and use the Lab without relying on this conversation.

Dependencies: TASK-008.

Required reading:

- Entire board, controlling plan, changed module indexes/registries, and all prior task receipts.
- Root and Product `AGENT_INDEX.md` files.
- `Makefile` check targets and workspace validation commands.

## Scope

In:

- Update root, Product, reasoning, skill, and Concept Lab navigation where needed.
- Reconcile all capability and implementation statuses with observed files.
- Add a final v1 registration/verification receipt with operator evaluator results.
- Run the full repository check and a manual fresh-agent invocation review.
- Close board tasks only when their individual evidence already satisfies all gates.

Exact closeout files:

- `AGENT_INDEX.md`
- `workspaces/concept-lab/AGENT_INDEX.md`
- `workspaces/concept-lab/artifacts/v1-registration-receipt.yaml`
- `workspaces/concept-lab/artifacts/source_manifest.yaml`
- `workspaces/concept-lab/resource_registry.json`
- `workspaces/testflight-product/AGENT_INDEX.md`
- `workspaces/testflight-product/architecture/artifacts/system-inventory.yaml` only if its status
  still says planned after the implementation is observed
- Existing registries that must reference the final receipt
- `docs/workboards/concept-lab-v1/` task, lane, decision, update, and handoff state

If verification reveals a defect in another implementation file, return that defect to its owning
task rather than hiding the repair in closeout.

Out:

- Live projection, runtime deployment, new capabilities, or cleanup unrelated to Concept Lab v1.
- Calling retrieval “certified” without a populated staging projection.

## Acceptance Criteria

- Repository and module indexes route Concept Lab requests correctly.
- Product records say exactly which v1 pieces are implemented and which remain deferred.
- All source URLs and IDs resolve; no navigation file acts as domain evidence.
- Targeted validations and `make check` pass.
- Final receipt separates structure, invariants, semantic continuity, usefulness, and live
  retrieval status.
- Git status is clean after the final focused commit.

## Plan

- Claim only after TASK-008.
- Audit rather than redesign; send defects back to their owning task.
- Run targeted checks first, then `make check`.
- Perform a fresh-context manual scenario: invoke `$concept-lab`, select the relational-content
  child, form a proposal, and trace it back.
- Record residual risks and close the board.

Failure mode: closeout labels local fixtures as live retrieval or equates schema success with a
useful conversational experience.

Verification commands:

- `uv run python scripts/validate_concept_lab.py`
- `uv run python scripts/validate_reasoning_operators.py`
- `uv run python scripts/validate_skill_catalog.py`
- `uv run python scripts/validate_testflight_product_workspace.py`
- `make check`
- `git diff --check`

## Verification Evidence

- Not run yet.

## Updates

- Created: `2026-09-08T09:53:07.959732+00:00`

## Handoff Notes

- Final handoff must list deferred runtime/UI/projection work and the exact invocation syntax.
