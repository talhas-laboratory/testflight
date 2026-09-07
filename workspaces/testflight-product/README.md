# Testflight Product workspace

This is the canonical product brain for people and agents building Testflight. It gives product
work a shared ontology, modular retrieval routes, explicit decisions, and one design language
across Brand Intake, Brand Lab, Creative Studio, and future surfaces.

Start with:

- `AGENT_INDEX.md` to route a task;
- `AGENT_CONFIG.yaml` for retrieval, mutation, and quality policy;
- `WORKSPACE.yaml` for identity, scope, and topology;
- `artifacts/product-ontology.yaml` for semantic types and relations;
- `artifacts/source-catalog.yaml` for evidence authority and limitations;
- `artifacts/entity-inventory.yaml` for the project-wide routed entity map;
- `artifacts/coverage-audit.yaml` for known completeness and evidence gaps;
- `artifacts/module-registry.yaml` before adding or changing a module; and
- `artifacts/extension-contract.yaml` before creating a child workspace.

The repository is canonical. Generated indexes, vector stores, graphs, caches, and databases are
rebuildable projections and must remain under ignored runtime state.

## Local validation

```bash
uv run python scripts/validate_testflight_product_workspace.py
uv run python scripts/populate_testflight_product_workspace.py --dry-run
```

No command above changes a live external store.

The workspace is populated from the repository as of 2026-09-04. It intentionally keeps the
current integration-laboratory identity, proposed Founder Brand World product, and researched
Campaign Decision Intelligence wedge distinct. Customer, financial, and growth records remain
partial until interviews, paid pilots, contracts, usage, and observed outcomes exist.
