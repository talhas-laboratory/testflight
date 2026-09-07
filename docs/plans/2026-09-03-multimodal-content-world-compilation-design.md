# Multimodal Content Substrate and World Compilation — Architecture and Build Guide

**Date:** 2026-09-03  
**Status:** Proposed architecture  
**Implementation baseline:** Post-build extension to the completed Moodboard/Creative Field,
operator-runtime, World-view, and context-intelligence vertical slice. The layers specified here
were discussed after that implementation run and are not yet represented as completed code unless
an existing component is explicitly named for reuse.  
**Initial use case:** Analyze authorized public-facing social profiles and reels to understand their
expressed brand identity, content patterns, and creative behavior.  
**General scope:** Create a reusable, provider-independent Content layer that can normalize
multimodal material, support plural interpretations, compile reviewed proposals into the World,
and provide bounded steering context to reasoning operators.

## 1. Outcome

Build an end-to-end system that can:

1. acquire an authorized profile, post, reel, upload, export, or other content source;
2. preserve the original bytes and source metadata as immutable evidence;
3. decompose video, image, audio, speech, text, captions, and metadata into synchronized tracks;
4. extract source-anchored observations without treating interpretation as perception;
5. identify recurring multimodal and semantic patterns across independent content items;
6. interpret what the content may mean under an explicit question, lens, context, and ontology;
7. retain alternatives, counterexamples, uncertainty, and missing modalities;
8. translate module-local interpretations into reviewable World proposals through explicit mappings;
9. compile only task-relevant, permission-filtered knowledge into reasoning steering packets;
10. analyze generated outputs through the same Content pipeline without creating a self-reinforcing
    feedback loop.

The intended architecture is:

```text
authorized source
  -> immutable evidence
  -> multimodal Content Compiler
  -> normalized Content substrate
  -> interpretation/module compiler
  -> World Projection Compiler
  -> reviewed World and Creative Field records
  -> Context/Steering Compiler
  -> reasoning operator
  -> output
  -> output normalization and evaluation
  -> reviewable learning proposal
```

The system must gain information through declared transformations while preserving the difference
between what was present, what was inferred, what was generalized, what was accepted, and what is
merely being used to steer a task.

## 2. Core architectural decision

The Content layer is neither raw evidence nor the main World. It is a normalized, versioned,
evidence-linked substrate between them.

Raw evidence is source material: media bytes, captions, page snapshots, exports, and acquisition
metadata. The Content substrate describes the internal structure of that material in a form that
different domain modules can consume. The World contains reviewed, scoped semantic records about
brands, products, audiences, campaigns, states, relationships, hypotheses, and decisions.

Do not collapse these layers:

```text
Evidence              what the system received
Observation           what a bounded observer detected
Normalized Content    how observations align into content structure
Interpretation        what that structure may mean under a lens
Module knowledge      what a domain proposes in its local ontology
World proposal        how that proposal may map into shared semantics
Accepted World        what authorized review has promoted
Steering context      what a particular reasoning task is allowed to use
```

A record may be structurally valid at any layer without being semantically correct or authorized
for promotion. Provider success, valid JSON, high model confidence, and retrieval rank are never
promotion criteria by themselves.

## 3. Why three compilers are required

### 3.1 Multimodal Content Compiler

The Content Compiler converts heterogeneous source material into a synchronized, provider-neutral
content representation. It answers: **what is present, where is it, when does it occur, and how do
the modalities relate?**

It must preserve exact source anchors and emit observations or pattern candidates, not brand truth.
It may use deterministic processors, multimodal models, speech recognition, audio analysis, OCR,
or human annotations behind replaceable ports.

### 3.2 Interpretation and Module Compiler

The Interpretation Compiler answers: **what might this content be about or be doing under a stated
question and lens?** It applies a module-specific ontology and transformation recipe to normalized
Content. Social analysis, brand analysis, narrative analysis, creative analysis, and production
analysis are different readings of the same substrate.

Its outputs are proposals with alternatives and anti-inferences. A social interpretation is not
automatically a Brand-world fact.

### 3.3 World Projection and Context Compilers

