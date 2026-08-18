# Reasoning-operator workspace index

## Workspace identity

- `workspace_id`: `world://workspace/reasoning-operators`
- `source_of_truth`: `reasoning/operators/index.yaml`
- `Cognee dataset`: `testflight_reasoning_operators`

## Routing

| Intent | Smallest child | Primary sources |
| --- | --- | --- |
| Which guardrail applies? | `selection` | operator index and category files |
| How do I execute one? | `execution` | selected operator procedure |
| Did it pass? | `evaluation` | selected operator evaluators and probes |
| How do I rebuild or refresh it? | `maintenance` | workspace manifest and population command |

For extraction, start with mention/entity, occurrence/canonical,
evidence/truth, confidence/truth, and sequence/causality. For architecture,
start with boundary, ontology, local/global, configuration/runtime, and
evaluation/schema. For persistence, start with identity/provenance,
validation/persistence, retry/idempotency, and workspace isolation. For
retrieval, start with retrieval/reasoning, local/global, and evidence/truth.

## Source rules

- The canonical YAML file is authoritative; task views explain how to use it.
- A source claim must retain operator id/version, file, category, and evidence.
- `AGENT_INDEX.md` and `AGENT_CONFIG.yaml` are navigation/policy sources only.
- No operator is a user trait, diagnosis, or private chain-of-thought artifact.
