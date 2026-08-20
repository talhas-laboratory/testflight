# Brand ontology research protocol

## Purpose

Turn interdisciplinary Brand research into source-grounded ontology proposals without allowing a
source, model output, or convenient storage shape to become canonical meaning automatically.

## Source authority tiers

| Tier | Permitted use |
| --- | --- |
| A | standards, foundational academic work, peer-reviewed synthesis, authoritative primary research |
| B | major scholarly books and established frameworks |
| C | high-quality professional frameworks and case material |
| D | exploratory practitioner material; candidate language only |
| E | examples and inspiration; never ontology authority |

English is the initial research language. Source and alias records must still carry language metadata
so the ontology can become multilingual without a migration of identity semantics.

## Proposal lifecycle

```text
research_note
  → candidate_definition
  → independent_evaluation
  → fixture_and_question_review
  → accept | hold | reject | deprecate
```

`accept` requires an authorized ontology steward. A model, source tier, or confidence value cannot
promote a definition by itself. `hold`, `branch`, `partial`, and `no_hit` are valid outcomes.

## Candidate contract

Every candidate records:

- immutable candidate ID and semantic kind;
- necessary definition and scope;
- inclusion and exclusion rules;
- examples and counterexamples;
- allowed subject/object types for relationships;
- source references and exact excerpts or fixture IDs;
- competency-question coverage;
- proposed ontology version and module;
- uncertainty, alternatives, and conflicts;
- evaluator and reasoning-operator receipts; and
- promotion authority or explicit non-promotion status.

## Research boundaries

Keep these separate:

- domain entities versus meta-model primitives;
- evidence and Observation versus accepted Assertion;
- intended, expressed, experienced, reported, observed, inferred, and hypothesized perspectives;
- semantic truth versus Context applicability;
- temporal sequence versus causality;
- candidate definitions versus accepted ontology definitions; and
- ontology certification versus Cognee projection/retrieval certification.

## Retrieval policy

Route to the smallest child view. Use lexical/BM25 retrieval first, bounded same-container hybrid
only on an in-domain lexical no-hit, and bounded graph traversal only for explicit path questions.
Navigation/configuration documents are not final semantic evidence. Out-of-domain queries return
`NO_HITS`.
