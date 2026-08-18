# Adding an upstream project

1. Confirm the project has an acceptable license and an active source repository.
2. Add its immutable release and commit to `upstreams/registry.yaml`.
3. Choose the least invasive integration mode: package, container, plugin, submodule, or fork.
4. Create `adapters/<id>/` with a descriptor and dependency-free health probe.
5. Keep all upstream imports inside that adapter.
6. Add contract tests and an explicit networked smoke test when useful.
7. Record an ADR for submodules, forks, vendored code, or shared infrastructure.
8. Run `make check`.

An experiment may start under `experiments/YYYY-MM-<topic>/`, but reusable code should be
promoted only after its contract is understood.
