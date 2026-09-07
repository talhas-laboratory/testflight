# TASK-020-connect-accepted-field-to-artifact-context: Connect an accepted field to artifact context

Status: done
Owner: talha
Current gate: done

## Problem

An accepted Creative Field version existed, but Creative Studio had no application command to
connect it to project/entity scope or feed it into the existing artifact context compiler.

## Scope

In:

- add a project-scoped `project_field` command consuming explicit entities, project/field binding
  data, a world-view result, request metadata and target capability manifest;
- resolve bindings through `CreativeBindingResolver` with workspace, context, version, selector,
  time and precedence checks;
- compile `FieldProjection`, `ResolvedCreativeRequest` and `CreativeContextPacket` through the
  existing `CreativeContextCompiler`;
- persist bindings and compiled records as an idempotent batch and hydrate projection status after
  restart;
- keep missing versions, unknown entities, policy mismatches and unsupported targets held or
  unavailable rather than inventing context.

Out:

- live Brand-world lookup (the command receives a bounded entity/world-view packet);
- target translation, provider invocation or output evaluation;
- a rich projection editor UI.

## Acceptance Criteria

- An accepted project field can be explicitly bound to canonical entity IDs and context scope.
- A valid artifact request produces a target-neutral projection and context packet containing field
  grounding, world-view records, omissions and conflicts.
- Binding/compiler failures do not persist fabricated records.
- Persisted binding and packet state replays after a new Creative Studio store is created.
- Existing project/version/review behavior and the full release gate remain green.

## Verification Evidence

- `uv run pytest apps/creative-studio/tests -q` — 19 Creative Studio tests passed, including
  accepted-version binding, packet compilation, restart hydration and missing-version hold.
- `make check` — passed: 134 Python tests, all TypeScript checks/tests, validators, certification
  and Compose validation. The environment reports a non-blocking Node 22 versus repository
  `>=24` engine warning.
- `git diff --check` and JSONL update validation — passed.

## Changed Files

- `apps/creative-studio/src/testflight_creative_studio/server.py`
- `apps/creative-studio/tests/test_server.py`
- `docs/workboards/moodboard-creative-field-implementation/DECISIONS.md`

## Residual Risks

- Entity/world-view data is still supplied by the caller; a context-intelligence adapter must
  resolve it from the Brand world before production use.
- Projection state is persisted but the UI has no request/binding form yet.
- Generation packet translation, target execution and evaluation remain the next artifact-workflow
  slice.

## Handoff Notes

Next, resolve explicit `ProjectBinding` and `FieldBinding` records from the live Brand world, then
compile a capability-honest `GenerationPacket` for one text/image target.