The World Projection Compiler maps module-local proposals into shared semantic types. It decides
whether a concept maps exactly, maps conditionally, remains local, requires an ontology-extension
proposal, conflicts with existing knowledge, or must be held.

The Context Compiler performs the inverse operational movement. Given a task, it selects a bounded
World view, relevant Content evidence, active interpretation lens, permissions, conflicts, and
omissions, then emits a steering packet. It does not dump the archive into a prompt.

The projection compiler protects World integrity. The context compiler protects reasoning quality.

## 4. Package and adapter topology

Recommended repository topology:

```text
packages/
  testflight-content/                # shared normalized Content contracts
  testflight-social-analysis/        # module-local social ontology and workflows
  testflight-creative-field/         # existing creative interpretation and synthesis
  testflight-brand/                  # existing Brand semantics
  testflight-semantic/               # shared World records and projection contracts
  testflight-context-intelligence/   # bounded World/context compilation
  testflight-operator-runtime/       # provider-independent operator execution

adapters/
  instagram-content/                 # Instagram acquisition and source normalization
  local-content-processors/          # ffmpeg/OCR/transcript/keyframe implementations
  <multimodal-model>/                # provider-specific observation implementation
  sqlite-semantic/                   # canonical append-oriented persistence
  cognee/                            # rebuildable retrieval projection only

apps/
  creative-studio/                   # capture, inspection, interpretation, review
  brand-lab/                         # read-only World exploration
```

`testflight-content` must not import Instagram SDKs, model SDKs, Cognee, UI frameworks, or Brand
classes. `testflight-social-analysis` may depend on Content and shared semantic contracts, but its
ontology must remain local until projection. Instagram-specific imports and HTTP behavior belong
only in `adapters/instagram-content`.

Before adding any external runtime dependency, update `upstreams/registry.yaml`. A new adapter
requires a descriptor, dependency-free health probe, documentation, and tests.

## 5. Canonical Content contracts

Start with small immutable records composed by stable IDs. Avoid one giant nested analysis object.

### 5.1 `SourceEnvelope`

Identifies the acquired source and its permitted use.

Required fields:

- `source_envelope_id`
- `project_id` and `workspace_id`
- `source_system` and provider-local source ID
- source URI or export-relative locator
- content hashes and byte references
- acquisition method and acquisition receipt ID
- recorded time and source-published time where available
- privacy classification
- rights/license record ID
- retention policy
- derivation ID

Visibility is not permission. Missing analysis rights must produce `hold` before model disclosure.

### 5.2 `ContentUnit`

Represents one semantically addressable content item: reel, post, story snapshot, image, caption,
profile snapshot, document, generated output, or composite bundle.

Required fields:

- `content_unit_id`
- `source_envelope_id`
- `content_kind`
- parent and child content-unit IDs
- profile/account subject reference when known
- valid and recorded time
- lifecycle and epistemic status
- derivation ID

Provider IDs are source identities, not semantic identities. A repost, edit, export, and duplicate
must remain distinct occurrences even when hashes overlap.

### 5.3 `MediaTrack`

Represents synchronized modalities within a ContentUnit.

Examples:

- video frames;
- source audio;
- speech transcript;
- music analysis;
- on-screen text/OCR;
- written caption;
- hashtags and metadata;
- derived keyframes;
- human annotations.

Each track records its time base, modality, language where applicable, source or derivative blob,
processor identity, limitations, and alignment status.

### 5.4 `ContentSegment`

Defines an addressable temporal, spatial, textual, or structural interval. A segment may be a shot,
scene, utterance, caption span, hook, transition, or manually marked section.

It must record:

- segment ID and parent ContentUnit;
- start/end time, spatial region, or text span;
- segmentation method and version;
- overlapping segment IDs;
- boundary uncertainty;
- source anchors.

Segmentation is a proposal. Different segmentation policies may coexist as separate derivations.

### 5.5 `PerceptualObservation`

Records a bounded observation such as a detected object, spoken phrase, palette distribution,
camera movement, cut, vocal property, musical event, layout relation, or interaction signal.

