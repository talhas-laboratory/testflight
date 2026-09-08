# TASK-003-create-the-concept-lab-workspace-and-first-domai: Create the Concept Lab workspace and first domain child

Status: done
Owner: codex
Current gate: implementation

## Problem

The domain contracts need a canonical, independently valid knowledge workspace that can add
isolated theory domains without turning the root into an unbounded conversation dump.

Dependencies: TASK-002.

Required reading:

- Controlling plan, ADR 0007, and `domains/concept-lab/*`.
- `.agents/skills/child-container-creator/SKILL.md` and its contract reference.
- `workspaces/testflight-product/WORKSPACE.yaml` for parent workspace conventions.
- `workspaces/brand-hellobiotic-research/content-strategy/AGENT_INDEX.md` for proof-source scope.

## Scope

In:

- Create the sovereign `world://workspace/concept-lab` parent with explicit identity, authority,
  retrieval, topology, source registry, quality gates, and staging dataset.
- Scaffold one child: `world://workspace/concept-lab/relational-content`.
- Add task views or artifact routes for source capture, theory, formation, trace, and review only
  when they reduce routing ambiguity.
- Keep the proof child structurally valid but unpopulated until bridge and rehearsal tasks.

Exact implementation paths:

- `workspaces/concept-lab/` canonical workspace pack.
- `workspaces/concept-lab/relational-content/` child-container pack.
- No other workspace.

Out:

- Importing Biotic records, registering the Product bridge, live Cognee population, or retrieval
  certification.
- Global active-session state or personal data.

## Acceptance Criteria

- Parent and child IDs, datasets, routes, and registries are disjoint and explicit.
- Parent search never broadens an in-domain child no-hit.
- Navigation/config sources are rejected as ordinary domain answers.
- Child scaffold validation passes while certification remains honestly not run.
- Generated state is absent from the commit.

## Plan

- Claim the task after TASK-002 is done.
- Create the parent contract manually from existing workspace conventions.
- Dry-run the child scaffold helper with an absolute parent path; inspect; then apply.
- Register the child manually in parent topology and registry.
- Add exact, intent, adversarial-navigation, and out-of-domain probe placeholders.
- Validate parent identity and child structure; commit only canonical files.

Failure mode: the root workspace becomes a generic store for all conversation material. Every
source must resolve to a project/domain route or return `ask`/`no_hit`.

Verification commands:

- `python3 .agents/skills/child-container-creator/scripts/validate_child_container.py workspaces/concept-lab/relational-content`
- targeted YAML/JSON parse over `workspaces/concept-lab`
- `git diff --check`

## Verification Evidence

- The child-container scaffold helper dry run and apply both reported only the expected six
  canonical child files, the isolated `testflight_concept_lab_relational_content_staging` dataset,
  and no live projection change.
- `python3 .agents/skills/child-container-creator/scripts/validate_child_container.py workspaces/concept-lab/relational-content` passed in structural mode: zero resources, four planned probes, and no errors.
- Targeted YAML/JSON parsing and `git diff --check` passed.

## Updates

- Created: `2026-09-08T09:53:07.958541+00:00`
- Claimed: `2026-09-08T10:33:00Z` by codex.
- Completed: `2026-09-08T10:39:00Z` by codex.

## Handoff Notes

- TASK-004 is ready because TASK-002 and TASK-003 are done. TASK-006 still waits for TASK-005.
