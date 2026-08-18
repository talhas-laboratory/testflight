# Reasoning-operator guardrails

## Context

The Mindspace context library defines an operator as a portable semantic
contract: it accepts typed inputs, declares required context and preconditions,
performs an observable transformation, returns an inspectable reasoning
object, preserves invariants, and is evaluated independently of its provider.
The library also makes three boundaries non-negotiable:

1. evidence, meaning, and operational state must not silently collapse;
2. relationships, scope, time, branches, and uncertainty must survive context
   compilation; and
3. deterministic code may prepare, validate, route, store, index, and verify
   lineage, but it must not manufacture semantic meaning.

The earlier entity/extraction discussion exposed a family of recurring errors.
This design turns each error category into a small control operator. These are
guardrails, not a claim about a person's fixed cognition. They can be used by
an agent, an LLM provider, deterministic validation code, or a human review
station.

## Category-to-operator map

| Mistake category | Operator | Primary protection |
| --- | --- | --- |
| Boundary conflation | `boundary-conflation` | Keeps evidential/semantic/operational/authority planes separate |
| Ontology conflation | `ontology-conflation` | Separates semantic types from storage/provider types |
| Mention/entity conflation | `mention-entity-conflation` | Keeps text mentions distinct from referents/entities |
| Occurrence/canonical conflation | `occurrence-canonical-conflation` | Requires recurrence before canonical promotion |
| Evidence/truth conflation | `evidence-truth-conflation` | Produces scoped, status-bearing claim proposals |
| Confidence/truth conflation | `confidence-truth-conflation` | Treats confidence as uncertainty, not truth |
| Sequence/causality conflation | `sequence-causality-conflation` | Requires mechanism or direct support for causality |
| Version/state conflation | `version-state-conflation` | Separates current projection from history and branches |
| Retrieval/reasoning conflation | `retrieval-reasoning-conflation` | Returns bounded evidence before interpretation |
| Local/global conflation | `local-global-conflation` | Requires explicit scope and independent cases |
| Identity/provenance conflation | `identity-provenance-conflation` | Separates semantic, source, actor, and derivation IDs |
| Validation/persistence conflation | `validation-persistence-conflation` | Schema pass never silently commits state |
| Workspace isolation failure | `workspace-isolation` | Enforces locus, permission, and cache boundaries |
| Retry/idempotency failure | `retry-idempotency` | Separates attempts from semantic results and side effects |
| Configuration/runtime conflation | `configuration-runtime` | Verifies effective config before execution |
| Evaluation/schema conflation | `evaluation-schema` | Separates schema, invariant, semantic, and outcome quality |

The canonical Mindspace operator references in each file identify the broader
reasoning family that the guardrail specializes: whole-before-parts, abstraction
lift, decompose-then-integrate, missing-layer detection, contextual
transformation, semantic precision, theory-to-agent utility, modularity, and
the intelligence/determinism boundary.

## Step-by-step use

1. **Classify the failure.** Name the category before fixing the output. A
   single incident may activate more than one operator.
2. **Compile a bounded packet.** Include locus, goal, station, perspective,
   state, time, authority, evidence references, assumptions, conflicts,
   uncertainty, invariants, permissions, and the requested return schema.
3. **Run the smallest operator first.** Do not load the whole catalog. Use the
   route in `reasoning/operators/index.yaml` as a starting point and add only
   operators whose preconditions are met.
4. **Execute observable steps.** Each procedure is deliberately finite. The
   output is a proposal or evaluation object, not private chain-of-thought.
5. **Honor holds.** If `hold_when` is true, return `hold`, `branch`, `ask`, or
   `no_hit` according to the packet's uncertainty policy. Do not fill the gap
   with plausible text.
6. **Evaluate independently.** Run the operator's evaluators and keep each
   dimension separate. A parseable object can still fail provenance,
   semantics, scope, or utility.
7. **Record lineage.** Persist operator id/version, configuration, input
   references, output, evaluator results, and any omitted context in the
   derivation record.
8. **Only then hand off or persist.** Downstream operators consume the
   declared return fields. World mutation remains proposal-only unless an
   explicit authority gate authorizes a commit.

## Promotion path

All 16 operators are version `1`, status `candidate`, and backed by the
Mindspace documentation rather than a claim about universal reasoning. A
future promotion should require:

- a positive case, counterexample, insufficient-context case, and regression
  case for the operator;
- continuity checks showing evidence, identity, uncertainty, and lineage
  survive each handoff;
- an independent semantic rubric in addition to deterministic contract tests;
- user review for any operator that would affect sensitive inference or
  external action; and
- a versioned migration/rebuild path if the contract changes.

## Scope decision

This repository receives the portable catalog and validation layer. It does
not add an Inner Space/Bridge runtime behavior or invent a new provider route.
Those systems can consume these contracts through an adapter later. Keeping
the catalog provider-neutral preserves the Mindspace narrow waist and avoids
coupling Testflight's upstream adapters to a private reasoning implementation.
