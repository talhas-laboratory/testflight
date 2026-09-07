# Biotic End-to-End Artifact Workflows — Implementation Plan

**Date:** 2026-09-07  
**Status:** implementation-ready proposal  
**Initial artifact:** five-card Biotic social carousel with copy, generated images, evaluation,
revision, approval, and local export  
**Knowledge scope:** `world://workspace/brand/hellobiotic-research`  
**Publishing:** explicitly out of scope

## 1. Outcome

Build an agent-invocable workflow set that turns a bounded Biotic creative request into a
source-grounded, visually coherent, reviewed artifact package by composing Testflight's existing
knowledge, reasoning, workflow, Creative Field, connector, persistence, and review modules.

The first complete path is:

```text
authorized creative agent
  -> scoped Biotic context compilation
  -> campaign brief proposal
  -> five-card carousel plan and copy proposal
  -> project-bound Creative Field projection
  -> five capability-aware image packets
  -> authorized image generation
  -> independent multimodal evaluation
  -> bounded revision proposal
  -> authorized human review
  -> approved local export package
```

This is not a benchmark, experiment framework, autonomous publisher, or attempt to infer Biotic's
private Brand truth. Its proof is operational: an authorized agent can discover and execute a
real workflow that uses the current knowledge layer intelligently and returns a usable artifact
with complete lineage and visible limits.

## 2. First-release contract

### 2.1 Included

- One Brand workspace: Biotic / Hellobiotic public research.
- One product context: Brightening Probiotic Deodorant.
- One artifact family: five-card square social carousel.
- Brief, narrative sequence, card copy, caption, five generated images, caveats, and handoff
  manifest.
- Independent evaluation of text and images.
- Selective revision of rejected copy or image cards.
- Explicit accept, revise, reject, hold, and branch decisions.
- Local export only; no social-platform delivery.
- Agent discovery and invocation through the existing authenticated MCP/REST workflow runtime.

### 2.2 Excluded

- Automatic publication, media buying, scheduling, or account access.
- Promotion of public research into an owner-approved Brand World.
- Medical, safety, clinical-efficacy, customer-behavior, or performance conclusions.
- Dynamic selection among arbitrary Brand workspaces.
- Multi-tenant deployment, OAuth, durable LangGraph crash resume, or internet exposure.
- A generic artifact ontology before the first carousel workflow proves the contract.

### 2.3 Completion definition

The increment is complete when an authorized creative agent can invoke the creation workflow and
receive a persisted review-ready bundle; a reviewer can submit a bounded decision or correction;
the revision workflow can selectively rebuild affected parts; and an authorized reviewer can
export an accepted bundle whose files, sources, prompts, model/provider receipts, evaluations, and
review history are reconstructible.

## 3. Architectural decisions

### 3.1 Use three workflows

1. `workflow://testflight/biotic/social-carousel-create@1`
   creates and evaluates a review-ready artifact proposal.
2. `workflow://testflight/biotic/social-carousel-revise@1`
   applies explicit feedback to selected text fields or cards, then re-evaluates the revision.
3. `workflow://testflight/biotic/social-carousel-review-export@1`
   records an authorized human decision and creates a local export only after acceptance.

The split is necessary because the current workflow runtime executes finite acyclic runs and does
not suspend a run while waiting for human input. Human review is therefore a new authorized run,
not a hidden pause inside generation.

### 3.2 Keep workflow semantics portable

Workflow YAML owns topology, input/output schemas, knowledge and authority envelopes, conditions,
retries, and output bindings. The workflow runtime owns authentication and lifecycle. LangGraph
owns scheduling. Handlers compose domain packages and adapters but do not redefine their records.

### 3.3 Keep Brand knowledge, Creative Field, and artifacts distinct

- The Biotic workspace supplies public evidence, attributed claims, visual observations, audience
  signals, held hypotheses, gaps, context, and world-view records.
- A project-scoped `CreativeFieldVersion` governs creative expression for this workflow. It is an
  accepted Testflight project configuration for public-research concept work, not an approved
  Biotic brand guideline.
- An artifact bundle references generated outputs and evaluations. Approving an artifact does not
  accept or mutate Brand knowledge or the Creative Field.

### 3.4 Use explicit agents and authority

Add two runtime principals:

