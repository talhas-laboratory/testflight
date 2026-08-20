# Brand ontology research workspace

This is the proposal and certification container for Brand Ontology v0.1. It is intentionally
separate from a real Brand workspace: research claims, candidate definitions, and synthetic worlds
must not be mistaken for accepted Brand-world assertions.

The constitution remains the architectural authority. The workspace adds the operational research
loop:

```text
source
  → candidate definition
  → independent evaluation
  → competency questions + synthetic worlds
  → accept | hold | reject | deprecate
```

Every source is registered with provenance and an evidence tier. Every candidate must have inclusion
and exclusion meaning, examples, counterexamples, allowed endpoints when relevant, and a mapping to
at least one competency question. Promotion is explicitly authorized and append-only.

The pack is currently `pack_only_until_certified`. Do not create or edit generated `.data/` state
as part of a source change. Once the pack passes certification, a dedicated population command may
rebuild the Cognee dataset `testflight_brand_ontology_research` from this Git revision.

The first population slice is a 24-source Tier A anchor catalog, bounded evidence notes and
proposal-only candidate definitions. Validate it with `make brand-research-corpus`. The source
search order, batch sequencing, diversity audit and stopping rule are in
[`artifacts/research-playbook.md`](artifacts/research-playbook.md).

The nine synthetic worlds are now executable and certified with:

```bash
make brand-research-fixtures
```

Their builders live in `scripts/brand_ontology_fixtures.py`; they exercise perspective separation,
bitemporal history, shared identity, adaptive representation, portfolio scope, evidence conflict,
causal guardrails and representation conflicts. Fixture certification remains separate from Cognee
projection certification.

The projection materializer is deterministic and credential-free in its safe modes:

```bash
make brand-research-projection
```

It currently produces 11 bounded research documents from the tracked pack. On the server, use
`make setup-server-brand-research ARGS="--dry-run"` after the isolated Cognee environment exists. The
`--populate` mode is intentionally gated until projection retrieval is separately certified and
the workspace manifest is explicitly authorized.

Start with:

- [`AGENT_INDEX.md`](AGENT_INDEX.md) for routing;
- [`AGENT_CONFIG.yaml`](AGENT_CONFIG.yaml) for retrieval and quality policy;
- [`WORKSPACE.yaml`](WORKSPACE.yaml) for scope and topology;
- [`artifacts/competency-questions.yaml`](artifacts/competency-questions.yaml) for the 30-question
  initial coverage map; and
- [`artifacts/synthetic-worlds.yaml`](artifacts/synthetic-worlds.yaml) for deterministic fixtures.
- [`artifacts/source-catalog.yaml`](artifacts/source-catalog.yaml) for the anchor source registry;
- [`artifacts/evidence-notes.yaml`](artifacts/evidence-notes.yaml) for bounded, source-grounded
  evidence; and
- [`artifacts/candidate-definitions.yaml`](artifacts/candidate-definitions.yaml) for proposals
  that have not been promoted into canonical ontology state.
