# Testflight World

`testflight-world` owns the provider-neutral transition layer for the Brand World v3 grammar.
It coordinates reviewable change sets, explicit approval or rejection, append-only record history,
branch merges, and scoped canonical reads. It does not define Brand meanings, compile agent context,
call a model, or persist data through a specific database.

## Boundary

- `testflight-semantic` owns the shared World record grammar.
- `domains/brand/ontology-v3` owns the candidate Brand domain vocabulary.
- `testflight-world` owns the proposal-to-accepted transition.
- `adapters/sqlite-semantic` implements `WorldRepository` for durable local storage.
- Legacy Brand ontology releases are read-only migration inputs; they must not be written through
  this package.

## Invariant

No record becomes accepted through a direct write. A `WorldChangeSet` must first be proposed and
then receive an approved `WorldDecision` in the same workspace and branch with an authority
reference. That reference is resolved through the injected `AuthorityGrantResolver`; approval
fails closed if the grant is unknown, expired, bound to another principal, lacks `promote` or
`accept`, or does not cover every affected record and context. The decision actor (`created_by`)
must be the grant principal. A successful receipt records the exact grant and capability used.
The service then records the resulting accepted version in history.

Supersession and branch merges always create proposals; neither operation can silently promote its
result. Reads require a workspace and branch where ambiguity would cross a boundary. Snapshots can
be reconstructed at a recorded-time cutoff, and evidence, relations, dependencies, diffs, state,
and bounded lexical search are explicitly labeled canonical or analytical results.

The SQLite adapter indexes history by workspace, branch, record identity, version, and recorded
time. Acceptance checks the current proposal status and every expected record version inside one
transaction. The in-memory repository remains a deterministic reference implementation only.

## Applied reasoning guardrails

This implementation records the operators that materially shaped its persisted behavior:

- `world://operator/guardrail/validation-persistence-conflation` v1: schema-valid proposals remain
  distinct from reviews and authorized acceptance. Evaluator result: pass; held, rejected, stale,
  and unauthorized paths cannot append accepted history through `WorldService`; in-memory and
  SQLite zero-partial-write tests cover unknown, expired, wrong-principal, wrong-capability,
  out-of-scope, and wrong-context grants.
- `world://operator/guardrail/workspace-isolation` v1: history identity includes workspace and
  branch. Evaluator result: pass; equal record IDs in separate branches reconstruct independently.
- `world://operator/guardrail/version-state-conflation` v1: immutable history, current snapshots,
  diffs, and branch merge proposals are separate objects. Evaluator result: pass; stale revisions
  are rejected and recorded-time replay is covered by both reference and SQLite tests.
- `world://operator/guardrail/retrieval-reasoning-conflation` v1: lexical search is bounded and
  returns matched canonical records plus match metadata without synthesis. Evaluator result: pass;
  empty and unbounded requests are rejected.