- `agent:biotic-creative`: may discover create and revise workflows, retrieve only the Biotic
  workspace, invoke approved reasoning/image providers, and write proposal-level creative records.
- `agent:biotic-review`: may discover review/export, read the Biotic artifact project, record
  artifact review decisions, and write a local export. It cannot publish externally or mutate the
  Brand World.

The workflow grant supplies the complete allowed authority. Prompts, callers, and retrieved text
cannot widen it.

### 3.5 Make image generation an auditable action

The image call must pass through `TargetCapabilityManifest`, `GenerationPacket`, explicit rights
and disclosure checks, an action ID, a stable idempotency identity, and an immutable invocation
receipt. Generated bytes go to the content-addressed blob store; canonical records retain hashes
and references rather than inline image bytes.

## 4. Workflow data model

### 4.1 Creation input

The creation workflow accepts:

```yaml
request_id: stable caller-supplied id
objective: bounded campaign objective
audience: audience context, not an asserted customer segment
channel: instagram_carousel
occasion: campaign or seasonal occasion
product_id: ENT-HB-OF-001
context_id: CTX-HELLOBIOTIC-DEODORANT-CURRENT
branch_id: research-main
card_count: 5
cta_request: optional requested CTA
valid_time: source-validity date
image_target_id: registered image target
creative_field_version_id: reviewed project field version
```

`product_id`, `context_id`, `branch_id`, `card_count`, and channel are constrained by schema or
deterministic handler validation. A caller cannot use this workflow to request another Brand,
workspace, product family, or arbitrary card count.

### 4.2 Proposed artifact structures

Keep the first artifact schema inside the versioned workflow definition. Add only the generic
cross-run lifecycle records to `testflight-creative-field`:

- `ArtifactBundle`: stable bundle identity, project/request/workflow IDs, revision, parent bundle,
  context packet, field version, output IDs, evaluation IDs, status, and derivation.
- `ArtifactReviewDecision`: bundle revision, disposition, actor, authority grant, rationale,
  feedback IDs, expected revision, and time.
- `ArtifactExportReceipt`: accepted bundle and decision IDs, export manifest URI/hash, exported
  file hashes, status, errors, and derivation.

The brief, carousel plan, copy, and caption are stored as an `application/json` creative output in
the blob store. Each generated card is an image `CreativeOutput`. The bundle groups these outputs
without duplicating their content.

### 4.3 Carousel JSON contract

The structured authoring result contains:

- `brief`: objective, communication task, audience context, product truth, message hierarchy,
  tone, visual direction, exclusions, claims boundaries, gaps, and citations;
- `cards`: exactly five records with stable card ID, narrative role, headline, supporting copy,
  image direction, negative constraints, cited evidence IDs, and production caveats;
- `caption`: body, disclosure/caveat field, CTA, and hashtags;
- `campaign_controls`: cross-card visual anchors, continuity rules, prohibited drift, and
  generation limitations;
- `status`: `proposal`, `partial`, or `hold`;
- `canonical_write`: always `false`.

Claims and disclosures remain separate fields. The image prompt compiler consumes image direction
and permitted visual controls, never medical disclaimers as visual content.

## 5. Workflow 1: create and evaluate

### 5.1 Step graph

```text
validate_request
      |
compile_brand_context
      |
plan_campaign
      |
compose_carousel
      |
validate_copy_and_claims
      |
compile_creative_projection
      |
prepare_image_set
      |
generate_image_set
      |
persist_artifact_bundle
      |
evaluate_artifact
      |
assemble_review_bundle
```

### 5.2 Step responsibilities

#### `validate_request` — deterministic normalizer

- Verify fixed Brand/workspace/product/channel scope.
- Verify context and branch IDs exist.
- Resolve effective date and project identity.
- Reject prompt text that attempts to widen knowledge or authority.
- Return a normalized request or structured `hold`/`ask` outcome.

#### `compile_brand_context` — deterministic/retrieval composition

- Invoke `testflight-context-intelligence` through a stable one-shot JSON process boundary.
- Route independently to core evidence, copy/claims, audience, visual language, and world view.
- Retrieve only from the declared Biotic staging dataset and exact repository manifests.
- Preserve source URLs, evidence IDs, epistemic status, held records, rights, omissions, and trace.
- Return `no_hit`, `partial`, or `hold` instead of adding generic brand knowledge.

