# Nike Brand research sandbox

This is an isolated, proposal-only workspace used to exercise every entity and relationship type
in Brand ontology version `1.0.0` against public information about the NIKE Brand.

It does not claim to be Nike's internal brand system. Public corporate statements are represented
as intended or reported claims; independent measurements remain observed or reported perceptions;
researcher synthesis remains inferred or hypothesized. Conflicts and time boundaries are retained.

## Contents

- `artifacts/source-catalog.yaml`: registered external sources and permitted uses;
- `artifacts/evidence-notes.yaml`: bounded excerpts, paraphrases, authority, and limitations;
- `artifacts/context-profiles.yaml`: reusable time, audience, channel, and campaign scopes;
- `artifacts/entity-inventory.yaml`: proposals covering all eight current entity types;
- `artifacts/relationship-inventory.yaml`: proposals covering all fourteen relationship types;
- `artifacts/asset-workflow-context.yaml`: stage-specific context requirements for asset creation;
- `artifacts/coverage-matrix.yaml`: completeness and release gates; and
- `artifacts/world-modeling.yaml`: branch-aware, perspective-aware semantic overlays used before retrieval and synthesis; and
- `certification_cases/probes.yaml`: retrieval and safety probes.

Start with `AGENT_INDEX.md` for routing and `AGENT_CONFIG.yaml` for retrieval policy. The intended
Cognee projection is the isolated dataset `testflight_brand_nike_research_staging`; it is not a
canonical Brand dataset. The eight registered research documents were populated on 2026-08-25
after local validation passed. This does not promote any proposal into canonical Brand state.

`world-modeling.yaml` is now registered for the next isolated projection rebuild. Until that
rebuild is run, the live staging dataset may not contain this newer document; the deterministic
world-view compiler reads the canonical file directly and records the distinction.

## Reuse

Validate this pack with `make nike-research-workspace`. Materialize another concrete Brand pack
with `scripts/populate_concrete_brand_workspace.py --dry-run --workspace <workspace-path>` after
using the same manifest, registry, evidence, context, entity, relationship, workflow, and probe
contracts. Staging population requires an explicit `*_staging` dataset and the server's isolated
Cognee runtime.

## Research date

Sources were last checked on 2026-08-25. Time-sensitive strategy, leadership, campaign, market,
competitor, and perception records require refresh rather than silent reuse after their validity
window.
