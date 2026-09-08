# TASK-004-add-the-controlled-testflight-product-bridge: Add the controlled Testflight Product bridge

Status: done
Owner: codex
Current gate: implementation

## Problem

Concept Lab and Testflight Product need useful two-way exchange without shared mutable records,
implicit traversal, or promotion of theory into accepted product knowledge.

Dependencies: TASK-002 and TASK-003.

Required reading:

- Controlling plan, ADR 0007, and Concept Lab packet contracts.
- `packages/testflight-semantic/src/testflight_semantic/federation.py`
- Product module contracts for product-definition, architecture, research-learning, and
  product-decisions.
- `workspaces/testflight-product/artifacts/extension-contract.yaml`

## Scope

In:

- Add a Concept Lab federation registry with two explicit bridge records: Product inquiry to Lab,
  and Lab formation proposal to Product.
- Set cross-workspace traversal false by default; packet source refs are the only imported context.
- Define target-module routing and explicit human promotion authority.
- Register the planned capability, architectural components, research question, and bridge source
  in the existing Product modules without adding a new Product child.

Exact implementation files:

- `workspaces/concept-lab/artifacts/testflight-product-bridge.yaml`
- `workspaces/concept-lab/artifacts/federation-registry.yaml`
- `workspaces/concept-lab/artifacts/source_manifest.yaml`
- `workspaces/concept-lab/resource_registry.json`
- `workspaces/testflight-product/product-definition/artifacts/capability-inventory.yaml`
- `workspaces/testflight-product/product-definition/artifacts/source_manifest.yaml`
- `workspaces/testflight-product/product-definition/resource_registry.json`
- `workspaces/testflight-product/architecture/artifacts/system-inventory.yaml`
- `workspaces/testflight-product/architecture/artifacts/source_manifest.yaml`
- `workspaces/testflight-product/architecture/resource_registry.json`
- `workspaces/testflight-product/research-learning/artifacts/research-catalog.yaml`
- `workspaces/testflight-product/research-learning/artifacts/source_manifest.yaml`
- `workspaces/testflight-product/research-learning/resource_registry.json`
- `workspaces/testflight-product/resource_registry.json`

Out:

- Canonical Product mutation from a Lab packet.
- Parent-wide or bidirectional automatic retrieval.
- New federation package types unless the existing FederationBridge cannot validate the instance.

## Acceptance Criteria

- Both workspaces remain valid independently when the other contributes no packet.
- Every bridge names source, target, context, subject, predicate, object, evidence refs, and
  authority state.
- Traversal is false without a separate grant.
- Formation targets route only to existing Product modules.
- Product records describe the implementation accurately as partial/planned.

## Plan

- Claim only after both dependencies are done.
- Instantiate existing FederationBridge records before proposing any new bridge primitive.
- Add the richer inquiry/formation exchange contract as payload policy, not federation identity.
- Update only owning Product modules and their registries.
- Validate federation models and the entire Product workspace; commit one task.

Failure mode: a registry reference is treated as permission or a FormationPacket writes accepted
Product state. Reject this in schema and fixtures.

Verification commands:

- Pydantic validation of the federation registry using `testflight_semantic.FederationRegistry`
- `uv run python scripts/validate_testflight_product_workspace.py`
- `uv run python scripts/audit_testflight_product_routes.py --summary`
- `git diff --check`

## Verification Evidence

- Federation registry validates with `testflight_semantic.FederationRegistry`; both bridge records set `allow_traversal: false`.
- Product workspace validation passed with no live projection change.
- Product route audit passed: 10/10 checks, zero routing errors.
- `git diff --check` passed.

## Updates

- Created: `2026-09-08T09:53:07.958821+00:00`
- Claimed: `2026-09-08T11:00:00Z` by codex.
- Completed: `2026-09-08T11:08:00Z` by codex.

## Handoff Notes

- Do not mark TASK-007 ready; it also requires TASK-005 and TASK-006.