The workflow runtime is Python while context intelligence is TypeScript. Add a generic CLI entry
to `packages/testflight-context-intelligence` and a small Python process client in Workflow Runtime.
Do not import the DeepSeek/Cordis plugin into the workflow application.

#### `plan_campaign` — model-backed planner

- Consume only the normalized request and compiled context packet.
- Select the campaign message hierarchy and narrative posture.
- Distinguish intended audience context from validated customer claims.
- List evidence, assumptions, conflicts, unanswered questions, and downstream constraints.
- Emit the strict brief schema through the private operator runtime.

#### `compose_carousel` — model-backed generator

- Produce exactly five semantically distinct cards and a caption.
- Carry the brief's objective, product, message hierarchy, tone, and exclusions forward.
- Attribute product claims and keep caveats in their governed field.
- Create image directions without pretending public observations are proprietary rules.
- Return `hold` if the brief lacks enough support for a requested material claim.

#### `validate_copy_and_claims` — deterministic reviewer

- Verify cardinality, field types, citation references, CTA/caption structure, and per-card IDs.
- Detect prohibited antiperspirant, medical, safety, universal-outcome, or unsupported customer
  claims using explicit policy fixtures.
- Check that every material product claim points to an allowed evidence record.
- Reject invalid output before any image calls occur.

#### `compile_creative_projection` — deterministic domain handler

- Load the reviewed project `CreativeFieldVersion`, project binding, and field binding.
- Resolve the Biotic world view and visual-language revision.
- Call `CreativeBindingResolver` and `CreativeContextCompiler`.
- Persist `CreativeRequest`, resolved request, projection, context packet, target manifest, and
  bindings through the creative repository.
- Preserve missing dimensions and unsupported target controls as explicit limitations.

#### `prepare_image_set` — deterministic connector compiler

- Create one `FieldProjection` specialization and `GenerationPacket` per card.
- Combine shared campaign controls with card-specific narrative and image direction.
- Send only cleared grounding assets. Public site or social images remain textually described
  inspiration unless a license record explicitly permits generation disclosure.
- Validate target modality, dimensions, output format, quality, text-in-image mode, and prompt
  limits against the target capability manifest.

#### `generate_image_set` — authorized batch action

- Use `action://testflight/creative/image-set-generate`.
- Derive stable per-card invocation IDs from workflow, request, bundle revision, card ID, packet
  hash, and adapter version.
- Invoke cards concurrently within a configured bound.
- Persist every attempt, receipt, output hash, and partial failure independently.
- Replay successful cards and retry only retryable failed cards.
- Return partial when some cards fail; never replace a missing image with an uncited stock asset.

Use one batch action step because the current portable workflow schema does not express an
idempotent action loop. Per-card safety remains enforced by connector and repository identities.

#### `persist_artifact_bundle` — proposal action

- Store the structured text output in the blob store.
- Create `CreativeOutput` records for text and images.
- Create `ArtifactBundle(revision=1, status=proposed)` referencing exact outputs and context.
- Never accept the artifact or mutate Brand records.

#### `evaluate_artifact` — independent multimodal reviewer

- Use a separate operator invocation and evaluator instruction from the authoring nodes.
- Inspect actual persisted text and image bytes, not metadata alone.
- Report field fidelity, task fitness, execution quality, governance, cross-card continuity,
  accessibility/readability, limitations, disagreements, and targeted feedback separately.
- Treat wrong product, prohibited claim, missing card, cross-workspace source, or missing lineage as
  a hard failure.
- Persist `CreativeEvaluation` and `FeedbackRecord` proposals.

#### `assemble_review_bundle` — deterministic transform

- Return bundle ID/revision, preview/output references, brief, card copy, evaluations, citations,
  holds, omissions, and trace/receipt IDs.
- Never expose local absolute blob paths through the agent-facing contract; use application-owned
  output references or authorized preview endpoints.

## 6. Workflow 2: selective revision

### 6.1 Input

- `request_id` and new `revision_request_id`;
- current `bundle_id` and expected revision;
- explicit feedback records or reviewer instruction;
- target scope: brief field, caption field, card IDs, copy, image, or both;
- preservation rules;
- same context/field version unless an explicit rebind is reviewed.

