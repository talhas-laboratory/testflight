# Brand World grounding and source dossier

Date: 2026-09-14  
Surface: `surface:brand-world-canvas`  
Status: implementation design

## Problem

The canvas currently projects each record as a label, a generic summary, relations, and short
evidence references. That is enough for navigation, but not enough to ground downstream reasoning.
The generic `Meaning` field can collapse an observed statement, an interpretation, and an agent-use
constraint into one sentence. It also hides the distinction between retained source context and a
live source's full body.

## First-principles contract

A record dossier must answer four questions independently:

1. What is asserted or observed?
2. What interpretation, if any, is being proposed?
3. Where, when, and for which task may the record be used?
4. Which evidence and source context make the answer auditable?

The contract therefore exposes:

- `assertion`: the smallest defensible statement;
- `interpretation`: a separate, explicitly inferential reading;
- `permittedUses`: task uses allowed by source authority;
- `scope`: system, semantic type, contexts, valid time, and source locus;
- `constraints`: limitations and prohibited extrapolations;
- `unknowns`: unresolved or freshness-sensitive information;
- `context`: direct typed relations and neighbouring records;
- `sources`: evidence excerpts, paraphrased findings, limitations, source metadata, and live links;
- `contentPolicy`: whether full text is retained and how it may be accessed.

Empty fields remain explicit. The projection does not invent missing interpretations or use rules.

## Approaches considered

### Put full content on every graph node

This makes each node self-contained but duplicates source text, creates drift, increases the graph
payload, and violates the Biotic policy that prohibits full-text storage.

### Put every dossier in `/api/world`

This preserves a single request, but makes the map payload grow with document depth and defeats
progressive disclosure.

### Selected: on-demand dossier projection

`/api/world` remains the deterministic map. `/api/records/{record_id}` compiles one read-only dossier
from canonical records, direct relations, evidence notes, source metadata, and content policy. The
frontend loads it when a record is selected and caches it for the session. This is a projection, not
canonical persistence.

## Interface behavior

The record card has three depths:

- **Grounding** presents assertion, interpretation, use, scope, constraints, and unknowns.
- **Context** presents relation direction, semantic role, neighbouring record, and relation status.
- **Sources** expands the specimen card into a dossier and presents every available bounded excerpt,
  paraphrased finding, limitation, provenance field, and a live-source action for full text.

The UI states when the full source body is not retained. It must never label a bounded excerpt or
paraphrase as “full text.”

## Operator derivation

The implementation applies these versioned controls:

- `world://operator/guardrail/ontology-conflation@1`: semantic type, UI grouping, source schema, and
  projection fields remain separate. Evaluators: `typed_consistency=pass`, `adapter_thinness=pass`.
- `world://operator/guardrail/evidence-truth-conflation@1`: excerpts, reported claims, and inferences
  remain distinguishable. Evaluators: `provenance_completeness=pass`, `status_accuracy=pass`,
  `contradiction_retention=pass` for fields available in the corpus.
- `world://operator/guardrail/retrieval-reasoning-conflation@1`: the dossier selects source context;
  it does not synthesize a new truth claim. Evaluators: `citation_resolution=pass`, `budget=pass`.
- `world://operator/guardrail/local-global-conflation@1`: contexts and valid time remain visible;
  local source statements are not widened to global Brand facts. Evaluator: `scope_accuracy=pass`.

## Error and absence states

- Unknown record IDs return `404` with a JSON error.
- Records without direct evidence return an explicit no-evidence state.
- Source references without catalog metadata remain visible as unresolved external references.
- A prohibited full-text policy yields a bounded-context notice plus a live-source link where one is
  available.
- Missing interpretations, use rules, or scope fields are reported as `Not recorded`, never filled by
  plausible prose.

## Verification

- Projection tests cover the canonical eight systems and all relation endpoints.
- Dossier tests cover assertion/interpretation separation, content-policy disclosure, source
  resolution, relation context, and unknown-record behavior.
- Browser verification covers record selection and all three disclosure depths.
