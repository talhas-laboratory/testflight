# Founder Brand World Build Order

**Status:** Recommended implementation sequence  
**Date:** 2026-09-04  
**Scope:** One-founder paid pilot of the Brand World Seeder  
**Companion:** [Founder Brand World Product Overview](2026-09-04-founder-brand-world-product-overview.md)

## 1. Build-order principle

Build the smallest end-to-end path first, then make each part reliable and intelligent.

Do not build all frontend screens, then all infrastructure, then all semantic logic. That delays the
most important discovery: whether the modules actually preserve evidence and meaning across their
handoffs.

The first walking skeleton should do only this:

```text
authenticate one founder
  -> create one intake session
  -> save one text note
  -> preserve it as source evidence
  -> run one test extraction
  -> show one proposal to the expert
  -> record one review decision
```

It can initially be visually plain and use a deterministic extraction fixture. Once this complete
path works, add offline behavior, voice, documents, real operators, clarification and EU hosting in
dependency order.

### Approaches considered

1. **Platform first:** build infrastructure and generalized services before the user flow. This
   produces reusable components but delays product learning and encourages unnecessary abstraction.
2. **Interface first:** prototype the polished notebook and clarification screens with fake data.
   This tests feel quickly but leaves storage, evidence and review semantics unproven.
3. **Vertical slices — recommended:** build one thin real path, then deepen it. This exposes bad
   boundaries early while still producing something testable after every stage.

## 2. Ordered stages

```text
0 Contracts and fixture
    ↓
1 Local walking skeleton
    ↓
2 Trustworthy text capture
    ↓
3 Attachments and voice
    ↓
4 Processing worker
    ↓
5 Brand interpretation
    ↓
6 Clarification loop
    ↓
7 Expert review
    ↓
8 Canonical handoff
    ↓
9 EU deployment and operations
    ↓
10 Pilot rehearsal and paid test
```

Each stage has a gate. Do not proceed merely because its screens exist; proceed when its contract
and failure behavior pass.

## Stage 0 — Freeze the pilot contract and fixture

### Purpose

Prevent UI or database convenience from defining the product's meaning.

### Build

- Confirm the pilot state machine:
  `SETUP -> CAPTURE -> PROCESSING -> CLARIFICATION -> REVIEW_READY -> EXPERT_INTEGRATION`.
- Define only the first required records:
  - `FounderWorkspace`;
  - `IntakeSession`;
  - `NotebookEntry` and immutable revisions;
  - `Attachment` and processing status;
  - `ClarificationQuestion` and answer revisions;
  - proposal, derivation and review-decision envelopes;
  - `ProcessingJob` and attempt receipts.
- Define application ports:
  - identity verification;
  - operational record store;
  - blob store and signed upload;
  - transcription;
  - document parsing;
  - operator execution;
  - clock and identifier generation.
- Create one synthetic founder fixture containing clear claims, ambiguity, contradiction and a
  missing topic.
- Define the expected provisional World and review decisions for that fixture.
- Add chosen upstreams to `upstreams/registry.yaml` before importing them.

### Do not build

- a universal intake ontology;
- production UI;
- multi-brand administration;
- marketing artifacts;
- automatic World mutation.

### Gate

Every field has one semantic owner. A note is not a claim, a mention is not an entity, and a
proposal is not an accepted World record. The synthetic fixture has expected outputs and explicit
`ask`, `hold`, `branch`, `partial`, and `no_hit` cases.

## Stage 1 — Local walking skeleton

### Purpose

Prove that the new application can connect to the existing Testflight system.

### Build

- Scaffold `apps/brand-intake-web` with React, TypeScript and Ionic.
- Scaffold `apps/brand-intake-api` with FastAPI.
- Initialize the local Supabase development stack and version-controlled migrations.
- Add founder magic-link authentication and workspace scoping.
- Implement:
  - create intake session;
  - create one text entry;
  - retrieve the entry;
  - enqueue a deterministic test processing job;
  - create one proposal;
  - show it in a minimal expert view;
  - record accept/reject without writing the canonical World.
