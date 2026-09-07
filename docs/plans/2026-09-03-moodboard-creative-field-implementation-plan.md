# Moodboard / Creative Field — End-to-End Implementation Plan

**Date:** 2026-09-03  
**Status:** implementation-ready proposal  
**Work board:** [`../workboards/moodboard-creative-field-implementation/README.md`](../workboards/moodboard-creative-field-implementation/README.md)  
**Upstream product design:** `/home/talha/repos/mindscape/docs/product-profiles/moodboard-creative-field/architecture/SYSTEM_DESIGN.md` on `home-server`

## 1. Outcome

Build a project-scoped, multimodal creative workspace in which a person can collect references,
have the system propose what they mean, correct those proposals, approve a versioned Creative
Field, bind that field to Brand-world entities, and use it through artifact workflows and external
generation providers with complete provenance.

The first useful release proves this path:

```text
one Brand project
  -> one image/text moodboard
  -> evidence-grounded per-reference proposals
  -> selective human correction
  -> one approved CreativeFieldVersion
  -> explicit Brand/entity bindings
  -> text and image FieldProjections
  -> one artifact workflow
  -> output evaluation and feedback proposal
```

The implementation extends the current Testflight architecture. It does not create a second
semantic kernel, treat Cognee as canonical storage, or couple the Creative Field to one model
provider.

## 2. Decisions and boundaries

### 2.1 Three distinct product objects

```text
Moodboard       = evidence-bearing curation and expression surface
Creative Field  = reviewed project-scoped semantic configuration
Field Connector = task-specific projection, provider translation, and evaluation boundary
```

The board is part of the semantic world because its assets, arrangement, and annotations are
addressable evidence. It is not identical to the accepted Creative Field derived from that
evidence.

### 2.2 Project scope is the default

A board and field belong to a `CreativeProject`. They do not become a global model of a person's
taste. Cross-project reuse is a separately reviewed binding or reusable-pattern proposal.

### 2.3 Observation, interpretation, acceptance, and execution remain separate

```text
ReferenceAsset
  -> ReferenceObservationProposal
  -> ReferenceInterpretationProposal
  -> CreativeFieldProposal
  -> reviewed CreativeFieldVersion
  -> FieldProjection
  -> GenerationPacket
  -> CreativeOutput
```

No successful model call advances a record across these boundaries automatically.

### 2.4 Stable contracts; replaceable implementations

Canonical IDs, evidence, scope, authority, versions, public handoffs, and derivation receipts are
stable. Providers, prompts, indexes, canvas libraries, orchestration frameworks, and model-specific
feature formats remain replaceable.

### 2.5 First release constraints

- Input modalities: images, text, URLs represented by retained snapshots/metadata, and user notes.
- One board produces one reviewed field version.
- One Brand workspace and project are active per request.
- Text and image projections are supported before audio/video generation.
- A minimal review UI is required; a sophisticated infinite canvas is not.
- Runtime assets and databases stay outside Git; only synthetic fixtures are tracked.

## 3. Current infrastructure and its role

| Existing area | Reuse | Required extension |
|---|---|---|
| `packages/testflight-semantic` | evidence envelopes, entities, assertions, contexts, branches, provenance, governance, dependency and world-view records | add only universally reusable envelopes or statuses; keep creative meaning out |
| `packages/testflight-brand` | Brand ontology modules and Brand-specific entity relationships | add Creative Field binding vocabulary where it expresses Brand meaning |
| `packages/testflight-context-intelligence` | provider-neutral model/retrieval ports, trace store, world-view and visual-language resolution, bounded packet compilation | add field projection consumption and a combined `CreativeContextPacket`; do not put board interpretation here |
| `adapters/sqlite-semantic` | local append-oriented canonical persistence | extend through a creative-field repository adapter and migrations; do not store binary assets as JSON |
| `adapters/cognee` | isolated child retrieval and graph projection | add creative-field projection after canonical lifecycle works |
| `adapters/langgraph` | optional orchestration boundary | defer real use until operator contracts and replay semantics are proven |
| `adapters/deepseek-harness-context-intelligence` | agent/runtime integration and context injection | consume `CreativeContextPacket`; never own field semantics |
| `apps/brand-lab` | snapshot compiler, diagnostics, simple local server | reuse read-only exploration patterns; keep Brand Lab read-only |
| `workspaces/<brand>` | scoped configuration, source registries, world records, visual language | add creative-project manifests, operator-pack bindings, synthetic fixtures, and generated-state references |

## 4. Target package and application topology

