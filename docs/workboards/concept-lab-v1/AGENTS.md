# Agent Rules

- Prefer sparse, high-signal updates over verbose status narratives.
- Keep task packets self-contained enough for another agent to resume.
- Update board state as part of the work, not after memory fades.
- Use append-only updates for activity history; edit task files for current state.
- Preserve provenance for imported context and sidecar work.
- Do not mark work done without test or verification evidence.
- Escalate blockers early with the smallest concrete question.
- Read `docs/plans/2026-09-08-concept-lab-v1-implementation-plan.md` before claiming work.
- Work on exactly one task packet and its declared files.
- Treat the plan's fixed decisions as constraints; record any required deviation in `DECISIONS.md`
  before implementing it.
- Do not infer that the Concept Lab, Testflight Product, or a brand workspace may read or write the
  others. Use only explicit bridge packets.
- Do not populate live retrieval state or add a model/runtime dependency in v1.
- Prefer typed `hold`, `branch`, `ask`, `partial`, and `no_hit` outcomes to invented completion.
- Preserve source, authority, scope, time, branch, uncertainty, and derivation in every handoff.
