# Moodboard Creative Field Implementation

Purpose: deliver the Moodboard -> Creative Field -> Field Connector vertical slice while preserving
project scope, evidence lineage, review authority, provider replaceability, and Brand-world integration.

Board id: `moodboard-creative-field-implementation`
Owner: `talha`
Created: `2026-09-03T16:28:24.772988+00:00`

Implementation plan:
[`../../plans/2026-09-03-moodboard-creative-field-implementation-plan.md`](../../plans/2026-09-03-moodboard-creative-field-implementation-plan.md)

Approved source design: `/home/talha/repos/mindscape/docs/product-profiles/moodboard-creative-field/architecture/SYSTEM_DESIGN.md`
on `home-server`.

## Delivery Blocks

1. **A — contracts and local lifecycle:** TASK-001 through TASK-004.
2. **B — board to reviewed field:** TASK-005 through TASK-007.
3. **C — world and artifact integration:** TASK-008 and TASK-009.
4. **D — human and connector loop:** TASK-010 and TASK-011.
5. **E — projection and certification:** TASK-012 and TASK-013.

TASK-001 is the first task. Later tasks may be refined in parallel, but implementation must respect
the dependencies in `TASKS.md`.

## Agent Start Protocol

1. Read `README.md`, `TASKS.md`, `GATES.md`, `DECISIONS.md`, and the latest entries in `UPDATES.jsonl`.
2. Claim one task by editing its task file and adding an update row.
3. Work only inside the task scope unless the board owner expands it.
4. Record decisions before relying on them.
5. Attach verification evidence before moving a task to `review` or `done`.

## Board Shape

- `TASKS.md`: board index and task status
- `lanes/`: Asana/Jira-style task lanes
- `tasks/`: one durable task packet per work item
- `GATES.md`: mandatory requirements and verification gates
- `DECISIONS.md`: Confluence-style decision log
- `UPDATES.jsonl`: append-only activity feed
- `HANDOFFS.md`: transfer notes between agents
- `AGENTS.md`: agent operating rules for this board
- `artifacts/`: plans, outputs, screenshots, logs, generated files
- `inbox/`: untriaged notes, imported context, pending requests
