# Brand ontology research playbook

## Objective

This workspace is a research-to-ontology pipeline. It collects diverse, source-grounded material,
creates candidate definitions and counterexamples, and only then proposes changes to canonical
semantic state. The current anchor corpus contains 24 Tier A sources. It is deliberately metadata-
and evidence-note based; full text is not copied into the repository unless access rights permit it.

## Search order

1. Search the canonical standards body, journal, publisher or registry first.
2. Use Crossref, OpenAlex, library catalogues or Google Scholar only for discovery and citation
   chaining.
3. Register the canonical DOI or institutional URL, not the discovery result URL.
4. Prefer the primary paper, standard, dataset or legal guidance over a secondary summary.
5. Add an independent source only when it adds a method, stakeholder, geography, time period,
   contradiction, boundary case or implementation constraint.

## Batch order

| Batch | Focus | Expected output |
| --- | --- | --- |
| 0 | Protocol and schema | source records, query vocabulary, rights decisions |
| 1 | Provenance, ontology, constraints and time | evidence envelopes and validation candidates |
| 2 | Brand knowledge, architecture and portfolio | entity and relationship candidates |
| 3 | Consumer identity, community and culture | perspective and meaning candidates |
| 4 | Experience, service and touchpoints | interaction and journey candidates |
| 5 | Representation, localization and accessibility | facet, binding and profile candidates |
| 6 | Legal, classification and valuation | jurisdiction, evidence and measurement candidates |
| 7 | Causality, change and dependency | event, invalidation and causal guardrails |
| 8 | Challenge pass | cross-cultural, non-Western, B2B, nonprofit, failure and counterexample sources |

## Source admission contract

Every source needs an entry in `source-catalog.yaml`, a bounded note in `evidence-notes.yaml`, and
at least one competency-question mapping. A source is not accepted merely because it is famous or
frequently cited. Record its methodology, stakeholder, geography, language, date and limitations.

Every candidate needs two or more independent source or fixture references, explicit scope and
exclusions, examples, a counterexample, uncertainty, derivation and an independent evaluator
receipt. Candidate status remains `proposed` or `held` until an authorized promotion decision.

## Diversity audit

Before expanding the corpus, check coverage across:

- technical, legal, academic, organizational, consumer, community and design perspectives;
- conceptual, empirical, ethnographic, normative and registry methods;
- global, regional and transnational contexts;
- organization, customer, community, regulator, investor and user stakeholders;
- historical foundations and current standards;
- supporting, dissenting and boundary-case material.

If a batch only repeats one school of thought, stop and add a challenge source instead.

## Stopping rule

Expand from the 24-source anchor corpus only when a competency question lacks three independent
lenses, a synthetic world cannot be executed, or a candidate lacks a counterexample. Stop expansion
after two consecutive batches yield fewer than 10% new concepts, relations or boundary cases.
