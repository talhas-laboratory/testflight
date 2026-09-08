# Gates

Every task must pass these gates before it is treated as complete.

## Intake Gate

- Problem is stated in one sentence.
- Scope-in and scope-out are explicit.
- Owner or active agent is named.
- Dependencies and unknowns are listed.

## Readiness Gate

- Relevant repo files or docs are linked.
- Test strategy is named before implementation.
- Failure mode is described.
- Acceptance criteria are concrete and inspectable.
- Every dependency task is `done` with verification evidence.
- Exact files allowed for the task are listed in its packet.

## Implementation Gate

- Changes are scoped to declared files.
- New abstractions are justified by repeated complexity or a local pattern.
- User or unrelated worktree changes are preserved.
- Updates are recorded in `UPDATES.jsonl`.
- No live provider, projection, or external action occurred.
- Formation outputs remain proposals and cannot perform canonical product writes.

## Verification Gate

- Commands run are listed exactly.
- Results are recorded, including failures.
- Manual checks include artifact paths or screenshots when relevant.
- Known residual risks are stated.
- Semantic continuity is evaluated separately from schema validity.
- Cross-workspace denial and no-hit behavior are exercised where relevant.

## Review Gate

- Another agent or reviewer can understand the task from the task packet alone.
- Decision log is updated for architectural choices.
- Handoff notes describe what changed and what remains.

## Done Gate

- Acceptance criteria are satisfied.
- Verification evidence is attached.
- Task file, `TASKS.md`, and lane placement agree.
- No hidden follow-up is required for the stated scope.
