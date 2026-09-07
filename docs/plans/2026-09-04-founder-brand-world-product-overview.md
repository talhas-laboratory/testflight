# Founder Brand World Product Overview

**Status:** Proposed product definition  
**Date:** 2026-09-04  
**Initial customer:** One founder, supported by a Testflight expert  
**Deployment:** Local-first development with a portable path to managed EU hosting

**Implementation sequence:** [Founder Brand World Build Order](2026-09-04-founder-brand-world-build-order.md)

**Experience prototype:** [`apps/brand-intake-web`](../../apps/brand-intake-web/README.md)

## 1. Product definition

The product helps a founder externalize the knowledge they carry about their brand and turns that
input into a structured, attributed, reviewable Brand World. That World can later become the
governing context for campaign briefs, messaging, copy, newsletters, social content, visual
directions, and other marketing artifacts.

The founder does not have to understand ontologies, knowledge graphs, prompt engineering, or
marketing schemas. They first use a calm mobile notebook to record raw thoughts. After several
capture sessions, the product asks a small number of easy clarification questions about conflicts,
important gaps, and underspecified concepts. Testflight then prepares a provisional Brand World for
expert and client review.

The system is not a generic chatbot, survey, content generator, or autonomous source of Brand
truth. It is an evidence-preserving knowledge elicitation and application system.

```text
founder expression
  -> preserved source evidence
  -> extracted proposals
  -> focused clarification
  -> provisional Brand World
  -> expert/client review
  -> accepted Brand World
  -> exact task context
  -> reviewed marketing artifacts
```

### What the customer buys

The immediate customer outcome is not an ontology. It is:

- a faster and less cognitively demanding way to explain the Brand;
- a durable map of audiences, offerings, beliefs, differentiation, voice, constraints, and proof;
- visibility into contradictions, assumptions, and missing knowledge;
- less repeated briefing of employees, agencies, and AI systems;
- marketing deliverables grounded in the correct version of Brand knowledge;
- a review trail showing why the system believes or proposes something.

The World model, provenance system, operators, versioning, and infrastructure are the machinery
that makes those outcomes dependable.

## 2. Product scope

### First paid pilot

The first pilot is intentionally narrow:

- one founder;
- one Brand workspace;
- three 30-minute free-capture sessions across three days;
- text notes, voice notes, images, links, and a bounded document set;
- automated processing after capture;
- several days of one-question-at-a-time clarification;
- a provisional Founder Brand World;
- expert review with the founder/client;
- manual expert promotion or mapping into the canonical Testflight World;
- no autonomous publishing and no requirement to generate production marketing assets.

The expert remains the integration authority. Model output remains proposal-only.

### Complete product

The complete product extends the pilot in controlled stages:

1. Capture and clarify founder knowledge.
2. Review and promote accepted knowledge into a versioned Brand World.
3. Resolve the exact Brand context for a marketing task.
4. Compose typed artifact proposals such as campaign briefs and message matrices.
5. Evaluate and review those proposals.
6. Render approved artifacts into useful files or platform formats.
7. Deliver them through explicitly authorized adapters.
8. Connect measured outcomes back as reviewable learning proposals.

The pilot proves the most uncertain premise first: whether low-pressure founder input can produce a
Brand World that is accurate and commercially useful.

## 3. Founder experience

### Phase A: setup

The founder opens a private link, authenticates with a magic link, sees the purpose and privacy
terms, and starts without configuring a workspace or ontology. Setup collects only information
needed for identity, consent, time zone, reminders, and retention.

### Phase B: three-day notebook

The application feels like a private mobile notepad, not a form. Each day presents a blank page and
quiet optional prompts such as “What do customers misunderstand?” or “What would you never want the
Brand to sound like?” Prompts can be ignored.

The founder can type, dictate, record audio, attach a document or image, and save links. Drafts are
saved locally immediately and synchronized when a connection is available. The system does not
interrupt the founder with analysis or corrections during raw capture.

### Phase C: processing

After the capture window, the system preserves the raw material, transcribes audio, extracts
document content, segments sources, and creates candidate mentions, claims, entities,
relationships, tensions, and missing topics. It does not silently accept these as Brand truth.

### Phase D: clarification

The interface changes from notebook to a single focused question at a time. A question exists only
when answering it is expected to materially improve the Brand World. The founder can answer by text
or voice, skip, say “I do not know,” revise an earlier answer, or see which notes caused the
question.

