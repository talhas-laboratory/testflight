# Ingestion and Elicitation

## Problem solved

Brands rarely begin with a structured, current, evidence-backed World model. Important knowledge is
distributed across founders, brand employees, agencies, decks, documents, analytics, and tacit
practice. A chat/note interface reduces cold-start friction, but only if raw statements retain
speaker, scope, time, and epistemic status.

## Recommended experience

Use a hybrid guided interview rather than an open chatbot or fixed questionnaire.

1. A user creates an intake session with a declared role and purpose.
2. They write notes, answer guided questions, speak, or attach documents.
3. The system preserves raw turns and attachments before interpretation.
4. Operators extract mentions, claims, candidate entities, relations, constraints, and questions.
5. A coverage planner compares proposals with the selected Brand module and asks the smallest
   material follow-up question.
6. The user reviews what the system understood, not just a prose summary.
7. Accepted proposals enter a World delta; held and conflicting proposals remain addressable.

Initial interview areas should be limited to Brand purpose, offering, audience, customer problem,
desired outcome, differentiation, proof, voice, creative boundaries, business constraints, and
known disagreements.

## Proposed records

### `IntakeSession`

- session ID, workspace, purpose, module coverage target;
- participant IDs, roles, authority, and perspective IDs;
- privacy, retention, disclosure, and model-use policy;
- started/completed time and session status.

### `IntakeTurn`

- exact raw text or transcript span;
- speaker, order, recorded time, optional claimed valid time;
- attachment/source references;
- assistant question and operator receipt where applicable.

### `CoverageAssessment`

- covered, missing, conflicting, and unsupported topics;
- question candidates and materiality rationale;
- stop condition so interviews do not continue indefinitely.

### Proposal outputs

- mention-to-referent hypotheses;
- entity, assertion, state, relationship-frame, hypothesis, and decision proposals;
- local vocabulary proposals;
- ontology-extension proposals;
- explicit no-hit, ambiguity, and contradiction records.

## Operator chain

```text
intake coverage planner
  -> mention and referent extraction
  -> claim/evidence classification
  -> candidate semantic typing
  -> identity resolution
  -> Brand module mapping
  -> contradiction and gap detection
  -> minimum follow-up question
  -> review bundle compilation
```

Each operator consumes bounded evidence and emits proposals. The assistant's follow-up wording is
not a source for Brand facts.

## Population versus ontology evolution

Most input should populate customer-specific instances of existing types. When no existing type
can represent a concept without distortion, keep the concept local and create an
`OntologyExtensionProposal` containing source examples, proposed definition, existing types
considered, role behavior, counterexamples, intended scope, and competency questions.

Conversation output never edits `domains/brand/ontology-v2/`. Shared ontology changes require
separate review, fixtures, counterexamples, integrity validation, and versioned release. This
prevents customer vocabulary or one model's preferred categories from becoming universal grammar.

## Multiple participants

Interview participants independently before synthesizing consensus. A founder belief, brand-team
policy, sales observation, customer quotation, and analytics result carry different authority.
Preserve them as distinct perspectives and evidence classes. The review bundle may show agreement,
disagreement, and missing external evidence, but must not manufacture organizational consensus.

## Failure behavior

- Ambiguous referent: preserve candidates and ask only if the distinction is material.
- Unsupported customer claim: record as reported internal belief.
- Conflicting participants: retain both perspectives and create a decision requirement.
- Missing rights: store permitted metadata, hold model disclosure.
- Unknown concept: keep local or propose ontology extension.
- Model/schema failure: retain raw evidence and return partial; never discard the session.

## Build guidance

Reuse `SourceEnvelope`, `ContentUnit`, evidence links, perspectives, assertions, state snapshots,
branches, derivation receipts, operator runtime, and SQLite/blob persistence. Add a small intake
application and ingestion workflow package; do not put chat behavior in `testflight-semantic`.

Start with text, notes, and document attachments. Voice transcription and external collaboration
connectors can follow after the proposal/review loop works reliably.