```text
packages/
  testflight-semantic/                 # unchanged shared kernel
  testflight-brand/                    # Brand ontology and bindings
  testflight-creative-field/           # new domain contracts and deterministic lifecycle
  testflight-operator-runtime/         # new provider-neutral operator execution contracts
  testflight-context-intelligence/     # world + field projection compiler

adapters/
  local-evidence/                      # content-addressed local asset bytes and metadata
  sqlite-semantic/                     # canonical record persistence
  cognee/                              # rebuildable creative-field projection
  <model-provider>/                    # provider-specific structured inference
  <creative-tool>/                     # generation connector(s)

apps/
  creative-studio/                     # board, inspector, field review, connection, evaluation
  brand-lab/                           # remains read-only world explorer

reasoning/operators/
  creative-field/                     # versioned transformational operator contracts

workspaces/<brand>/creative-field/
  projects.yaml                        # tracked configuration/fixtures only
  dimension-registry.yaml
  operator-pack.yaml
  certification_cases/
```

Do not add an external runtime dependency without first updating `upstreams/registry.yaml`.

## 5. Canonical model

### 5.1 Creative project and board

- `CreativeProject`: project identity, purpose, Brand workspace, context, participants, and active
  bindings.
- `Moodboard`: stable board identity and lifecycle.
- `BoardRevision`: immutable board snapshot/event projection.
- `ReferenceAsset`: stable identity for image, text, URL snapshot, audio, video, object, or note.
- `Placement`: position, scale, order, crop, centrality, and adjacency within one board revision.
- `ReferenceCluster`: user-created or proposed grouping with explicit authority.
- `UserAnnotation`: emphasis, correction, desired transfer, anti-transfer, or free note.
- `SourceLicenseRecord`: origin, ownership, retention, analysis, generation, and disclosure policy.

### 5.2 Observation and interpretation

- `ObservedFeature`: a bounded feature anchored to an image region or text span.
- `ReferenceInterpretation`: a proposed explanation of why a reference matters to this project.
- `ReferenceContribution`: the role, dimension, polarity, scope, weight, and transfer behavior of a
  reference.
- `CreativePrimitive`: a reusable meaning-bearing unit such as restraint, recursive order, or
  warmth.
- `InterpretationAlternative`: a competing reading retained until evidence or review resolves it.
- `ReviewDecision`: accept, modify, reject, split, merge, or defer with actor authority.

### 5.3 Creative Field

- `FieldDimension`: extensible registry item; initial dimensions are visual, material, temporal,
  spatial, rhetorical, emotional, symbolic/narrative, structural, interaction, and
  social/strategic.
- `DimensionState`: one field version's configuration of a dimension.
- `Principle`: a governing relation or conditional rule.
- `Tension`: a productive polarity to preserve, not average away.
- `Exclusion`: a property, association, motif, or behavior that must not transfer.
- `FieldConflict`: incompatible contributions or unresolved alternatives.
- `MissingDimension`: a material unknown that must remain empty or trigger a question.
- `CreativeFieldProposal`: model-produced, reviewable synthesis with a semantic diff.
- `CreativeFieldVersion`: immutable reviewed field with lineage and dependency manifest.

### 5.4 Connections and runtime artifacts

- `ProjectBinding`: connects the CreativeProject to one Brand workspace, context, and set of target
  entity IDs.
- `FieldBinding`: connects one field version to Brand, Offering, Product, Audience, Campaign,
  Channel, Occasion, or artifact-family entities under explicit scope and precedence.
- `LocalOverride`: request-scoped change that never mutates the field.
- `CreativeRequest` and `ResolvedCreativeRequest`: resolve project, field, task, modality, target,
  world scope, permissions, and ambiguity.
- `FieldProjection`: target-neutral, task- and modality-specific view of the field.
- `CreativeContextPacket`: composition of `ResolvedWorldView`, resolved visual language where
  applicable, `FieldProjection`, task facts, conflicts, omissions, and receipts.
- `TargetCapabilityManifest`: controls and media accepted by a target provider/tool.
- `GenerationPacket`: target-specific translation of the context packet.
- `InvocationReceipt`, `CreativeOutput`, `OutputEvaluation`, and `FeedbackRecord`.

## 6. Connections to the existing world

### 6.1 Board and project connection

The user selects a Brand/client project once. `ProjectBinding` records:

```yaml
project_id: project:hellobiotic:summer
workspace_id: world://workspace/brand/hellobiotic-research
context_id: context:hellobiotic:summer
target_entity_ids:
  - world://brand/hellobiotic
  - offering:hellobiotic:deodorant
branch_id: branch:main
```

Every board revision, interpretation, field, and artifact derives its default scope from this
binding. An explicit local override may narrow it but cannot silently widen it.

