# Working agreements

- Start repository-wide discovery at `AGENT_INDEX.md`, then route to the smallest owning module.
- Keep `AGENT_INDEX.md` current when adding, removing, renaming, or materially reconnecting a
  module, application, adapter, domain, workspace, operator runtime, or workflow layer.
- Preserve modular boundaries: upstream-specific imports stay inside their adapter.
- Add or update `upstreams/registry.yaml` before introducing an external runtime dependency.
- Do not commit secrets, `.env` files, databases, model weights, or generated knowledge stores.
- Prefer a released package or container. Document any submodule, fork, or vendored patch in an
  architecture decision record.
- New adapters need a descriptor, a dependency-free health probe, documentation, and tests.
- Run `make check` before committing.
- Server access uses the endpoint documented in `.env.example`; never add credentials to this
  file or any tracked file.

## Reasoning operators

- For semantic extraction, architecture, retrieval, persistence, or agent-runtime work, read
  `reasoning/README.md` and route the task through the smallest relevant operator in
  `reasoning/operators/index.yaml`.
- Operators are portable contracts, not prompt memory. Preserve source evidence, authority,
  scope, time, relations, branches, uncertainty, and derivation across every handoff.
- Treat `hold`, `branch`, `ask`, `partial`, and `no_hit` as valid outcomes. Do not repair a
  semantic gap with an invented fact or silently commit a proposal.
- Record the operator id/version and evaluator results when an operator influences a persisted
  artifact or material answer.
- For workspace/container population, read `workspaces/reasoning-operators/README.md` and keep
  `reasoning/operators/` as the source of truth; rebuild Cognee projections instead of editing
  generated `.data/` state.

## Testflight product workspace

- For product strategy, product decisions, user-facing experience, architecture, customers,
  marketing, finance, or operations work, start at `workspaces/testflight-product/AGENT_INDEX.md`
  and route to the smallest child module.
- Keep knowledge modules, product capabilities, implementation modules, and UI components as
  distinct semantic types. Add new product modules through
  `workspaces/testflight-product/artifacts/extension-contract.yaml`.
- For every user-facing application or artifact, load the active experience-design contract and
  consume `packages/testflight-design-language`; record exceptions as product-decision proposals.
- Never treat Testflight product language as evidence about a customer or brand workspace. Use an
  explicit, scoped, provenance-bearing bridge for every cross-workspace transfer.