Required properties:

- modality and observation type;
- value and optional calibrated measurement;
- exact source/segment anchors;
- observer and operator version;
- uncertainty and known limitations;
- status `observed`, `reported`, `partial`, or `unavailable`;
- derivation ID.

Do not place inferred intention, audience psychology, or brand character in this record.

### 5.6 `CrossModalRelation`

Represents relations across tracks without flattening them into prose.

Examples:

- narration names the object shown;
- the caption qualifies the spoken claim;
- a product reveal aligns with a musical accent;
- on-screen text contradicts narration;
- editing rhythm follows the beat;
- a visual motif recurs while the semantic topic changes.

The relation records role, participating observation/segment IDs, alignment tolerance, evidence,
and uncertainty.

### 5.7 `ContentOccurrence` and `PatternCandidate`

An occurrence is local to a ContentUnit or segment. A pattern candidate proposes recurrence across
multiple occurrences.

`PatternCandidate` must include:

- target corpus and time range;
- occurrence IDs;
- count of independent ContentUnits and source episodes;
- variation and counterexamples;
- candidate invariants;
- proposed scope: local, series, profile, campaign, or cross-profile;
- transfer conditions;
- uncertainty and derivation;
- status `local_only`, `scoped_pattern`, `global_candidate`, or `held`.

Repeated observations derived from the same reel, duplicate, or export do not constitute
independent evidence.

## 6. Interpretation contracts

### 6.1 `InterpretationFrame`

An InterpretationFrame is the explicit instruction for gaining additional information from
normalized Content. It prevents hidden interpretation assumptions from living only in a prompt.

It should contain:

- `frame_id` and version;
- question and intended use;
- module ontology/version;
- target subject and corpus scope;
- context, branch, time, locale, channel, and perspective;
- requested dimensions;
- permitted inputs and epistemic statuses;
- inference depth: descriptive, relational, strategic, or causal;
- required counterexample search;
- uncertainty policy: branch, ask, or hold;
- prohibited conclusions and sensitive-inference rules;
- output schema and evaluator rubric;
- authority and disclosure policy.

The same content can be read through multiple frames without overwriting previous readings.

### 6.2 `TransformationRecipe`

A TransformationRecipe makes the informational transformation inspectable and reproducible.

It declares:

- operator ID/version;
- accepted record types;
- required context;
- transformation steps;
- output record types;
- invariants;
- forbidden shortcuts;
- hold conditions;
- deterministic and semantic evaluators;
- cache and idempotency identity;
- disclosure and provider capability requirements.

This is the portable contract. Prompts and provider syntax are implementations of it.

### 6.3 `ContentInterpretation`

Stores a lens-specific hypothesis about role, meaning, topic, structure, or strategy.

It must retain:

- proposition and interpretation category;
- supporting observation, occurrence, and pattern IDs;
- opposing and qualifying evidence;
- alternatives;
- what the evidence cannot establish;
- target scope and valid time;
- authority and epistemic status;
- invalidation conditions;
- derivation and evaluator results.

Model confidence may prioritize review. It may not stand in for evidence or truth.

### 6.4 Module-local social analysis

The initial social module may define local dimensions such as:

- topic and subtopic;
- hook and retention structure;
- narrative progression;
- visual grammar and shot behavior;
- editing rhythm and reveal structure;
- audio and voice function;
- rhetorical posture;
- emotional progression;
- audience address and participation role;
- product/service role;
- call-to-action behavior;
- recurring motif and format family;
- expressed brand-identity candidate;
- content-strategy hypothesis.

These concepts must not be inserted into the global ontology merely because the first use case
needs them. They live in `testflight-social-analysis` until mapped.

## 7. World Projection Compiler

### 7.1 Mapping registry

Create a versioned mapping registry whose entries state:

- source module concept ID and version;
- target World concept or record type;
- mapping kind: exact, conditional, lossy, composite, local-only, or unsupported;
- required source fields and context;
- epistemic-status conversion rules;
- authority and review requirements;
- transfer conditions;
- evaluator;
- inverse/rebuild behavior;
- known omissions.

