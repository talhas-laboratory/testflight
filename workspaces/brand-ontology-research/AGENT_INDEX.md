# Brand ontology research workspace index

## Workspace identity

- `workspace_id`: `world://workspace/brand-ontology-research`
- `source_of_truth`: `artifacts/research-protocol.md`
- `anchor corpus`: `artifacts/source-catalog.yaml` + `artifacts/evidence-notes.yaml`
- `candidate layer`: `artifacts/candidate-definitions.yaml`
- `executable fixtures`: `scripts/brand_ontology_fixtures.py`
- `constitution`: `docs/plans/2026-08-20-brand-ontology-constitution-v0.1-design.md`
- `Cognee dataset`: `testflight_brand_ontology_research` (pack-only until certification)

## Mission

This container researches the vocabulary needed for Brand Ontology v0.1. It produces proposals and
tests; it does not commit canonical Brand facts or silently change the ontology.

The initial population is a 24-source Tier A anchor corpus. Use `artifacts/research-playbook.md`
for search order, batch sequencing, diversity checks and stopping rules. Source metadata and
bounded evidence notes are canonical within this research workspace; external full text remains
outside the repository unless licensed.

The nine synthetic worlds are executable certification fixtures. They test semantic boundaries;
they do not create accepted Brand-world facts.

## Routing

Route to smallest relevant child container first:

| Intent | Child | Primary sources |
| --- | --- | --- |
| Find research protocol or source tiers | `research` | `artifacts/research-protocol.md`, registry |
| Draft a candidate type or relationship | `proposal` | proposal contract, constitution |
| Test a candidate against questions or fixtures | `evaluation` | competency questions, synthetic worlds |
| Decide accept/hold/reject/deprecate | `promotion` | evaluation receipts, authority contract |
| Check pack or ontology release quality | `certification` | probes, fixture cases, certification policy |
| Refresh or rebuild the workspace | `maintenance` | manifest, registry, source hashes |

Run `bm25` first in the selected child. Escalate to bounded same-container `hybrid` only for an
in-domain lexical no-hit. Use graph retrieval only for explicit bounded path questions. An
out-of-domain query returns `NO_HITS`.

`AGENT_INDEX.md`, `AGENT_CONFIG.yaml`, and the workspace manifest are navigation/policy sources.
They are not final evidence for ontology claims unless the query explicitly asks for routing or
policy.

## Required handoff

Every proposal or evaluation must preserve source URLs, evidence tier, exact excerpts or fixture
IDs, Context, uncertainty, authority, ontology version, operator id/version, and derivation record.
Model output may remain `partial`, `held`, `branch`, or `no_hit`.