### Phase E: review

The system creates a provisional Brand World containing proposed entities, claims, relationships,
conflicts, uncertainties, missing evidence, and source references. The Testflight expert reviews it
with the founder and records accept, revise, reject, hold, or branch decisions before anything is
promoted into the canonical World.

## 4. End-to-end architecture

```text
[Ionic React PWA]
  notebook | voice | attachments | clarification | progress
          |
          v
[Application API]
  sessions | permissions | phase state | sync | review commands
          |
          +-----------> [PostgreSQL operational store]
          +-----------> [Object/blob storage]
          +-----------> [Local offline cache]
          |
          v
[Ingestion worker]
  transcription | document parsing | segmentation
          |
          v
[Testflight operator runtime]
  extraction | identity | evidence classification | gaps | questions
          |
          v
[Proposal and review layer]
  provisional records | conflicts | derivations | authority decisions
          |
          v
[Existing semantic + Brand World]
  accepted entities | states | assertions | frames | versions | branches
          |
          v
[Context and artifact system]
  exact resolution | profiles | composition | evaluation | rendering
```

Every arrow is a typed handoff. Open-source tools can implement transport and processing, but they
must not become the semantic owner of Brand records.

### The build in simple terms

The product should be built as ten connected modules. These are product responsibilities, not ten
independent services. For the pilot, the API, ingestion workflow, clarification planner and review
commands can run in one Python application plus one background worker.

```text
1. Founder app
      |
2. API and access
      |
3. Capture and storage
      |
4. Ingestion worker
      |
5. Brand interpretation
      |
6. Clarification planner <---- founder answers
      |
7. Provisional World review
      |
8. Canonical Brand World
      |
9. Artifact production
      |
10. Rendering/delivery/learning
```

1. **Founder app:** the mobile notebook, voice recorder, upload surface and clarification screen.
   Build it with React, TypeScript and Ionic as an installable PWA. Dexie protects unsent work and
   Uppy manages uploads.
2. **API and access:** verifies the founder, exposes application commands and prevents the browser
   from calling Testflight internals directly. Build it with FastAPI. Supabase supplies identity;
   the API verifies the issued token and enforces workspace scope.
3. **Capture and storage:** stores exact notes, answer revisions, session state and attachment
   manifests. PostgreSQL stores records; object storage stores files. Supabase provides both
   locally and in the managed EU deployment.
4. **Ingestion worker:** transcribes audio, parses documents and creates traceable content segments.
   Use faster-whisper and Docling through replaceable adapters.
5. **Brand interpretation:** runs the existing Testflight operators to propose claims, entities,
   relationships, conflicts and Brand mappings. This is proprietary Testflight logic.
6. **Clarification planner:** compares the proposals with desired Brand coverage and chooses one
   materially useful question. Its answer returns through capture and is interpreted like any
   other attributed source.
7. **Provisional World review:** shows the expert what was proposed, why, and from which source. The
   expert records accept, revise, reject, hold or branch decisions.
8. **Canonical Brand World:** receives only accepted records. Existing semantic and Brand packages
   own identity, versions, evidence, perspectives, relationships and branches.
9. **Artifact production:** later resolves the exact World records needed for a campaign brief,
   message matrix or social pack, then generates and evaluates a structured proposal.
10. **Rendering, delivery and learning:** later turns approved artifacts into usable files, sends
    them only with authorization, and brings results back as reviewable evidence.

For the paid founder pilot, build modules 1–7 and provide a controlled handoff into module 8.
Modules 9–10 are the next commercial expansion; they should not delay testing the World Seeder.

## 5. Module catalog

### 5.1 Product experience modules