### 6.2 Field and entity connection

`FieldBinding` is implemented using the semantics of `RepresentationBinding` plus a creative-field
payload. It records exact field version, target entity IDs, context, applicable artifact types,
channels, time, mode, priority, and authority.

Where several roles must remain explicit, create a `RelationshipFrame` such as
`CreativeFieldApplication` with bindings for field, Brand, offering, audience, campaign, channel,
occasion, and artifact family.

### 6.3 Artifact workflow connection

The artifact workflow resolves two inputs independently:

```text
WorldViewResolver(Project + Context + Branch + Perspective)
  -> ResolvedWorldView

FieldProjectionCompiler(FieldVersion + Request + Lens + LocalOverride)
  -> FieldProjection

compose under policy
  -> CreativeContextPacket
```

The artifact operator receives the combined packet. It does not query the entire Brand workspace,
board, or evidence vault. Every selected and omitted record is listed in the receipt.

### 6.4 Learning connection

An output evaluation may propose an output-only correction, packet correction, projection rule
change, reference interpretation correction, new field version, or Brand-world hypothesis. The
proposal is routed to its owning module and reviewed. Evaluation never writes directly into the
Brand world or Creative Field.

## 7. Operator system

### 7.1 Operator contracts

Create and register these contracts under `reasoning/operators/creative-field/`:

| Operator | Input | Output |
|---|---|---|
| `observe-reference@1` | bounded source asset and technical metadata | `ReferenceObservationProposal@1` |
| `interpret-reference-role@1` | observations, project purpose, annotations, local board context | `ReferenceInterpretationProposal@1` |
| `compare-references@1` | selected interpretations/contributions | patterns, differences, roles, outliers and conflicts |
| `synthesize-creative-field@1` | contributions, annotations, reviews and parent version | `CreativeFieldProposal@1` |
| `project-field@1` | field version, request, lens and override | `FieldProjection@1` |
| `translate-projection@1` | projection and capability manifest | `GenerationPacket@1` proposal |
| `evaluate-creative-output@1` | output, request, projection and packet | `CreativeEvaluation@1` |
| `integrate-creative-feedback@1` | feedback and dependency graph | minimal change proposal and stale set |

Each operator specifies context requirements, preconditions, procedure, invariants, forbidden
shortcuts, hold conditions, output schema, evaluators, and evidence basis. Existing guardrail
operators wrap the transformational operators.

### 7.2 Client-specific operator packs

A client pack is configuration over general operators unless the transformation genuinely differs:

```yaml
pack_id: operator-pack:hellobiotic@1
workspace_id: world://workspace/brand/hellobiotic-research
operators:
  interpret-reference-role:
    context_selectors: []
    vocabulary_refs: []
    priority_principle_refs: []
    forbidden_association_refs: []
    evaluator_rubric_ref: rubric:hellobiotic:creative-field@1
```

Client packs reference accepted Brand-world records. They do not duplicate those records inside
prompts and do not grant permission to use restricted material.

### 7.3 Provider routing

The new `testflight-operator-runtime` owns `OperatorExecutor`, `ModelCapabilityManifest`,
`OperatorRoute`, `ExecutionPreflight`, `OperatorRunReceipt`, and `OperatorResult` interfaces.
Routes are selected by operator, modality, privacy class, structured-output support, context/media
limits, cost ceiling, and availability. Provider adapters translate the stable operator contract
into provider requests. The route and effective redacted configuration enter the derivation ID.

There is no semantic fallback for observation, interpretation, synthesis, cross-modal projection,
or evaluation. Provider failure returns `held`, `partial`, or `unavailable`. Deterministic logic may
hash, transcode, validate, route, enforce policy, and replay state.

## 8. Storage and projection

### 8.1 Runtime data root

Add a non-secret configuration reference such as `TESTFLIGHT_DATA_ROOT`; never commit a runtime
database or client asset. Recommended local shape:

```text
<data-root>/creative-field/<workspace>/<project>/
  assets/sha256/<hash>
  thumbnails/<hash>
  events.sqlite3
  traces/<run-id>/
  exports/<artifact-id>/
```

### 8.2 Canonical storage

- Original bytes: content-addressed filesystem evidence adapter.
- Board edits, review decisions, versions and feedback: append-only events.
- Current canonical identities and relations: SQLite repository projection for the first release.
- Operator outputs: immutable proposal artifacts plus derivation receipts.

The repository enforces immutable source identity, expected prior revision, unique output
derivation, referential integrity, and accepted-only promotion APIs.

### 8.3 Rebuildable projections