An adapter mapping must not add semantic meaning. If a mapping would distort the source concept,
return `local_only`, `extension_proposed`, or `hold`.

### 7.2 `WorldProjectionProposal`

The compiler emits a proposal rather than mutating the World. Its result contains:

- mapped records;
- source interpretation IDs and evidence links;
- unchanged module-local records;
- conditional and lossy mapping diagnostics;
- identity hypotheses;
- conflicts with existing World records;
- ontology-extension proposals;
- review requirements;
- semantic diff against the selected branch;
- derivation and evaluator results.

Likely target records already present in Testflight include:

- `CreativeFieldProposal` for creative and expressive principles;
- `StateSnapshot` for scoped modeled conditions;
- `RelationshipFrame` for brand–audience–channel–content relations;
- `HypothesisRecord` for strategic explanations or expected effects;
- `EvidenceLink` for support, opposition, qualification, and inconclusive evidence;
- `PerspectiveProfile` for situated readings;
- Brand assertions only after the Brand module and authority policy accept them.

### 7.3 Promotion policy

Promotion is separate from compilation:

1. validate structure;
2. validate provenance, identity, scope, rights, and operator invariants;
3. run an independent semantic evaluator;
4. compare against existing branch records;
5. retain conflicts and alternatives;
6. request the required review authority;
7. append a proposal or accepted version according to policy;
8. never rewrite source evidence or previous versions.

## 8. Reasoning steering

### 8.1 Why steering requires a compiler

Normalized Content and the World may become large. Injecting the full corpus into a reasoning
request would increase noise, disclosure, contradiction collapse, and prompt injection risk.

The steering path should be:

```text
ReasoningRequest
  -> resolve workspace, project, branch, context, task, lens, and permissions
  -> retrieve child-first from the smallest relevant Content/module container
  -> resolve exact World records and conflicts
  -> select accepted knowledge plus explicitly requested hypothesis branches
  -> compile bounded steering packet
  -> execute reasoning operator
```

Retrieval selects evidence. It does not decide the answer.

### 8.2 `ReasoningSteeringPacket`

The packet should contain:

- task, goal, target and expected return schema;
- active World view and branch;
- active InterpretationFrame;
- selected accepted principles and scoped pattern candidates;
- evidence and Content anchors;
- constraints, exclusions, and anti-generalizations;
- alternatives and unresolved conflicts;
- context dimensions and valid time;
- permissions and disclosure limitations;
- omissions and no-hit sections;
- operator IDs/versions and evaluator requirements;
- route and derivation receipt.

The packet is operational context, not additional authority. An inferred pattern may steer an
exploratory branch, but cannot override an accepted policy or Brand decision.

### 8.3 Connection to existing context intelligence

Extend `testflight-context-intelligence` by composition:

```text
WorldViewResolver
  -> ResolvedWorldView

ContentContextResolver
  -> ResolvedContentContext

InterpretationResolver
  -> ResolvedInterpretationFrame

SteeringCompiler
  -> ReasoningSteeringPacket
```

Do not move observation or interpretation ownership into context intelligence. It should select
and compile already typed records, preserving the current bounded-packet behavior.

## 9. Output analysis and learning loop

Generated artifacts, recommendations, and agent outputs should re-enter the Content Compiler as
new `ContentUnit` records with origin `generated_output`. They can then be segmented, observed,
interpreted, categorized, and compared with the active World view or Creative Field.

Output evaluation must distinguish:

- schema validity;
- operator-invariant compliance;
- evidence fidelity;
- semantic alignment;
- task usefulness;
- brand/field alignment;
- novelty versus prohibited drift;
- outcome evidence when later available.

Evaluation produces proposals such as:

- output-only correction;
- revised steering packet;
- interpretation correction;
- mapping correction;
- new Creative Field proposal;
- Brand-world hypothesis;
- experiment or measurement proposal.

Never feed an evaluation directly into accepted steering configuration. Otherwise generated output
can validate its own assumptions and amplify them. Promotion requires review or an explicit
experiment/learning policy.

## 10. Operator routing