### 6.2 Step graph

```text
load_revision_context
      |
classify_revision_scope
      |
revise_structured_artifact
      |
validate_revision_preservation
      |
prepare_changed_images
      |
regenerate_changed_images
      |
persist_bundle_revision
      |
evaluate_revision
      |
assemble_review_bundle
```

### 6.3 Invariants

- Require optimistic concurrency through `expected_revision`.
- Preserve all untargeted text fields and output references exactly.
- Regenerate only cards whose image direction or requested image changed.
- Preserve product identity, objective, evidence attribution, claims boundaries, and governing
  field version unless explicitly targeted by an authorized change.
- Do not copy reviewer instructions into consumer-facing copy.
- Create revision `n+1` with `parent_bundle_id`; never overwrite revision `n`.
- Re-evaluate both the requested fix and semantic continuity with the original accepted request.

## 7. Workflow 3: review and local export

### 7.1 Input and access

- Reviewer principal must be `agent:biotic-review` or carry its explicit role.
- Input includes bundle ID, expected revision, decision, rationale, selected feedback IDs, and
  export request ID.
- `accept` requires an artifact-review authority grant. `revise`, `reject`, `hold`, and `branch`
  remain non-exporting decisions.

### 7.2 Step graph

```text
load_review_bundle
      |
validate_review_authority
      |
record_review_decision
      |
export_accepted_bundle (only when decision == accept)
      |
return_review_result
```

### 7.3 Export package

Write under ignored runtime storage:

```text
.data/artifact-exports/biotic/<bundle-id>/<revision>/
  manifest.json
  brief.json
  carousel-copy.md
  caption.txt
  cards/01.png ... 05.png
  evaluation.json
  sources.json
  receipts.json
```

`manifest.json` records every file hash, media type, bundle revision, review decision, context
packet, field version, source/evidence references, provider/model/adapter versions, unresolved
limitations, and the explicit statement `publishing_authorized: false`.

The exporter writes atomically through a temporary directory followed by rename. Replaying the
same export request returns the existing matching receipt. A changed bundle revision or manifest
hash requires a new export ID.

## 8. Module changes

### 8.1 `packages/testflight-context-intelligence`

Add a one-shot JSON CLI composition entry that:

- loads `INTELLIGENCE.json`;
- constructs the existing engine, visual resolver, world-view resolver, retriever, and trace store;
- reads one context request from stdin;
- writes one `ContextPacket` to stdout;
- emits errors only to stderr and uses a non-zero exit status on transport failure.

Refactor reusable engine construction out of the DeepSeek plugin without moving Cordis imports
into the package. The DeepSeek adapter and CLI must share configuration logic rather than fork it.

Files:

- modify `packages/testflight-context-intelligence/src/index.ts`;
- add `packages/testflight-context-intelligence/src/cli.ts`;
- add or extend package scripts/exports;
- add CLI contract tests under `packages/testflight-context-intelligence/test/`;
- refactor `adapters/deepseek-harness-context-intelligence/src/index.ts` only as needed.

### 8.2 `packages/testflight-creative-field`

- Add artifact bundle, artifact review, and export receipt models.
- Add deterministic validation for revision lineage, output ownership, review disposition, and
  accepted-only export eligibility.
- Add image-target control vocabulary without embedding provider-specific syntax.
- Extend generation packet expected output with explicit count, dimensions, media type, and text
  rendering policy.
- Keep field evaluation and artifact review as distinct records.

Files:

- modify `src/testflight_creative_field/models.py` and `__init__.py`;
- add `src/testflight_creative_field/artifacts.py` if lifecycle logic would otherwise enlarge the
  model module;
- extend `projection.py` only for provider-neutral output requirements;
- add focused tests under `packages/testflight-creative-field/tests/`.

### 8.3 `adapters/creative-connectors`

- Extend the image capability manifest with supported image controls.
- Add a concrete image transport behind the existing `ImageTargetAdapter` protocol.
- Use an environment-named credential reference; never persist or log its value.
- Normalize provider output to bytes plus media type and retain provider request IDs in the
  adapter receipt.
- Enforce timeouts, bounded retry classification, response-size limits, and content-type checks.
- Reject unsupported reference images or parameters before the provider call.