- Cognee: candidate retrieval, relationship exploration, and bounded graph navigation.
- Multimodal/vector indexes: candidate recall only; never determine governing field versions.
- UI snapshots, thumbnails, packets, and evaluations: disposable derived caches.

## 9. End-to-end behavior

1. **Create project:** persist `CreativeProject` and `ProjectBinding`; resolve Brand scope, context,
   branch, entities, participants and privacy policy.
2. **Capture:** preserve original bytes and source/licence metadata; create `ReferenceAsset`,
   placement, grouping and annotation events without inferring meaning.
3. **Observe:** run `observe-reference` on bounded media and retain exact regions/spans,
   configuration, uncertainty and proposal status.
4. **Interpret:** compile project purpose, permitted local board context, observations, annotations
   and bounded Brand context; propose role, carry-forward, anti-transfer, dimensions and alternatives.
5. **Review:** accept, edit, reject, split, merge or defer consequential interpretation proposals.
6. **Synthesize:** propose patterns, roles, outliers, tensions, conflicts, exclusions and missing
   dimensions with coverage and a semantic diff.
7. **Approve and bind:** create immutable `CreativeFieldVersion` and explicit `FieldBinding`
   records to relevant Brand-world entities and workflows.
8. **Resolve artifact request:** resolve project, field, world view, task, audience, modality,
   target capabilities, permissions, time and local override.
9. **Compile:** compose target-neutral `FieldProjection`, `ResolvedWorldView`, applicable visual
   language, conflicts and omissions into `CreativeContextPacket`.
10. **Translate and invoke:** create capability-honest `GenerationPacket`, run disclosure
    preflight, call the provider adapter and preserve the exact receipt.
11. **Evaluate:** assess field fidelity, exclusion violations, task fitness, execution quality and
    target limitations separately.
12. **Correct and learn:** route feedback to the smallest affected record, mark dependents stale,
    selectively recompute, and create reviewed successor versions without rewriting history.

## 10. Creative Studio experience

Create `apps/creative-studio` as a separate composition root. Reuse Brand Lab's server,
snapshot and diagnostic patterns initially, but do not make Brand Lab write canonical state.

The first release needs:

1. Project selector with visible Brand-world scope.
2. Board with upload/drop, ordered arrangement, grouping and lightweight annotations.
3. Reference Inspector with sources, observations, interpretations, alternatives, carry-forward
   and anti-transfer choices.
4. Field View with principles, tensions, exclusions, reference roles, conflicts and gaps.
5. Semantic diff and approve/new-version action.
6. Binding panel showing Brand entities and artifact workflows.
7. Text and image projection previews.
8. Packet, trace and evaluation inspection.

A full spatial canvas, collaboration, mobile-native app, field mixing and advanced Harness View
follow after the semantic vertical slice passes.

## 11. API and command surface

Begin with application commands over typed services; expose HTTP or MCP later through thin
adapters:

```text
create_project
create_board
add_reference
place_reference
annotate_reference
request_observation
request_interpretation
review_interpretation
synthesize_field
review_field
activate_field_binding
compile_creative_context
invoke_creative_target
evaluate_output
record_feedback
```

Queries such as inspect, compare, trace, preview and why never mutate. Commands create events or
proposals and require explicit authority at promotion and invocation boundaries.

## 12. Test strategy

### 12.1 Contract, model, repository and replay tests

- Public artifacts reject unknown fields and accepted/version records are immutable.
- IDs, references, project scope, authority, time, revision lineage and derivations resolve.
- Proposal, review and canonical statuses cannot be confused.
- Unknown dimensions round-trip but are not actionable without a registered handler.
- Binary assets deduplicate without collapsing distinct source identities.
- Board revisions replay deterministically and conflicting expected revisions fail atomically.
- Corrections preserve history and mark exactly dependent artifacts stale.
- A project rebuilds from source bytes, events and manifests.

### 12.2 Operator tests

- Schema, invariants, semantic quality and usefulness are evaluated separately.
- Every interpretation resolves to exact evidence or explicit user instruction.
- Provider output cannot promote its own proposal.
- Missing intelligence yields an honest non-success status.
- Instructions embedded in imported content cannot override operator contracts.

### 12.3 Gold semantic fixtures

1. A dominant colour is irrelevant; rhythm/composition carry and colour is excluded.
2. “Minimal but not sterile” survives interpretation, field synthesis, projection and evaluation.
3. An outlier contributes typography only and neither disappears nor dominates.
4. Gradual revelation translates into text and image differently without literal copying.
5. Contrary projects for one client never leak into each other.
6. A correction invalidates only records derived from the corrected contribution.
7. A missing temporal dimension stays missing.
8. A restricted asset remains local and is absent from external disclosure.
9. Model interpretation stays proposed until user review.
10. A target lacking reference controls receives an honest reduced packet.

