# Working agreements

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
