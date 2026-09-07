# Content Semantic Planes and Handoff Contract

## Purpose

This glossary defines the semantic planes used by multimodal Content processing and the legal
handoffs between them. It is a classification contract for architecture, models, adapters,
operators, persistence, retrieval, and review.

If a candidate record spans several planes, split it into linked records unless the combined form
has an explicit reversible projection and preserves each field's authority.

## Planes

### Evidence

What the system received or retained from a source: bytes, export records, captions, metadata,
snapshots, annotations, and acquisition receipts.

Evidence may support, oppose, qualify, mention, or remain inconclusive about a claim. Its presence
does not decide truth. Evidence requires source identity, integrity/hash, access and rights scope,
recorded time, and provenance.

### Observation

A bounded report of what an observer detected in evidence: an object, phrase, cut, color relation,
audio event, text span, gesture, layout, or measured property.

An Observation requires exact temporal, spatial, textual, or record anchors; observer/operator
identity; uncertainty; modality; and derivation. Observation cannot assert private intent, brand
essence, causal effect, or global recurrence.

### Normalized Content

A provider-independent structural representation of one or more content items. It composes content
units, synchronized tracks, segments, observations, and cross-modal relations by stable reference.

Normalized Content describes how source-bearing elements are arranged and related. It may retain
pattern candidates, but does not make them accepted World rules. It must be rebuildable from source
records and derivations.

### Interpretation

A question- and lens-dependent proposal about what normalized Content means, does, expresses, or
suggests. Interpretation uses an explicit frame and transformation recipe.

Interpretation requires supporting and opposing evidence, alternatives, scope, valid time,
epistemic status, invalidation conditions, authority, derivation, and evaluator results. Several
interpretations may coexist.

### Module Knowledge

A typed interpretation or pattern expressed in a domain-local ontology, such as social-content
strategy, narrative analysis, production technique, or creative-field contribution.

Module Knowledge can be internally coherent and useful without having a valid shared-World mapping.
Module ownership, ontology/version, corpus scope, and transfer conditions remain explicit.

### World Projection Proposal

A reviewable translation from module-local knowledge into shared semantic records. A proposal
records exact and conditional mappings, losses, local-only residues, identity hypotheses, conflicts,
extension requests, evidence links, semantic diff, and required review.

Compilation produces a proposal; it does not accept or activate it.

### Accepted World

Versioned semantic state promoted by an authorized review or explicit governance policy. Examples
include accepted Creative Field versions, supported StateSnapshots, reviewed RelationshipFrames,
and accepted Brand assertions.

Accepted does not mean timeless or universal. Context, branch, valid time, source lineage,
conflicts, and supersession remain available.

### Retrieval Selection

A bounded, permission-filtered selection of records for a task. Retrieval records ranking strategy,
scope, branch, time, perspective, anchors, omissions, budget, and no-hit state.

Retrieval does not interpret results or decide truth. A top-ranked record is not automatically an
answer or steering instruction.

### Reasoning Steering

Operational context compiled for a specific reasoning operator. It may contain accepted knowledge,
explicitly selected hypotheses, evidence anchors, interpretation frames, constraints, alternatives,
anti-generalizations, permissions, omissions, and return requirements.

Steering changes what an operator considers; it does not silently change the World or grant action
authority.

### Action and Outcome

An Action is an external or persistent operation authorized under an explicit grant. An Outcome is
an observed result recorded after action or independent occurrence.

Planned actions, predictions, simulations, generated outputs, and expected outcomes remain distinct
from observed outcomes. Evaluation may propose learning; it cannot validate itself into accepted
knowledge.

## Allowed handoffs

| From | To | Required handoff | Authority/result |
|---|---|---|---|
| Evidence | Observation | Multimodal observation operator | Bounded observation proposal |
| Observation | Normalized Content | Content Compiler | Rebuildable structural record |
| Normalized Content | Interpretation | InterpretationFrame + TransformationRecipe | Interpretation proposal/branch/hold |
| Interpretation | Module Knowledge | Module validator and ontology | Module-local proposal |
| Module Knowledge | World Projection Proposal | Versioned mapping registry | Exact/lossy/local/extension/hold result |
| World Projection Proposal | Accepted World | Semantic evaluation + review authority | New accepted version or rejection |
| Accepted World/Module Knowledge | Retrieval Selection | Scoped retrieval policy | Ranked evidence packet/no-hit |
| Retrieval Selection | Reasoning Steering | Context/Steering Compiler | Bounded steering packet |
| Reasoning Steering | Action | Task operator + explicit authority grant | Authorized invocation or hold |
| Action/Output | Evidence | Receipt + retained output bytes/observations | New source envelope/content unit |
| Outcome/Evaluation | World Projection Proposal | Learning/evaluation policy | Reviewable update or hypothesis |

## Forbidden collapses

- Evidence -> truth.
- Observation -> intent.
- One occurrence -> canonical pattern.
- Duplicate observations -> independent recurrence.
- Interpretation -> accepted fact.
- Module type -> World type by name similarity.
- Provider schema or database table -> ontology.
- Model confidence -> calibrated probability or truth.
- Retrieval rank -> answer.
- Steering packet -> authority grant.
- Generated output -> observed outcome.
- Evaluation -> automatic self-modification.
- Valid JSON -> persistence approval.

## Classification checklist

Before adding a field or record, determine:

1. its semantic plane;
2. source, semantic, actor, workspace, version, and derivation identities;
3. valid time and recorded time;
4. context, branch, project, corpus, and permission scope;
5. supporting, opposing, and missing evidence;
6. epistemic status;
7. operator and transformation recipe;
8. alternatives and invalidation conditions;
9. ontology owner and mapping status;
10. review, persistence, disclosure, and action authority;
11. independent evaluator results;
12. rebuild and recovery path.

If a missing answer could change meaning, authority, persistence, or action, return `branch`, `ask`,
or `hold` rather than inventing a default.

