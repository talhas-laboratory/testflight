# Brand workspace operations

This guide describes the first working slice of the system-theoretic Brand infrastructure. It
is intentionally small: the ontology, evidence boundary, accepted assertion repository, and
Cognee projection are usable now; LangGraph orchestration and provider-specific extraction remain
replaceable follow-on modules.

## Validate and initialize

From the repository root:

```bash
uv sync --all-packages
uv run brand-lab validate --root .
uv run brand-lab init acme --output /srv/testflight/workspaces/acme
```

`brand-lab init` copies the tracked template, substitutes the workspace slug, and refuses to
overwrite an existing directory. The resulting `WORKSPACE.yaml` names the ontology and policy
versions and derives the Cognee dataset name (`testflight_brand_<slug>_p1`).

The synthetic fixture is a deterministic smoke test for the domain boundary:

```bash
uv run brand-lab certify --root .
```

Certification checks that declared component IDs, relationship definitions, endpoint types,
evidence references, perspectives, and contradiction links are internally consistent. It does not
claim that a real Brand source has been extracted or evaluated.

## Canonical write path

1. Create an `EvidenceEnvelope` for each source and store its UTF-8 content with
   `SemanticRepository.put_envelope`. The SHA-256 hash and all source metadata are immutable for
   a `source_id`.
2. Store exact `EvidenceSpan` records for quotes used by extraction or review.
3. Produce `BrandAssertion` proposals. Keep perspective, epistemic status, evidence IDs,
   contradictions, valid time, and the separate relationship-weight dimensions on the proposal.
4. Accept only after schema, invariant, semantic, and usefulness checks; then call
   `append_assertions`. Held, partial, unresolved, and hypothesized records remain outside
   canonical accepted state.

The repository is deliberately independent of Cognee. It makes retries idempotent and permits a
projection to be discarded and rebuilt without losing evidence or accepted state.

## Cognee projection

Use `testflight_adapter_cognee.brand_projection` to map `BrandSystem`, `BrandComponent`, and
accepted `BrandAssertion` records to lazy Cognee `DataPoint` classes. Persist assertion nodes for
evidence-oriented retrieval and optionally pass `brand_assertion_custom_edges(...)` as
`custom_edges` for bounded endpoint traversal. Direct edges carry assertion ID, relation
definition, perspective, epistemic status, and the structural/evidence score dimensions; they do
not collapse those dimensions into truth or a single weight.

Rebuild the projection from the SQLite repository into a new dataset version, certify it, and only
then switch the active dataset reference. Do not put Cognee `.data`, SQLite files, source evidence,
or model output in Git.

## Runtime placement

The repository and generated state belong under the server runtime root from the workspace
manifest (for example `/home/talha/testflight/.data/brand-workspaces/acme`). The Git checkout on
the Mac and the checkout on `home-server` contain code, ontology, policy, templates, and tests
only. Synchronize code with `make sync-server`; copy or back up runtime state using a separate,
explicit data operation.