Use the smallest relevant contracts rather than sending the entire operator catalog to a model.

Recommended route:

```text
acquisition and observation
  -> creative/observation-extraction@1
  -> guardrail/mention-entity-conflation@1
  -> guardrail/occurrence-canonical-conflation@1

interpretation and patterning
  -> guardrail/evidence-truth-conflation@1
  -> guardrail/confidence-truth-conflation@1
  -> guardrail/local-global-conflation@1
  -> creative/reference-interpretation@1 or a Content-specific equivalent

module-to-World projection
  -> guardrail/boundary-conflation@1
  -> guardrail/ontology-conflation@1
  -> guardrail/identity-provenance-conflation@1
  -> guardrail/validation-persistence-conflation@1

reasoning steering
  -> guardrail/retrieval-reasoning-conflation@1
  -> context compilation
  -> task-specific operator

evaluation
  -> guardrail/evaluation-schema@1
  -> creative/output-evaluation@1 where applicable
```

Each persisted derivation must record operator ID/version, input references, configuration,
outputs, evaluator results, and hold/branch decisions.

## 11. Implementation sequence

### Phase 0 — freeze contracts and fixtures

1. Add a decision record for the Content substrate boundary.
2. Define a glossary for evidence, observation, Content, interpretation, module knowledge, World
   proposal, accepted World, and steering context.
3. Create synthetic fixtures for one profile with three short reels, captions, transcripts,
   keyframes, audio events, repeated motifs, one counterexample, and one unavailable modality.
4. Define expected holds and no-hits before building model integrations.

Exit gate: reviewers can classify every fixture field into exactly one semantic plane or identify
an explicit cross-plane relation.

### Phase 1 — `testflight-content` contracts

Implement immutable models and validation for:

- SourceEnvelope;
- ContentUnit;
- MediaTrack;
- ContentSegment;
- PerceptualObservation;
- CrossModalRelation;
- ContentOccurrence;
- PatternCandidate;
- InterpretationFrame;
- TransformationRecipe;
- ContentInterpretation;
- derivation/evaluator receipts.

Add ports for source bytes, processor execution, record persistence, and content resolution. Use
the existing content-addressed blob store rather than embedding media bytes in records.

Exit gate: synthetic Content bundles round-trip through persistence and every observation resolves
to an immutable source anchor.

### Phase 2 — deterministic local multimodal pipeline

Build deterministic or fixture-backed processors first:

1. probe media and establish a canonical time base;
2. extract audio and keyframes;
3. ingest supplied transcript/OCR fixtures;
4. segment shots and text spans;
5. align tracks;
6. emit observations and cross-modal relations;
7. emit explicit omissions for unsupported modalities.

Do not begin with an autonomous model pipeline. Deterministic fixtures make boundaries and replay
behavior testable before provider variance is introduced.

Exit gate: replay produces stable IDs and semantically equivalent records without duplicate
occurrences.

### Phase 3 — social analysis module

Implement the module-local ontology, InterpretationFrames, TransformationRecipes, validators, and
operator schemas. Start with descriptive and relational inference. Defer causal claims about why a
post performed well until experiments or external outcome evidence exist.

Build profile-level aggregation only after reel-level observations work. Pattern aggregation must
count independent ContentUnits, preserve counterexamples, and label scope.

Exit gate: the system distinguishes one-reel observations, recurring profile patterns, strategic
hypotheses, and unsupported global claims.

### Phase 4 — Instagram adapter

Implement authorized acquisition behind the shared adapter port. Support the safest available
route first, such as owner-provided export/upload or approved API access. Store provider-local IDs
and transport receipts only in the adapter/source envelope.

The adapter must:

- validate requested scope and rights before acquisition;
- rate-limit and identify itself appropriately;
- avoid private endpoints, challenge bypass, fake accounts, and block evasion;
- retain deletions/private transitions as source-state changes;
- normalize into shared Content contracts;
- provide a dependency-free health probe;
- return partial/hold rather than fabricate missing media.

Exit gate: replacing the Instagram adapter with fixture input produces the same shared Content
schema and downstream behavior.

