# Brand workspace template

This is a tracked template for one isolated Brand workspace. It contains routing, policy, source
metadata, and certification cases. It deliberately contains no real Brand, source evidence,
credentials, database, model output, or generated Cognee state.

The provider-neutral source of truth is under [`domains/brand/`](../../domains/brand/). A concrete
workspace should be initialized from this template, assigned a real workspace/Brand ID, and
projected to a dataset named by its manifest. Cognee is a rebuildable projection, not the
canonical ontology or evidence repository.