If a new external SDK is required, update `upstreams/registry.yaml` first. Prefer direct HTTP with
the standard library or an already registered HTTP dependency when it keeps the adapter smaller.

Files:

- modify `src/testflight_adapter_creative_connectors/connectors.py` and exports;
- add a provider-specific module inside this adapter;
- add the currently missing adapter README;
- add descriptor/health coverage if the concrete target changes the advertised capability;
- add unit tests with a fake HTTP transport; live calls remain opt-in.

### 8.4 `apps/workflow-runtime`

Add a handler module dedicated to Brand artifact composition. It may import owned packages and
adapters because the application is the composition root.

Handlers:

- `biotic.request.validate`;
- `biotic.context.compile`;
- `creative.campaign.plan` and `creative.carousel.compose` through `PromptStepHandler`;
- `biotic.claims.validate`;
- `creative.field.project`;
- `creative.image_set.prepare`;
- `creative.image_set.generate`;
- `creative.artifact.persist`;
- `creative.artifact.evaluate`;
- `creative.artifact.revise`;
- `creative.artifact.review`;
- `creative.artifact.export`;
- `creative.review_bundle.assemble`.

Use small handler classes grouped by owning boundary, not a single conditional mega-handler.
Introduce ports for context compilation and image transport so tests inject fakes.

Files:

- add `biotic_artifact_handlers.py`;
- add `context_client.py` if the JSON process client is reusable;
- add `artifact_export.py` for deterministic packaging;
- update `config.py` only if typed handler settings are needed;
- add unit and integration tests under `apps/workflow-runtime/tests/`.

### 8.5 Workflow definitions and runtime configuration

Add:

- `workflows/biotic/social-carousel-create.yaml`;
- `workflows/biotic/social-carousel-revise.yaml`;
- `workflows/biotic/social-carousel-review-export.yaml`;
- `workflows/biotic/fixtures/` for tracked synthetic requests, operator responses, image bytes,
  expected bundles, evaluation findings, and continuity cases.

Modify:

- `workflows/registry.yaml` to register all three as candidates first;
- `workflows/runtime.example.yaml` to declare the two principals, environment token references,
  handler module, context CLI command, operator endpoint, creative database/blob roots, image target,
  and export root;
- `.env.example` with variable names and safe non-secret defaults only;
- `AGENT_INDEX.md` only if the supported workflow recipe or module connectivity materially changes;
- the product architecture inventory/dependency map when the new handler/CLI/image connections are
  implemented.

Do not create a new Testflight product knowledge child: these are executable workflows and
implementation connections, not a new knowledge domain.

### 8.6 Creative Studio

Reuse its repository, blob store, preview, and evaluation patterns. Add only what the workflow
review handoff requires:

- load an `ArtifactBundle` by stable ID;
- show the five images, copy, caption, citations, limitations, and evaluation findings;
- record accept/revise/reject/hold/branch through the same artifact lifecycle service used by the
  review workflow;
- show export eligibility and the local export receipt;
- never expose a publish control in this increment.

All new UI must consume `packages/testflight-design-language` and visibly distinguish proposed,
partial, held, accepted, rejected, and failed states.

## 9. Creative Field bootstrap prerequisite

The creation workflow requires one reviewed, project-scoped field version. Create it once before
enabling live generation:

1. Create project `project:biotic:public-research-social` in Creative Studio.
2. Bind it to the Biotic workspace, current deodorant context, `research-main`, and the Brand and
   offering entity IDs.
3. Add permitted textual/public observation records from the visual-language and copy graphs as
   source contributions. Do not upload public site imagery as generation grounding without
   explicit rights.
4. Synthesize a Creative Field proposal preserving the held status of inferred principles.
5. Review it under a Testflight public-research concept authority.
6. Accept a project version for sandbox concept production with limitations stating that it is not
   an owner-approved proprietary system.
7. Bind it only to the social-carousel artifact family and relevant channel/context.

Export a deterministic tracked fixture describing the expected IDs and public limitations, but
keep the live SQLite database and asset bytes under `.data/`.

## 10. Operator contracts

Reuse the existing canonical operators:

- `creative/project-binding@1` for project and entity scope;
- `creative/field-projection@1` for task-specific Creative Field projection;
- `creative/connector-packet@1` for target capability and disclosure preflight;
- `creative/output-evaluation@1` for independent output evaluation;
- `guardrail/evidence-truth-conflation@1` for attributable claims;
- `guardrail/workspace-isolation@1` for every read, write, cache, and trace;
- `guardrail/retry-idempotency@1` for provider calls and exports;
- `guardrail/configuration-runtime@1` for effective runtime receipts;
- `guardrail/validation-persistence-conflation@1` for proposal and approval boundaries;
- `guardrail/evaluation-schema@1` for separate structural, semantic, governance, and usefulness
  results.

Add three executable workflow prompt contracts in workflow YAML rather than cloning general
operator YAML:

- campaign planner instruction;
- carousel composer instruction;
- bounded artifact reviser instruction.

The independent evaluator uses the existing creative output-evaluation operator with a
carousel-specific rubric supplied as versioned configuration.

## 11. Testing strategy

### 11.1 Deterministic contract tests

- Workflow YAML schema and DAG validation.
- Agent discovery allow/deny tests.
- Step knowledge and capability subset tests.
- Fixed Biotic workspace/product/context/branch enforcement.
- Cross-workspace, foreign project, and foreign output denial.
- Context CLI stdin/stdout/error contract.
- Creative record identity, lineage, optimistic concurrency, and accepted-only export.
- Image control negotiation, rights/disclosure rejection, media validation, and output hashing.
- Per-card invocation and export idempotency.
- Partial image-set recovery without duplicate outputs.
- No Brand canonical mutation from create, revise, evaluate, or artifact review.

### 11.2 Generative node test packs

Create isolated packs for:

| Node | Type | Required cases |
| --- | --- | --- |
| `compile_brand_context` | retrieval | relevant selection, irrelevant exclusion, held hypotheses retained, no-hit, cross-workspace denial |
| `plan_campaign` | planner | useful brief, unsupported audience restraint, conflicting evidence, missing objective, generic-strategy regression |
| `compose_carousel` | generator | five-card positive case, minimal valid case, unsupported health-claim attack, missing evidence hold, product/tone drift regression |
| `evaluate_artifact` | reviewer | true finding, false-positive prevention, hard-failure severity, missing image, actionable feedback |
| `revise_structured_artifact` | reviser | targeted correction, stable-field preservation, instruction-leak attack, stale revision rejection, repair-drift regression |

Every pack contains a testing context, golden cases, semantic-adherence cases, deterministic fake
operator responses, and bounded comparators. Exact matching is reserved for IDs, routes, schemas,
field ownership, and unchanged fields; freeform quality uses bounded semantic or explicit rubric
checks.

### 11.3 End-to-end semantic continuity pack

Create one `biotic-social-carousel` continuity pack covering:

- request -> context: correct product, objective, audience status, and claims boundaries survive;
- context -> brief: public claims remain attributed and held hypotheses remain non-factual;
- brief -> carousel: message hierarchy, tone, product identity, and exclusions survive channel
  specialization;
- carousel -> images: visual direction remains Biotic-specific without copying unavailable assets;
- evaluation -> revision: the requested fix is applied while untargeted campaign meaning remains;
- accepted bundle -> export: exported files match the reviewed revision and manifest.

Required case families:

- positive survival;
- channel specialization;
- product, audience, tone, governance, and workflow drift guards;
- review/repair preservation;
- end-state usefulness for a human social-content operator.

Hard failures include wrong product, antiperspirant promise, unattributed efficacy claim, invented
customer segment, missing card, unpermitted grounding asset, cross-workspace evidence, missing
receipt, review/export revision mismatch, or `publishing_authorized: true`.

### 11.4 Runtime integration test

Using fake operator and image transports:

1. Authenticate `agent:biotic-creative`.
2. Discover only create/revise workflows.
3. Invoke create through the generated MCP tool.
4. Assert LangGraph executes the registered topology.
5. Assert the creative SQLite repository and blob store contain the expected proposal records.
6. Invoke revise with one card-scoped correction and assert selective regeneration.
7. Assert creative agent cannot invoke review/export.
8. Authenticate `agent:biotic-review`, accept the revision, and export it.
9. Replay all action request IDs and assert zero duplicate provider calls or exports.
10. Attempt a foreign workspace/project/output reference and assert denial.