### Phase 5 — World Projection Compiler

Add mapping registry contracts and proposal-only projection. Implement a narrow initial map:

- expressed creative patterns -> Creative Field contributions/proposal;
- scoped profile condition -> StateSnapshot proposal;
- brand/audience/channel relation -> RelationshipFrame proposal;
- strategic explanation -> HypothesisRecord proposal;
- all support/opposition -> EvidenceLink records.

Exit gate: unsupported concepts remain local, lossy mappings report omissions, and no model output
can directly mutate accepted World state.

### Phase 6 — context and steering integration

Add Content and interpretation resolvers beside the existing WorldViewResolver. Compile a bounded
ReasoningSteeringPacket and integrate it with the operator runtime. Preserve no-hit, partial, hold,
branch, and ask outcomes.

Exit gate: a task receives only the permitted profile patterns and World records relevant to its
scope; every material steering statement resolves to evidence or an accepted policy record.

### Phase 7 — output evaluation loop

Normalize one generated text or visual output, interpret it under an evaluation frame, compare it
with the active Creative Field and World view, and create a feedback proposal. Do not automatically
promote that proposal.

Exit gate: the feedback path cannot alter accepted knowledge without an authority-bearing review
decision.

## 12. Testing and certification

### 12.1 Contract tests

- reject missing source anchors;
- reject cross-project references;
- require rights records before disclosure;
- reject invalid temporal and spatial ranges;
- preserve source, semantic, actor, and derivation identities separately;
- require operator/version and evaluator receipts;
- keep semantic and persistence statuses separate.

### 12.2 Multimodal continuity tests

- transcript spans resolve to the source time base;
- keyframes resolve to video intervals;
- audio/video relations remain valid after segmentation revision;
- contradictions between caption, speech, and image remain visible;
- unavailable modalities produce omissions rather than inferred substitutes.

### 12.3 Pattern-quality tests

- duplicate media does not inflate recurrence;
- multiple observations in one reel do not masquerade as independent episodes;
- counterexamples are preserved;
- one-reel findings remain local;
- sensitive or diagnostic generalizations hold;
- profile-level claims identify corpus and time window.

### 12.4 Projection tests

- exact mappings preserve meaning and provenance;
- lossy mappings expose omissions;
- unsupported concepts remain module-local;
- ontology extension is a proposal, never automatic;
- conflicts and alternatives survive projection;
- rebuilding derived projections yields equivalent results.

### 12.5 Steering tests

- retrieval no-hit remains no-hit;
- the packet respects context and token/record budgets;
- accepted and hypothetical branches remain distinct;
- untrusted source text cannot become an operator instruction;
- packet statements cite allowed records only;
- steering does not grant mutation or external-action authority.

### 12.6 End-to-end golden case

Certify one synthetic profile through:

```text
source bundle
  -> normalized Content
  -> reel interpretations
  -> profile pattern proposal
  -> Creative Field and World projection proposals
  -> reviewed version
  -> task-specific steering packet
  -> generated output
  -> output evaluation proposal
```

Run `make check` before committing implementation changes. Extend the existing reasoning-operator,
semantic-continuity, and creative-field fixtures instead of relying only on unit tests.

## 13. Failure and recovery behavior

Use typed outcomes consistently:

- `no_hit`: no source or knowledge matches the bounded request;
- `partial`: useful evidence exists but modalities, scope, or coverage are incomplete;
- `branch`: multiple interpretations materially affect the result;
- `ask`: a user decision can resolve an important ambiguity;
- `hold`: rights, identity, scope, authority, evaluator, or semantic mapping is missing;
- `failed`: an implementation or provider operation failed after valid preflight.

Persist valid upstream records even when a later stage holds. Do not persist malformed provider
outputs. Derived indexes and Cognee projections are disposable; canonical source records,
derivations, proposals, reviews, and accepted versions are append-oriented and recoverable.

Every provider call requires effective-configuration preflight, redacted credential references,
capability checks, disclosure checks, idempotency identity, and an execution receipt.

## 14. How to reason while building

For every proposed record, processor, or mapping, answer these questions in order:

