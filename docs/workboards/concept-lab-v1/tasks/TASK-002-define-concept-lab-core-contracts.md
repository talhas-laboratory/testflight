# TASK-002-define-concept-lab-core-contracts: Define Concept Lab core contracts

Status: done
Owner: codex
Current gate: implementation

## Problem

The Lab needs small provider-neutral records for concepts and bidirectional formation without
duplicating Testflight's existing semantic, content, federation, or authority primitives.

Dependencies: TASK-001.

Required reading:

- Controlling plan and ADR 0007.
- `packages/testflight-semantic/src/testflight_semantic/federation.py`
- `packages/testflight-semantic/src/testflight_semantic/representation.py`
- `reasoning/operator-contract.yaml`
- `domains/creative-field/manifest.yaml`
- `packages/testflight-content/README.md`

## Scope

In:

- Create the candidate Concept Lab domain manifest, vocabulary, and contract inventory.
- Define ConceptFragment, ConceptDefinition, ConceptRelation, TheoryBranch, TransformationRun,
  InquiryPacket, FormationPacket, and ReverseTrace.
- Express composition with existing IDs and refs rather than redefining Evidence, Context,
  WorldBranch, Derivation, AuthorityGrant, ContentUnit, KnowledgeContainer, or FederationBridge.
- Declare lifecycle states, required provenance, and forward/reverse continuity invariants.

Exact implementation files:

- `domains/concept-lab/README.md`
- `domains/concept-lab/manifest.yaml`
- `domains/concept-lab/vocabulary.yaml`
- `domains/concept-lab/contracts.yaml`

Out:

- Pydantic/TypeScript implementation, persistence, retrieval, UI, operators, or workspace records.
- Treating the Biotic case as a universal domain definition.

## Acceptance Criteria

- Every new type has one purpose, owner, required fields, lifecycle, and source/derivation rule.
- Every reused primitive is referenced by its existing owner.
- FormationPacket requires `target_workspace_id`, `target_module_id`, alternatives, evaluations,
  authority status, and `canonical_write: false`.
- ReverseTrace requires a resolvable chain through technical, formal, theoretical, interpretive,
  and source layers, with explicit missing links.
- YAML parses and no contract implies runtime implementation.

## Plan

- Claim the task after TASK-001 is done.
- Inventory existing primitives and record reuse mappings before adding types.
- Define only the minimum fields required by the five v1 modes and test fixture.
- Review for type conflation and storage-language leakage.
- Parse all YAML, run reasoning-operator validation as a compatibility check, and commit one task.

Failure mode: creating a second Evidence, Branch, Derivation, or Federation schema with different
meaning. Stop and reuse or compose the existing primitive.

Verification commands:

- `uv run python -c 'import pathlib,yaml; [yaml.safe_load(p.read_text()) for p in pathlib.Path("domains/concept-lab").glob("*.yaml")]'`
- `uv run python scripts/validate_reasoning_operators.py`
- `git diff --check`

## Verification Evidence

- `uv run python -c 'import pathlib,yaml; [yaml.safe_load(p.read_text()) for p in pathlib.Path("domains/concept-lab").glob("*.yaml")]'` passed.
- `uv run python scripts/validate_reasoning_operators.py` passed: 24 existing operators remain valid.
- `git diff --check` passed.

## Updates

- Created: `2026-09-08T09:53:07.958292+00:00`
- Claimed: `2026-09-08T10:22:00Z` by codex.
- Completed: `2026-09-08T10:28:00Z` by codex.

## Handoff Notes

- TASK-003 and TASK-005 are ready. TASK-004 remains backlog until TASK-003 is done.