| Module | Necessity | Responsibility | Build or reuse |
| --- | --- | --- | --- |
| Founder onboarding | Required for pilot | Authentication, consent, privacy, reminder and retention settings | Build thin UI; use Supabase Auth |
| Capture notebook | Required for pilot | Low-pressure text entry, optional prompts, autosave and session history | Build custom with Ionic React |
| Voice capture | Required or strongly recommended | Dictation/recording, playback and transcript review | Build UI; browser media APIs, Uppy, transcription adapter |
| Attachment intake | Required for realistic onboarding | Images, PDFs, decks, documents and links | Build thin UI; use Uppy and object storage |
| Capture schedule | Required for the designed experience | Day/session progress and transition into processing | Build a deterministic application state machine |
| Clarification interface | Required for pilot | One question at a time, rationale, source links, answer revision and skip | Build custom; optionally reuse assistant-ui primitives later |
| Founder progress | Required | Shows what is complete without gamifying or pressuring the founder | Build custom |
| Expert review surface | Required for pilot | Inspect, compare, accept, revise, reject, hold and branch proposals | Build custom using existing review lifecycle patterns |
| Artifact studio | Required only after World Seeder | Request, compose, review and approve marketing artifacts | Build later; reuse existing studio patterns |

The notebook and clarification interface should not share a generic chat transcript. Their records,
interaction rules, and user expectations are different.

### 5.2 Application and infrastructure modules

| Module | Necessity | Responsibility | Recommended implementation |
| --- | --- | --- | --- |
| Application API | Required | Stable boundary between UI and domain workflows | Build a small FastAPI composition layer over provider-neutral ports |
| Operational database | Required | Users, sessions, turns, questions, answers, state and jobs | PostgreSQL; Supabase locally and hosted |
| Blob storage | Required | Audio, images, documents and rendered outputs | Supabase Storage behind a `BlobStore` port |
| Authentication | Required for a real pilot | Founder identity, magic links and session control | Supabase Auth behind an `IdentityProvider` port |
| Local offline cache | Required for trustworthy mobile capture | Draft recovery, temporary recordings and upload queue | Dexie/IndexedDB |
| Upload manager | Strongly recommended | Progress, retry, validation and resumable upload | Uppy; enable tus only where needed |
| Background jobs | Required | Transcription, parsing, extraction and World compilation | Start with PostgreSQL job records plus one worker |
| Notifications | Optional in first pilot | Session reminders and processing-complete messages | Email first; web push later |
| Product telemetry | Required for pilot learning | Completion, correction, processing and review metrics | Small first-party event table; no marketing analytics SDK required |
| Audit and operations | Required before multiple paying Brands | Execution receipts, errors, retries, access events and health | Build on existing receipts and structured logs |

### 5.3 Ingestion and intelligence modules

| Module | Necessity | Responsibility | Existing connection / upstream |
| --- | --- | --- | --- |
| Source preservation | Required | Store exact text, transcript spans, speaker, time, rights and attachment identity | Extend `testflight-content` and semantic evidence records |
| Audio transcription | Required when recording is enabled | Convert audio into time-aligned transcript proposals | `faster-whisper` adapter locally; interchangeable hosted adapter |
| Document parsing | Required for attachments | Preserve text, layout, tables, pages and source locations | Docling adapter |
| Content normalization | Required | Convert each source into provider-neutral content units and segments | Extend `testflight-content` |
| Mention and claim extraction | Required | Propose referents, assertions, states and relationship candidates | Existing operator runtime plus new intake operators |
| Evidence classification | Required | Distinguish founder belief, observation, quotation, policy, hypothesis and external evidence | Existing semantic/operator contracts |
| Identity resolution | Required | Prevent different mentions becoming duplicate entities or unrelated entities being merged | Extend semantic identity logic |
| Brand mapping | Required | Map local founder concepts into Brand domain types without forcing ontology changes | Extend `testflight-brand` mapping registry |
| Conflict and gap detection | Required | Find materially inconsistent or incomplete knowledge | New bounded operators |
| Question planning | Required | Select the smallest, highest-value clarification question | New elicitation operator and coverage assessment |
| Review-bundle compiler | Required | Assemble proposals, sources, conflicts and derivations for expert review | New ingestion workflow; reuse Creative Field review pattern |

### 5.4 World and artifact modules

| Module | Pilot | Complete product | Existing connection |
| --- | ---: | ---: | --- |
| Canonical Brand World | Read/manual promotion | Required | `testflight-semantic`, `testflight-brand` |
| World review and promotion | Expert-managed | Required | Generalize Creative Field proposal/acceptance patterns |
| Applicability resolver | Not blocking for intake | Required | Extend world views and context intelligence |
| Creative Field | Optional input | Required for expressive artifacts | Existing `testflight-creative-field` |
| Artifact profile registry | Not required | Required | New `testflight-artifacts` and marketing profiles |
| Artifact context compiler | Not required | Required | Compose resolved World view and Creative Field projection |
| Artifact composers | Not required | Required per artifact type | New versioned creation operators |
| Artifact evaluators | Not required | Required | Extend existing evaluation patterns |
| Artifact review/versioning | Not required | Required | New generic artifact lifecycle |
| Renderers | Optional review export | Required for deliverables | Provider-specific adapters |
| Delivery adapters | Out of scope | Optional/authorized | Provider-specific adapters only |
| Outcomes and learning | Out of scope | Later | Extend semantic learning records |