- Add adapter health probes and local configuration preflight.

### Open-source software

- Ionic React;
- FastAPI and Pydantic;
- Supabase CLI, PostgreSQL, Auth and Storage.

### Gate

One command starts the reproducible local environment. One authenticated founder can save a note,
and one expert can see its source-linked proposal and record a decision. No provider-specific type
appears in `testflight-ingestion` or existing domain packages.

## Stage 2 — Trustworthy text capture

### Purpose

Make the notebook safe enough for a founder to trust with unfinished thoughts.

### Build

- Design the quiet mobile notebook and three-day session experience.
- Add autosave and immutable entry revisions.
- Add Dexie as the local draft store and mutation outbox.
- Generate client-side UUIDs before synchronization.
- Add idempotent create/update commands and optimistic concurrency.
- Show local, synchronizing, synchronized and failed states without technical language.
- Add installed-PWA behavior and mobile safe-area handling.
- Add optional prompts that never block free writing.
- Add session progress without streaks, scores or pressure.

### Open-source software

- Ionic React;
- Dexie/IndexedDB;
- Supabase operational storage.

### Gate

Typing survives refresh, browser termination, temporary network loss and repeated submission. A
retry creates no duplicate entry or revision. The founder can always distinguish saved from unsaved
work.

## Stage 3 — Attachments and voice capture

### Purpose

Let the founder contribute knowledge in the forms in which it already exists.

### Build

- Add audio recording, playback and explicit submit/discard controls.
- Add image, PDF and document attachments.
- Add Uppy for validation, progress, retry and cancellation.
- Store files through signed upload flows and provider-neutral attachment manifests.
- Record checksum, media type, size, rights/disclosure state and logical owner.
- Keep recording and file metadata usable even before transcription or parsing succeeds.
- Add clear limits for supported file types, sizes and recording duration.

### Open-source software

- Browser MediaRecorder APIs;
- Uppy;
- Supabase Storage;
- tus only if real mobile tests show it is necessary.

### Gate

Interrupted or repeated uploads do not create duplicate attachments. Every stored blob has a
manifest and checksum. Unsupported content returns a useful rejection, and a failed processor never
causes the original source to disappear.

## Stage 4 — Processing worker and normalized evidence

### Purpose

Turn founder material into traceable content without yet interpreting it as Brand truth.

### Build

- Create `workers/brand-intake-worker`.
- Implement PostgreSQL-backed job leasing, attempt records, bounded retry and cancellation state.
- Add the Docling document-ingestion adapter.
- Add the faster-whisper transcription adapter or an equivalent hosted adapter behind the same
  port.
- Convert results into existing `SourceEnvelope`, `ContentUnit` and source-segment contracts.
- Preserve page, time span, table, speaker, file and checksum references.
- Store processor version, configuration, timestamps, warnings and partial-failure receipts.
- Add reprocessing as a new derivation, never an overwrite of the original source.

### Open-source software

- Docling;
- faster-whisper;
- PostgreSQL job table initially.

### Gate

Every derived segment resolves to an exact original note, page or audio time span. Retrying an
identical job produces one validated semantic result and separate attempt receipts. Partial parser
or transcription output is visibly partial.

## Stage 5 — Brand interpretation and provisional World

### Purpose

Create the first differentiated Testflight value: an evidence-backed proposal of what the founder
appears to mean.

### Build

- Add the smallest intake operators for:
  - mentions and referent hypotheses;
  - founder claims and epistemic classification;
  - candidate entities and relationships;
  - audience, offering and Brand-module mapping;
  - contradictions and ambiguity;
  - knowledge gaps and unsupported beliefs.
- Execute them through the existing provider-neutral operator runtime.
- Reuse existing semantic and Brand records instead of inventing intake-specific entity models.
- Persist proposal records, evidence links, operator/version/configuration and evaluator results.
- Compile a provisional Founder Brand World read model.
- Keep local vocabulary local; emit an ontology-extension proposal only when representation would
  otherwise distort the source.

### Existing Testflight software