### 12.4 Integration, adapter, UI and value tests

- Board import -> observation -> interpretation review -> field version.
- Project/field binding -> exact entity and world-view resolution.
- One field -> distinct, grounded text and image projections.
- Cross-workspace packet composition is rejected.
- Generation adapters receive only declared packets and permitted assets.
- Artifacts trace through packet, field, interpretations and original evidence.
- Provider implementations run the same fixtures without consumer changes.
- Browser tests cover upload, annotation, correction, approval, binding, projection and trace.
- Compare prompt-only, ordinary moodboard and reviewed Creative Field workflows for coherence,
  genericness, articulation time, repeated explanation, correction burden and felt control.

## 13. Build sequence and gates

### Block A — Contracts and local lifecycle

Tasks 001–004 establish the ADR, package, canonical models, local evidence store, operator
contracts and gold fixtures. Gate: deterministic replay and contract tests pass with fake operator
results.

### Block B — One board to one reviewed field

Tasks 005–007 add provider routing, image/text observation, interpretation, review, synthesis and
immutable versioning. Gate: core semantic gold cases pass independent review.

### Block C — World and artifact integration

Tasks 008–009 implement ProjectBinding, FieldBinding, relationship frames, field resolution,
`FieldProjection` and `CreativeContextPacket`. Gate: cross-workspace leakage is zero and one field
produces distinct grounded text/image projections.

### Block D — Human and connector loop

Tasks 010–011 provide the review UI, one text connector, one image connector, output evaluation
and feedback-driven invalidation. Gate: a user completes the vertical slice and every external
disclosure has a receipt.

### Block E — Projection and certification

Tasks 012–013 add the Cognee child projection, operations and certification. Gate: projections
rebuild from canonical state, semantic fixtures pass, and `make check` succeeds.

## 14. Expected file changes

```text
docs/decisions/0005-moodboard-creative-field-profile.md
packages/testflight-creative-field/**
packages/testflight-operator-runtime/**
reasoning/operators/index.yaml
reasoning/operators/creative-field/*.yaml
adapters/local-evidence/**
adapters/sqlite-semantic/**
adapters/cognee/**
packages/testflight-context-intelligence/src/contracts.ts
packages/testflight-context-intelligence/src/engine.ts
apps/creative-studio/**
workspaces/brand-hellobiotic-research/creative-field/**
scripts/validate_creative_field_workspace.py
scripts/populate_creative_field_projection.py
scripts/certify_creative_field.py
upstreams/registry.yaml                         # only for a new external dependency
Makefile
pnpm-workspace.yaml
pyproject.toml
```

## 15. Completion criteria

- Original references and user actions are recoverable.
- Every accepted field item traces to evidence or explicit user instruction.
- Project scope prevents cross-client and cross-project leakage.
- Corrections can change why a reference matters without rebuilding unrelated meaning.
- An approved field binds explicitly to Brand entities and artifact workflows.
- Text and image projections preserve a shared deeper field without surface copying.
- Provider calls use capability/privacy preflight and produce receipts.
- No proposal is promoted and no external action occurs without authority.
- Evaluation separates field fidelity, task fitness, execution quality and target limitations.
- Canonical state rebuilds Cognee, UI snapshots, projections and packets.
- Semantic fixtures, adapter conformance, browser flow and operational checks pass.
- `make check` passes without committing runtime assets, databases, secrets or generated stores.

## 16. Reasoning and evaluator record

- `world://operator/guardrail/boundary-conflation@1` — **pass**: every evidence,
  semantic, runtime and agency crossing has a named handoff.
- `world://operator/guardrail/ontology-conflation@1` — **pass**: ontology types, project
  instances, storage records and UI views remain distinct.
- `world://operator/guardrail/configuration-runtime@1` — **partial**: route contracts are
  specified; concrete provider choices remain deliberately open.
- `world://operator/guardrail/evaluation-schema@1` — **pass at plan level**: schema,
  invariants, semantic quality, usefulness and product outcomes are separate dimensions.
- `world://operator/guardrail/validation-persistence-conflation@1` — **pass**: proposals,
  review and persistent versions use separate lifecycle operations.
- `world://operator/guardrail/retrieval-reasoning-conflation@1` — **pass**: Cognee and
  multimodal indexes retrieve candidates; operators interpret downstream.

Provider selection, UI canvas technology, detailed licence policy and calibrated semantic
thresholds remain explicit decisions for Tasks 001, 004 and 005.