### 11.5 Optional live smoke test

Keep live provider execution outside `make check`. Run it only with explicit environment
credentials and a cost cap. The smoke test generates one low-cost five-card set, records effective
model/provider configuration, verifies image decodability and dimensions, runs evaluation, and
produces a local review bundle. It never auto-accepts or exports.

## 12. Implementation sequence

### Increment 0 — Freeze fixture and contracts

1. Add the Biotic request, context expectations, prohibited claims, carousel schema, and fake image
   fixture.
2. Record semantic priorities: governance and source fidelity outrank creative fluency; task
   usefulness outranks decorative similarity when both remain safe.
3. Define all IDs, action IDs, principal IDs, statuses, and expected failure outcomes.
4. Add failing workflow-definition tests before handlers.

**Gate:** the fixture fully specifies success, acceptable variation, prohibited output,
preservation rules, and decision priority without requiring live model judgment.

### Increment 1 — Artifact lifecycle records

1. Add the three generic creative artifact records and validators.
2. Extend SQLite serialization/replay support if model discovery is explicit.
3. Add revision, review-authority, and accepted-only export eligibility tests.

**Gate:** artifact proposal, revision, decision, and export eligibility are reconstructible without
running a model or workflow.

### Increment 2 — Context CLI and client

1. Extract reusable context-engine composition from the DeepSeek plugin.
2. Add the JSON CLI and Python process client.
3. Test exact Biotic configuration, visual revision, world-view selection, trace creation,
   malformed output, timeout, and no-hit behavior.
4. Run against the certified Biotic staging projection; never substitute navigation files as
   evidence.

**Gate:** a Python handler receives a valid, cited Biotic `ContextPacket` with no direct dependency
on Cordis or Cognee internals.

### Increment 3 — Image target capability and transport

1. Extend provider-neutral image control fields.
2. Add the concrete image transport and redacted configuration preflight.
3. Add fake-transport tests for success, partial set, timeout, unsupported controls, invalid media,
   permission denial, and replay.

**Gate:** five image packets can be invoked and persisted with exact per-card receipts; a failed
preflight produces zero provider calls.

### Increment 4 — Creation handlers and workflow

1. Implement request validation and context compilation.
2. Add planner and composer prompt contracts.
3. Implement deterministic claims validation.
4. Compose Creative Field projection and image packets.
5. Generate/persist the image set and text output.
6. Evaluate and assemble the review bundle.
7. Register the candidate workflow and creative principal.

**Gate:** the fake-provider MCP end-to-end creation test passes, including partial/hold behavior and
zero Brand canonical writes.

### Increment 5 — Revision workflow

1. Implement revision scope classification.
2. Add reviser prompt contract and deterministic preservation validator.
3. Reuse successful unchanged outputs and selectively regenerate changed cards.
4. Persist revision lineage and re-evaluate.
5. Register the candidate workflow.

**Gate:** targeted revision and repair-preservation continuity cases pass; stale revisions are
held before any model or image call.

### Increment 6 — Review, export, and Creative Studio handoff

1. Implement artifact review lifecycle service and export packager.
2. Register reviewer principal and review/export workflow.
3. Add Creative Studio bundle loading, decision controls, previews, and export status.
4. Apply Testflight design-language tokens and state treatments.

**Gate:** only the review principal can accept/export; the exported manifest matches the reviewed
revision byte-for-byte and cannot authorize publishing.

### Increment 7 — Certification and operational documentation

1. Add an offline certification command covering all three workflows with fake providers.
2. Add the optional live smoke command and explicit cost/credential preflight.
3. Document local startup order, Biotic projection prerequisite, Creative Field bootstrap,
   recovery, reprocessing, and export inspection.
4. Update repository navigation and product architecture inventories for implemented connections.
5. Promote workflows from `candidate` to `active` only after certification passes.

**Gate:** `make check`, workflow validation, Creative Field certification, Biotic workspace
validation, offline workflow certification, and secret scanning all pass.

## 13. Operational configuration

Add non-secret configuration names for:

- context-intelligence CLI command and timeout;
- Biotic intelligence config and staging dataset;
- operator-runtime endpoint;
- creative SQLite database and blob root;
- image target ID, endpoint, model, credential environment name, request timeout, concurrency, and
  maximum output bytes;