- `testflight-content`;
- `testflight-semantic`;
- `testflight-brand`;
- `testflight-operator-runtime`;
- optional Cognee projection for retrieval, never canonical storage;
- optional LangGraph execution adapter, not required for the pilot state machine.

### Gate

Every material proposal cites exact source evidence and a derivation. Founder belief remains
distinct from verified external fact. Known ambiguity is preserved rather than resolved by model
confidence. The synthetic fixture meets its expected proposal and failure outcomes.

## Stage 6 — Coverage assessment and clarification loop

### Purpose

Ask only questions that materially improve the Brand World.

### Build

- Define initial coverage targets: purpose, offering, audience, customer problem, desired outcome,
  differentiation, proof, voice, creative boundaries and business constraints.
- Create `CoverageAssessment` containing covered, missing, conflicting and unsupported topics.
- Rank question candidates by expected information value, materiality and founder effort.
- Add stopping rules and daily question limits.
- Build custom `QuestionCard`, `AnswerComposer`, `AnswerHistory` and `SourceReason` components.
- Support text, dictation, skip, “I do not know,” revise and defer.
- Preserve the selection rationale and source references for every question.
- Feed answers back through the same evidence and interpretation pipeline.

### Open-source software

- Existing Ionic components;
- browser dictation/recording plus the transcription adapter;
- no general chat platform initially.

### Gate

The planner asks one understandable question at a time, can explain why it matters, and stops when
remaining questions are low value. Answers update coverage without overwriting earlier evidence.

## Stage 7 — Expert review workspace

### Purpose

Turn model interpretation into a responsible client deliverable.

### Build

- Create a review queue grouped by important Brand concepts rather than operator runs.
- Show proposal, exact source excerpts, derivation, conflicting views and unresolved gaps together.
- Add accept, revise, reject, hold and branch commands.
- Require expected revision and authority identity for decisions.
- Create an immutable `ReviewBundle` and exportable provisional World report.
- Add an audit trail and correction metrics.
- Let the expert prepare a founder-review agenda from material conflicts and gaps.

### Reuse

- Creative Field proposal/review/version patterns;
- existing semantic decisions, branches and evidence links;
- Ionic UI primitives.

### Gate

No proposal can become accepted merely through extraction success. Every decision identifies actor,
time, authority, reviewed proposal revision and rationale. Unreviewed, rejected and held proposals
remain separate from accepted knowledge.

## Stage 8 — Controlled canonical handoff

### Purpose

Connect the new product to the existing Brand World without automating past the agreed pilot scope.

### Build

- Produce a validated, provider-neutral `WorldDeltaProposal` export.
- Include stable proposed identities, exact source and derivation references, review decisions,
  conflicts, local vocabulary and held ontology extensions.
- Build a read-only preview of how accepted proposals map to current Brand types.
- Add deterministic validation against the current ontology and semantic contracts.
- Keep actual promotion manual for the first paid pilot.
- Record the expert's final mapping/integration receipt.

### Gate

You can reproduce every integrated Brand record from the founder input and review history. Export
and re-import preserve identifiers and versions. Nothing writes the canonical World without the
expert's explicit integration action.

## Stage 9 — Managed EU deployment and pilot operations

### Purpose

Move the proven local system into a safe environment for real client data.

### Build

- Create the managed Supabase project in the selected EU region.
- Deploy the FastAPI application and Python worker in an approved EU environment.
- Apply the same migrations and storage policies used locally.
- Add workspace isolation and row-level policies.
- Configure secrets by reference and verify effective runtime configuration.
- Add TLS, rate limiting, structured logs, error reporting and dependency health checks.
- Configure backups, retention, deletion and export procedures.
- Verify provider regions, subprocessors, model-use policies and DPA coverage.
- Run local-to-hosted migration and checksum verification.
- Add a support and recovery runbook.

### Do not add yet

- Trigger.dev unless the simple worker is operationally insufficient;
- Capacitor or app-store deployment;
- assistant-ui;
- SSO/SCIM;
- autonomous publishing;
- broad multi-tenant administration.

