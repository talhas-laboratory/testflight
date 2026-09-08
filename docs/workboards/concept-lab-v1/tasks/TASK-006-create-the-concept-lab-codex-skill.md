# TASK-006-create-the-concept-lab-codex-skill: Create the concept-lab Codex skill

Status: done
Owner: codex
Current gate: implementation

## Problem

The user needs a lightweight, reliable Codex entry point that immediately adopts Concept Lab
language and can route requests to transformations without embedding evolving knowledge in prompt
instructions.

Dependencies: TASK-003 and TASK-005.

Required reading:

- Controlling plan, Concept Lab workspace index, and all four operator contracts.
- System `skill-creator/SKILL.md` and `references/openai_yaml.md`.
- `.agents/skills/AGENT_CONFIG.yaml`, catalog, index, and validator.
- Official Codex skill guidance linked from the controlling discussion.

## Scope

In:

- Create a repo-local `concept-lab` skill with automatic discovery enabled.
- Ensure explicit `$concept-lab` and natural phrases such as “enter the Concept Lab” are strongly
  represented in the description and UI prompt.
- Define five modes: explore, distill, formalize, form, and trace.
- Put stable language, mode, routing, and formation-target guidance in focused references.
- Register the skill in the flat repo-local catalog and index.

Exact implementation paths:

- `.agents/skills/concept-lab/SKILL.md`
- `.agents/skills/concept-lab/agents/openai.yaml`
- `.agents/skills/concept-lab/references/`
- `.agents/skills/catalog.yaml`
- `.agents/skills/AGENT_INDEX.md`

Out:

- Domain knowledge copied into the skill.
- Persistent enter/exit runtime state, scripts without repeated deterministic need, provider calls,
  or implicit authorization to persist/publish.

## Acceptance Criteria

- The description discriminates Concept Lab requests from ordinary brainstorming or coding.
- `$concept-lab` is present in the default prompt and the skill validates.
- Each mode names required inputs, operator route, output type, and honest non-success outcomes.
- The skill loads the smallest domain child and only then any explicit Product bridge packet.
- A fresh Codex instance can follow the skill without reading this conversation.

## Plan

- Claim after both dependencies are done.
- Initialize the skill with only `references`; do not create unused assets or scripts.
- Keep SKILL.md short and route conditional detail progressively.
- Add catalog metadata and static trigger scenarios.
- Run both skill validators and commit one task.

Failure mode: the skill becomes a second knowledge store, activates for generic analysis, or
promises persistent mode state that native skills do not provide.

Verification commands:

- skill creator `quick_validate.py` against `.agents/skills/concept-lab`
- `uv run python scripts/validate_skill_catalog.py`
- targeted trigger/route tests added by TASK-007, not this task
- `git diff --check`

## Verification Evidence

- `python3 /Users/talhauddin/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/concept-lab` passed.
- `uv run python scripts/validate_skill_catalog.py` passed: 2 repo-local skills validate.
- `git diff --check` passed.

## Updates

- Created: `2026-09-08T09:53:07.959179+00:00`
- Claimed: `2026-09-08T11:12:00Z` by codex.
- Completed: `2026-09-08T11:17:00Z` by codex.

## Handoff Notes

- TASK-007 is ready because TASK-004 and TASK-005 are done.