## 6. Open-source software allocation

### Ionic React: application shell

Use [Ionic React](https://ionicframework.com/react) for mobile-safe pages, inputs, navigation,
modals, sheets, recording controls, loading states, accessibility behavior, and safe-area handling.
Style it as a quiet Testflight notebook rather than accepting the default component aesthetic.

Use it in:

- founder onboarding;
- notebook and daily progress;
- recording and upload controls;
- clarification question cards;
- expert review navigation.

Build as an installable PWA. Add [Capacitor](https://capacitorjs.com/docs) only when App Store
distribution or native-only capabilities justify it. Domain and API code must not depend on
Capacitor.

### FastAPI: application API composition layer

Use [FastAPI](https://fastapi.tiangolo.com/features/) for the authenticated HTTP API. It matches the
existing Python domain packages, validates request and response contracts through Pydantic, emits
OpenAPI documentation, and supports dependency injection for swapping local and hosted adapters.

FastAPI belongs in `apps/brand-intake-api`; it is not a domain package. Endpoint handlers should
authenticate, validate, call one application command and translate its typed outcome into HTTP.
They must not contain extraction prompts, ontology mapping rules or direct provider SDK logic.

The frontend may use Supabase directly only for authentication bootstrap and signed upload flows.
All semantic commands, review actions and job creation go through the API.

### Supabase: portable application infrastructure

Use [Supabase](https://supabase.com/docs/guides/getting-started/architecture) for PostgreSQL,
authentication, storage, migrations, and local development. Run the Supabase local stack through
its CLI/Docker during development and point the same application at a managed EU-region project for
the paid pilot.

Supabase is an implementation of explicit ports:

```text
IdentityProvider
OperationalRecordStore
BlobStore
SignedUploadService
```

Core domain packages must not import Supabase SDKs. Supabase-specific code belongs in adapters.
Database migrations remain ordinary version-controlled SQL wherever practical. Storage rows retain
provider-neutral object IDs, checksums and logical locations so blobs can be exported and imported.

Do not self-host Supabase for production merely to preserve portability. Its
[self-hosting guidance](https://supabase.com/docs/guides/self-hosting) assigns backup, security,
availability, monitoring and scaling to the operator. Managed EU hosting is the lower-risk pilot
choice.

### Dexie: resilient local drafts

Use [Dexie](https://dexie.org/docs/Dexie.js) as a small IndexedDB layer for unsynchronized text,
temporary recordings, queued mutations and upload state. Each local item receives its final UUID
before synchronization so retries remain idempotent.

Dexie is a cache and outbox, not canonical storage. The application shows synchronization state,
retries safely, and keeps server acknowledgements. Browser storage can be evicted, so confirmed
server synchronization remains the durability boundary.

### Uppy: uploads

Use [Uppy](https://uppy.io/docs/) for file selection, validation, progress, retry, cancellation and
mobile upload recovery. Begin with its core components and the smallest adapter needed for signed
Supabase uploads. Add the [tus protocol](https://tus.io/) only for large or interruption-sensitive
audio and document uploads. Add Uppy Companion only if third-party Drive/Dropbox imports become a
validated need.

Uppy owns upload transport state. It does not own attachment identity, evidence metadata, rights,
or source records.

### Docling: document-ingestion adapter

Use [Docling](https://docling.ai/) in a Python worker for PDF, Office, HTML, image/OCR and structured
document extraction. Convert its result into Testflight `ContentUnit` and segment contracts while
preserving page, table, image and source-location references.

Docling output is derived content. The original file, checksum, extraction configuration and
processing receipt must remain available. Docling does not classify Brand truth or mutate the
ontology.

### faster-whisper: optional local transcription

Use [faster-whisper](https://github.com/SYSTRAN/faster-whisper) behind a `TranscriptionProvider`
port when local or private transcription is valuable. It is appropriate for the local server and
can also run in an EU worker environment.

For the earliest pilot, a hosted EU-compatible transcription provider may reduce deployment work.
Both implementations must return the same provider-neutral transcript, time spans, language,
confidence metadata, model/configuration receipt, and failure disposition.

### assistant-ui: optional clarification primitives

[assistant-ui](https://www.assistant-ui.com/docs) can later supply accessible composer, attachment,
voice and conversational UI primitives. It should not own the interview workflow or canonical
records. The MVP clarification flow is simpler as custom `QuestionCard`, `AnswerComposer`, and
`AnswerHistory` components over first-class Testflight records.

Adopt assistant-ui only if testing shows that clarification becomes a genuinely threaded
conversation requiring streaming, tool displays, or richer message handling.

### Trigger.dev: later job orchestration

[Trigger.dev](https://trigger.dev/docs/introduction) is an open-source, Apache-2.0 background-job
framework with queues, retries, schedules and monitoring. Do not add it for the one-founder pilot.
Its self-hosted platform adds PostgreSQL, Redis, worker and operational responsibilities, and its
[documentation](https://trigger.dev/docs/self-hosting/overview) explicitly assigns reliability and
security to the operator.

Begin with a `processing_job` table, leases, attempt counts, idempotency keys, receipts, and one
worker. Move to Trigger.dev or another durable runner only when concurrency, long waits,
cancellation, scheduling or operational visibility exceed the simple worker's limits.

## 7. Portability and deployment profiles

### Portability rule

Portability does not mean hiding PostgreSQL behind a universal lowest-common-denominator repository.
It means keeping domain semantics independent from hosting products and defining ports at genuine
external boundaries.

```text
domain packages
  -> application ports
      -> local/Supabase adapters
      -> hosted/Supabase adapters
      -> later alternative adapters if required
```

The local and hosted Supabase profiles implement the same interfaces, migrations, bucket rules,
record identifiers, and object manifests. Configuration selects an adapter; it does not change
domain records.

### Local development profile

```text
Ionic PWA on developer machine
Supabase CLI local stack in Docker
local PostgreSQL/Auth/Storage
Python ingestion and Testflight workers
Docling locally
faster-whisper locally when enabled
existing local operator/model adapters
```

This profile supports development and private testing on the local server. It should not be
mistaken for a production-ready self-hosted service.

### Managed EU pilot profile

```text
static/PWA frontend hosted in EU or at an approved edge provider
managed Supabase project in a selected EU region
EU-hosted application API and Python worker
EU-resident object storage and backups
approved model/transcription providers or self-hosted EU workers
centralized secrets, monitoring and error reporting
```

Before accepting client data, verify the actual region, backup location, subprocessors, model-use
policy, retention, deletion behavior and DPA for every provider. “EU database” alone does not prove
that every processing path remains in the EU.

### Migration path

1. Apply the same versioned SQL migrations to the hosted project.
2. Export and import operational rows while preserving UUIDs and timestamps.
3. Copy blobs using their logical object manifests and verify checksums.
4. Switch environment-specific adapter configuration and secrets.
5. Replay dependency-free health probes.
6. Verify record counts, blob hashes, permissions, job state and sample derivations.
7. Run a read-only acceptance test before directing new writes to the hosted profile.

No migration should require rewriting Brand World or evidence identifiers.

## 8. Core records and handoffs

The minimum first-class records are:

- `FounderWorkspace`
- `IntakeSession`
- `NotebookEntry` and immutable `NotebookEntryRevision`
- `Attachment`, `VoiceNote`, `Transcript`, and `ProcessingReceipt`
- `SourceEnvelope`, `ContentUnit`, and evidence spans
- `CoverageAssessment`
- `ClarificationQuestion` with selection rationale and dependencies
- `ClarificationAnswer` and immutable answer revisions
- entity, assertion, state, relationship and mapping proposals
- `Conflict`, `KnowledgeGap`, and `OntologyExtensionProposal`
- `ReviewBundle` and authority-bearing `ReviewDecision`
- `WorldDeltaProposal`
- `JobRecord` and execution receipt

Important boundaries:

```text
notebook entry != extracted claim
mention != entity
founder statement != verified fact
model confidence != truth
proposal != accepted World record
answer revision != destructive overwrite
local vocabulary != shared ontology change
processing retry != duplicate semantic mutation
```

## 9. State, error and recovery model

The product workflow is a deterministic state machine:

```text
SETUP
  -> CAPTURE_DAY_1
  -> CAPTURE_DAY_2
  -> CAPTURE_DAY_3
  -> PROCESSING
  -> CLARIFICATION
  -> REVIEW_READY
  -> FOUNDER_REVIEWED
  -> EXPERT_INTEGRATION
```

Transitions are recorded commands, not inferred from the last screen visited. Administrative
overrides require an actor, reason and audit record.

Failure behavior:

- network loss: keep local outbox and synchronize idempotently;
- upload interruption: resume or retry without creating a second attachment;
- transcription/parser failure: retain the original source and expose retry or manual handling;
- partial extraction: persist valid proposals and explicit failures separately;
- ambiguous referent: preserve candidates and ask only when material;
- contradictory statements: preserve both and create a clarification or decision requirement;
- unavailable model: leave the job retryable; never fabricate completion;
- invalid proposal: hold it outside the canonical World;
- provider migration: retain stable IDs, checksums, receipts and revision history.

## 10. Build sequence

### Exact initial package layout

```text
apps/
  brand-intake-web/               # React + TypeScript + Ionic PWA
  brand-intake-api/               # FastAPI composition root and HTTP contracts

packages/
  testflight-ingestion/           # intake records, state machine and workflows
  testflight-content/             # existing source/content contracts
  testflight-semantic/            # existing canonical semantic records
  testflight-brand/               # existing Brand ontology and validation
  testflight-operator-runtime/     # existing operator execution

adapters/
  supabase-intake/                # auth verification, PostgreSQL and blob implementations
  docling-ingestion/              # document parser implementation
  faster-whisper/                 # local transcription implementation

workers/
  brand-intake-worker/            # job leasing and processing composition root

supabase/
  config.toml                     # reproducible local stack configuration
  migrations/                     # operational schema, policies and buckets
  seed.sql                        # non-sensitive development fixtures
```

`testflight-ingestion` is the important new domain package. It owns intake sessions, notebook entry
revisions, clarification records, coverage assessments, processing jobs, proposal bundles and the
workflow state machine. It reuses Content and Semantic types rather than redefining evidence,
entities, assertions, branches or accepted World records.

`brand-intake-api` and `brand-intake-worker` are composition roots: they assemble ports and adapters
for one runtime. They do not own domain meaning. This permits the same ingestion workflows to run
against local Supabase or managed EU Supabase by changing validated runtime configuration.

### Slice 0: contracts and portability

Define intake records, application ports, state transitions, job semantics, migration rules and
provider-neutral transcription/document outputs. Add every upstream to `upstreams/registry.yaml`
before importing it. Each adapter receives a descriptor, dependency-free health probe,
documentation and tests.

**Gate:** the same fixture can run through local and hosted-profile adapters without changing
domain output.

### Slice 1: trustworthy notebook

Build authentication, onboarding, Ionic notebook UI, Dexie outbox, Supabase persistence, autosave,
session progress, uploads, and exact source preservation.

**Gate:** no typed character or completed recording is lost across refresh, network loss, duplicate
submission or upload retry.

### Slice 2: ingestion pipeline

Add document parsing, transcription, normalized content units, processing jobs and receipts.

**Gate:** every extracted span resolves to the original file/entry and processing configuration;
partial failures remain inspectable.

### Slice 3: proposals and clarification

Add bounded extraction, identity hypotheses, Brand mapping, coverage assessment, contradiction/gap
detection, question selection and the one-question interface.

**Gate:** questions cite their triggering evidence and materiality; the system can return `no_hit`,
`partial`, `branch`, `ask`, or `hold` without inventing knowledge.

### Slice 4: expert review and pilot

Build the provisional World review surface, review decisions, export, telemetry and manual
integration handoff. Run first with an internal Brand fixture, then one founder.

**Gate:** every proposed World record is traceable to source evidence, derivation and review state;
no proposal enters the canonical World automatically.

### Slice 5: artifact application

After the World Seeder proves useful, build Campaign Brief, Message Matrix and Social Campaign Pack
profiles, exact context compilation, evaluation, approval and renderers as described in the Brand
Artifact System plan.

## 11. Testing and product proof

### Engineering tests

- local/hosted adapter contract tests;
- offline outbox and synchronization tests;
- duplicate event, retry and idempotency tests;
- storage checksum and migration tests;
- source-to-transcript/document-segment traceability;
- operator schema, evidence and uncertainty tests;
- identity, version, branch and review lifecycle tests;
- workspace isolation, access and deletion tests;
- mobile browser and installed-PWA interaction tests.

### Pilot success measures

- founder completes the capture period without assistance or data loss;
- time and cognitive effort required per session;
- proportion of important founder concepts represented in the provisional World;
- proposal acceptance, correction, rejection and unresolved rates;
- number and usefulness of clarification questions;
- source coverage for material records;
- expert time needed to review and integrate the World;
- founder agreement that the result represents the Brand;
- whether the World materially improves a later campaign brief or comparable artifact;
- willingness to pay for a repeatable engagement.

The primary early proof is not extraction volume. It is whether the reviewed Brand World reduces
briefing effort and produces a visibly better, more defensible marketing artifact.

## 12. Architectural decisions

1. **PWA before native application.** Ionic supplies mobile behavior; Capacitor remains an escape
   hatch rather than an initial dependency.
2. **Focused clarification before general chat.** Questions and answers are domain records, not
   generic messages.
3. **Managed EU production, local development.** Both run the same migrations and ports; production
   operations are not placed on the local prototype stack.
4. **Provider-neutral semantic core.** Supabase, Docling, Whisper, Uppy and model SDKs remain inside
   adapters or the UI layer.
5. **Original evidence is immutable.** Derived transcripts and interpretations are versioned and
   reproducible.
6. **Proposal-only intelligence.** The system can structure and challenge founder knowledge, but
   expert/client authority promotes it.
7. **Simple worker before workflow platform.** Add operational infrastructure only when observed
   load and failure modes justify it.
8. **World before artifact automation.** Production deliverables are the eventual commercial
   surface, but their reliability depends on a reviewed and correctly resolved World.

## 13. Existing Testflight fit

This product extends rather than replaces the current architecture:

- `testflight-content` owns provider-neutral sources and content units;
- `testflight-semantic` owns evidence links, entities, assertions, states, frames, perspectives,
  decisions, branches and World views;
- `testflight-brand` supplies Brand domain modules and validation;
- `testflight-operator-runtime` executes versioned provider-neutral reasoning contracts;
- `testflight-context-intelligence` compiles bounded context after deterministic applicability
  selection;
- `testflight-creative-field` supplies reviewed creative direction to later artifacts;
- SQLite/blob persistence remains useful for fixtures and isolated tests;
- Cognee remains a rebuildable retrieval/graph projection behind its adapter, never canonical
  storage;
- LangGraph remains an optional stateful orchestration implementation and is not required for the
  deterministic founder experience state machine.

The genuinely new product center is `testflight-ingestion` plus `apps/brand-intake`. The later
commercial artifact layer adds `testflight-artifacts`, marketing artifact profiles, renderers and
delivery adapters. The proprietary value remains in the semantic contracts and operators connecting
these surfaces—not in recreating commodity authentication, storage, uploads or parsers.

## 14. Reasoning and evaluator record

This design applies the following Testflight operators at architecture depth:

- `boundary-conflation@1`: pass; capture, evidence, proposal, acceptance, artifact and external
  action have distinct owners and handoffs.
- `ontology-conflation@1`: pass; customer population and shared Brand ontology evolution remain
  separate.
- `local-global-conflation@1`: pass; founder-local vocabulary is not promoted globally by default.
- `configuration-runtime@1`: partial; ports and profiles are defined, but each local and EU runtime
  capability still requires a health probe and deployment verification.
- `evaluation-schema@1`: partial; engineering gates and pilot measures are defined, but gold
  interview fixtures and acceptance thresholds must be authored during implementation.
- `identity-provenance-conflation@1`: pass in design; stable record IDs, evidence anchors,
  derivations and review authority survive provider changes.
- `version-state-conflation@1`: pass in design; entry, answer, transcript and World revisions are
  immutable and distinct from workflow phase and contextual applicability.
- `retry-idempotency@1`: pass in design; client-generated IDs, job keys, leases and receipts prevent
  transport retries from duplicating semantic mutations.
