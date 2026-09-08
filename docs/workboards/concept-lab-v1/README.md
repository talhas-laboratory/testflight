# Concept Lab v1

Purpose: implement the repository-native Concept Lab v1 through small, dependency-ordered task
packets with enough local context for a smaller model to execute safely.

Board id: `concept-lab-v1`
Owner: `talha`
Created: `2026-09-08T09:53:07.955612+00:00`

Controlling plan: `docs/plans/2026-09-08-concept-lab-v1-implementation-plan.md`

## V1 Boundary

V1 consists of a repo-local skill, provider-neutral domain contracts, a sovereign Concept Lab
workspace with one proof child, four transformation operators, an explicit Testflight Product
proposal bridge, deterministic validation, and a Biotic rehearsal. It does not include a UI,
provider call, live projection, persistent mode runtime, or automatic product mutation.

## Agent Start Protocol

1. Read `README.md`, `TASKS.md`, `GATES.md`, `DECISIONS.md`, and the latest entries in `UPDATES.jsonl`.
2. Select only a task whose dependencies are done; claim it by editing its task file and adding an
   update row.
3. Work only inside the task scope unless the board owner expands it.
4. Record decisions before relying on them.
5. Attach verification evidence before moving a task to `review` or `done`.
6. Use one focused commit per task. Do not combine tasks even when adjacent changes look small.

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