### Gate

The hosted environment passes access-isolation, backup/restore, deletion, upload, job-retry,
configuration-preflight and sample-derivation tests. No client data is accepted before these checks
and the privacy terms are ready.

## Stage 10 — Pilot rehearsal and paid founder test

### Purpose

Test product value, not merely technical completion.

### Build and run

- Complete one internal end-to-end rehearsal with the synthetic fixture.
- Complete one rehearsal with a real but non-client Brand owned by the team.
- Fix only pilot-blocking usability, reliability and interpretation issues.
- Create founder onboarding, consent, support and session instructions.
- Create the expert review and integration procedure.
- Instrument first-party product measures.
- Run one paid founder engagement.

### Pilot-ready definition

- no known path loses a completed note, answer, recording or document;
- every material proposal is source-linked and reviewable;
- failures become retry, partial or hold states rather than false success;
- the founder can complete capture and clarification without technical assistance;
- the expert can correct and integrate the result without editing raw database state;
- export and deletion work;
- the reviewed World produces a useful founder/client conversation;
- the result is suitable for testing one downstream campaign brief.

### Measure

- completion and abandonment by session;
- founder time and reported effort;
- useful versus unnecessary clarification questions;
- proposal acceptance, correction, rejection and hold rates;
- source coverage and unresolved gaps;
- expert review and integration time;
- founder agreement with the reviewed World;
- improvement in a downstream brief;
- willingness to pay and repeat.

## 3. What to build after the pilot

Do not begin artifact automation until the pilot shows that the reviewed World is useful. Then
build in this order:

1. exact applicability and version resolution;
2. immutable artifact context manifest;
3. Campaign Brief profile, composer, evaluator and review lifecycle;
4. Markdown/PDF renderer;
5. Message Matrix as a child of the approved brief;
6. Social Campaign Pack as a child of the brief and message matrix;
7. post-render quality evaluation;
8. one document delivery adapter;
9. publication and outcome ingestion only after explicit demand.

The Campaign Brief is the correct first artifact because it tests whether the World can be turned
into a familiar, valuable marketing deliverable before adding expensive asset production.

## 4. Dependency and parallel-work rules

Some work can proceed in parallel after Stage 0:

- visual notebook design can proceed beside the local API skeleton;
- Docling and transcription adapter spikes can proceed beside trustworthy text capture;
- synthetic operator fixtures can be authored before the real worker is complete;
- EU provider evaluation can begin early, but production deployment waits for the local vertical
  slice.

These dependencies must remain sequential:

- reliable source capture before semantic extraction;
- normalized evidence before proposal evaluation;
- proposal extraction before clarification planning;
- clarification before final review-bundle compilation;
- review decisions before canonical integration;
- complete local recovery behavior before accepting hosted client data;
- reviewed World value before artifact automation.

## 5. Testing rule

Testing is part of each stage, not a final stage. Every new adapter requires:

- an entry in `upstreams/registry.yaml` before a new external runtime dependency is used;
- a descriptor and provider boundary;
- a dependency-free health probe;
- contract tests with a fake implementation;
- integration tests against the selected local upstream;
- failure, partial-result and retry tests;
- documentation and configuration preflight.

Every semantic handoff must test that evidence, entity identity, version, workspace, authority,
uncertainty and derivation survive unchanged.

## 6. Reasoning and evaluator record

This build order applies:

- `boundary-conflation@1`: pass; every stage finishes at a typed handoff rather than collapsing
  source, interpretation, review and canonical mutation.
- `retry-idempotency@1`: pass in design; local sync, uploads, jobs and semantic results distinguish
  stable identity from execution attempts.
- `configuration-runtime@1`: partial until local and hosted preflight manifests, health probes and
  redacted runtime receipts are implemented.
- `validation-persistence-conflation@1`: pass in design; provider/model output is validated and
  reviewed before promotion.
- `evaluation-schema@1`: partial until synthetic gold fixtures, operator thresholds and pilot
  acceptance criteria are executable.