- export root;
- creative and reviewer bearer-token environment names;
- public-research Creative Field version/binding IDs;
- maximum workflow duration and image-call count.

Every run receipt must record resolved non-secret configuration, versions, endpoint class, model
ID, target ID, workspace/project IDs, and credential reference name. Secret values must never enter
workflow inputs, prompts, records, logs, traces, or exports.

## 14. Failure and recovery behavior

- **Context no-hit:** hold before planning and name the missing route/evidence.
- **Context partial:** continue only when the missing material is non-critical; carry omissions into
  the artifact and evaluation.
- **Invalid planner/composer output:** fail the node; do not guess fields or generate images.
- **Claims violation:** hold before image generation and return exact findings.
- **One image fails:** persist successful images and return partial; retry only the failed stable
  invocation.
- **Evaluator unavailable:** keep the bundle proposed and non-exportable.
- **Revision conflict:** hold on expected-revision mismatch with zero downstream calls.
- **Export interruption:** retain the prior accepted bundle and retry atomically by export ID.
- **Provider configuration mismatch:** preflight hold with zero provider calls.
- **Cross-workspace reference:** deny and write a boundary receipt without copying the record.

## 15. Acceptance checklist

- [ ] All three workflows validate and are discoverable only by their assigned principals.
- [ ] Creation produces one structured text output and exactly five image outputs or an explicit
      partial/hold result.
- [ ] Every material claim and creative control resolves to context, evidence, or an explicit
      assumption/limitation.
- [ ] Generated images are linked to card-level packets and immutable invocation receipts.
- [ ] Public reference assets are not disclosed to generation without explicit rights.
- [ ] Evaluation is independent, multimodal, structured, and persisted separately from generation.
- [ ] Revision changes only authorized targets and preserves required semantics.
- [ ] Artifact acceptance does not mutate Brand knowledge or the Creative Field.
- [ ] Export requires the reviewer principal and the exact accepted revision.
- [ ] Export manifest says publishing is unauthorized.
- [ ] Identical action retries do not duplicate provider calls, outputs, decisions, or exports.
- [ ] Cross-workspace/project access is rejected.
- [ ] Offline end-to-end certification passes with deterministic fakes.
- [ ] Optional live smoke produces a review-ready bundle without secret leakage.
- [ ] Root and product architecture indexes describe the implemented connections.
- [ ] `make check` passes.

## 16. Operator and evaluator record

This plan was shaped by the following contracts:

- `world://operator/creative/project-binding@1`: **pass** — field and artifact use remain explicit,
  project-scoped, and authority-bearing.
- `world://operator/creative/field-projection@1`: **pass** — task translation uses a bound field
  version and preserves omissions rather than introducing visual defaults.
- `world://operator/creative/connector-packet@1`: **pass** — image generation requires capability,
  disclosure, permission, and adapter-version preflight.
- `world://operator/creative/output-evaluation@1`: **pass** — evaluation remains independent and
  multidimensional, and feedback remains proposal-only.
- `world://operator/guardrail/workspace-isolation@1`: **pass at design level** — every workflow,
  handler, cache, record, and action is bound to the Biotic workspace/project; runtime enforcement
  remains an implementation gate.
- `world://operator/guardrail/retry-idempotency@1`: **pass at design level** — stable action and
  per-card invocation identities are specified; crash and partial-set tests remain required.
- `world://operator/guardrail/configuration-runtime@1`: **partial** — the design requires effective
  redacted configuration receipts, but the shared service does not yet bind a complete runtime
  configuration manifest to every workflow run.
- `world://operator/guardrail/validation-persistence-conflation@1`: **pass** — schema validity,
  evaluation, proposal persistence, artifact acceptance, Brand mutation, and export are separate.
- `world://operator/guardrail/evaluation-schema@1`: **pass at design level** — structural,
  governance, semantic, continuity, execution-quality, and usefulness judgments remain separate;
  evaluator fixtures and thresholds remain to be implemented.

The generative-node test system supplied the node-level contract, decision, guardrail, failure,
preservation, observability, and semantic-adherence layers. The semantic-continuity test system
supplied the cross-handoff survival, drift, repair-preservation, and end-state usefulness gates.