1. **Locus:** Is this source evidence, observation, normalized Content, interpretation, module
   knowledge, World knowledge, retrieval state, or operational steering?
2. **Identity:** Is the ID a source occurrence, semantic referent, actor, workspace, version, or
   derivation identity?
3. **Time and scope:** Where, when, for which corpus, branch, channel, audience, and project does it
   hold?
4. **Evidence:** Which immutable spans, regions, timestamps, or records support or oppose it?
5. **Transformation:** Which operator and recipe produced it, from which typed inputs?
6. **Uncertainty:** Is it observed, reported, inferred, hypothesized, simulated, normative, or
   unresolved?
7. **Alternatives:** What other reading remains plausible, and what would invalidate this one?
8. **Generalization:** Are supporting cases truly independent? What counterexamples exist?
9. **Ontology:** Does the target type express the same meaning, or is the mapping merely convenient?
10. **Authority:** Who may review, accept, bind, disclose, act on, or persist the result?
11. **Evaluation:** Did schema, invariants, semantic quality, and usefulness pass independently?
12. **Recovery:** Can the derived state be rebuilt from preserved evidence and derivations?

If any answer is missing and could materially change downstream behavior, return `branch`, `ask`,
or `hold`. Do not repair the gap with plausible prose.

## 15. First vertical slice

The smallest useful implementation should avoid broad crawling and complex UI work. Build:

1. one synthetic or owner-provided profile bundle;
2. three short reels with video, audio, captions, supplied transcripts, and keyframes;
3. one ContentUnit and synchronized tracks per reel;
4. time-anchored observations for visual, temporal, rhetorical, audio, and social-strategic signals;
5. reel-level interpretations with alternatives;
6. one profile-level PatternCandidate with a retained counterexample;
7. one CreativeFieldProposal and one WorldProjectionProposal;
8. a manual review step;
9. one ReasoningSteeringPacket for a concrete creative task;
10. one normalized and evaluated generated output.

This slice proves the architecture without depending on arbitrary Instagram access, broad ontology
expansion, production-scale indexing, or autonomous knowledge promotion.

## 16. Deferred work

Defer until the vertical slice passes:

- arbitrary public-profile discovery;
- comments and follower-graph analysis;
- demographic or sensitive-trait inference;
- causal performance attribution from engagement numbers;
- real-time monitoring;
- cross-platform identity resolution;
- automatic ontology mutation;
- automatic learning-loop promotion;
- broad Cognee or vector-index optimization;
- autonomous external action based on inferred brand strategy.

## 17. Operator and evaluator record for this design

This design was materially shaped by these contracts:

- `world://operator/creative/observation-extraction@1`: source-anchored multimodal observations;
- `world://operator/guardrail/boundary-conflation@1`: separation of evidence, semantic proposal,
  accepted World, retrieval, and action;
- `world://operator/guardrail/ontology-conflation@1`: module ontology and World mapping separation;
- `world://operator/guardrail/evidence-truth-conflation@1`: explicit epistemic status and competing
  interpretations;
- `world://operator/guardrail/local-global-conflation@1`: independent recurrence and scoped
  generalization;
- `world://operator/guardrail/identity-provenance-conflation@1`: source, semantic, actor, workspace,
  and derivation identity separation;
- `world://operator/guardrail/retrieval-reasoning-conflation@1`: bounded evidence selection before
  interpretation;
- `world://operator/guardrail/validation-persistence-conflation@1`: proposal-only persistence and
  review-gated promotion;
- `world://operator/guardrail/configuration-runtime@1`: inspectable effective runtime and provider
  preflight;
- `world://operator/guardrail/evaluation-schema@1`: separate structural, invariant, semantic, and
  usefulness evaluation.

Design evaluator result:

- boundary coverage: pass at architecture level;
- ontology separation: pass at architecture level;
- provenance path: specified end-to-end, implementation proof pending;
- persistence authority: proposal-only path specified, implementation proof pending;
- multimodal continuity: contract specified, fixture proof pending;
- usefulness: vertical slice defined, user validation and end-to-end proof pending.
