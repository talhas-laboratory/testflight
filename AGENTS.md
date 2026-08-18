# Working agreements

- Preserve modular boundaries: upstream-specific imports stay inside their adapter.
- Add or update `upstreams/registry.yaml` before introducing an external runtime dependency.
- Do not commit secrets, `.env` files, databases, model weights, or generated knowledge stores.
- Prefer a released package or container. Document any submodule, fork, or vendored patch in an
  architecture decision record.
- New adapters need a descriptor, a dependency-free health probe, documentation, and tests.
- Run `make check` before committing.
