# Build Plan

## Recommended topology

```text
packages/
  testflight-semantic/               # existing canonical World kernel
  testflight-brand/                  # existing Brand ontology and validation
  testflight-content/                # existing provider-neutral source/content contracts
  testflight-context-intelligence/   # extend structured applicability resolution
  testflight-creative-field/         # existing creative direction lifecycle
  testflight-operator-runtime/       # existing provider-neutral operator execution
  testflight-ingestion/              # new intake sessions and proposal workflows
  testflight-artifacts/              # new generic artifact contracts and lifecycle
  testflight-marketing-artifacts/    # new marketing profiles, composers, evaluators

domains/
  marketing-artifacts/
    profiles/
    mapping-policies/
    evaluation-policies/

adapters/
  document-ingestion/
  artifact-renderers/
  delivery-connectors/
  analytics-connectors/

apps/
  brand-intake/                       # guided interviews and World review
  campaign-studio/                    # request, compose, review, render, deliver
```

Do not add external runtime dependencies until `upstreams/registry.yaml` is updated. Every new
adapter needs a descriptor, dependency-free health probe, documentation, and tests.

## Phase 0 — Contract alignment

Define the minimum records and ports before adding UI or providers:

- `IntakeSession`, `IntakeTurn`, and `CoverageAssessment`;
- exact revision/lineage and bitemporal rules for versioned World records;
- structured World/artifact selectors;
- `ArtifactProfileRevision`, `ArtifactContextManifest`, `ArtifactProposal`, and `ArtifactVersion`;
- dependency invalidation and stale-state semantics;
- renderer, delivery, and outcome ports.

**Gate:** every field has one semantic owner; no duplicate Creative Field, context, or persistence
lifecycle is introduced.

## Phase 1 — World Seeder

Build text/note intake, guided questions, exact evidence capture, extraction proposals, identity
resolution, Brand mapping, contradiction/gap analysis, and human review. Use synthetic and one
owner-provided Brand fixture before external collaboration tools.

**Gate:** two participants can disagree without forced consensus; every accepted record resolves
to a source turn and review decision; ontology gaps remain local or proposed.

## Phase 2 — Exact context and campaign brief

Extend the World-view request with structured selectors and exact revision manifests. Implement
the Campaign Brief profile, context-slot mapping, creation operator, evaluator, approval lifecycle,
and Markdown/PDF renderer.

**Gate:** the same request and recorded-time cutoff reproduce the same context and brief, or report
explicit divergence; changing an audience or product revision marks the brief stale.

## Phase 3 — Message matrix and social pack

Add parent/child artifact dependencies, Message Matrix and Social Campaign Pack profiles, Creative
Field projection, a production image/text target, post-render evaluation, and bundle export.

**Gate:** campaign intent and exact entity revisions survive brief -> messages -> variants;
unaffected accepted content survives revision.

## Phase 4 — Delivery and outcomes

Add one document destination and one operational marketing destination, publication receipts,
measurement import, identity reconciliation, observed outcomes, and reviewable learning.

**Gate:** retries do not duplicate delivery; metrics link to exact published artifact versions;
correlation does not become causal learning.

## Phase 5 — Enterprise hardening

- tenant and workspace isolation;
- SSO/OIDC, SCIM, RBAC, source-permission synchronization;
- audit export, encryption, retention/deletion, backup and disaster recovery;
- data residency, DPA, subprocessors, model-use and zero-retention controls;
- prompt-injection and untrusted-content isolation;
- job queues, cancellation, observability, budgets, SLA and support;
- security testing and certification roadmap.

## Test architecture

### Deterministic tests

- record validation, immutability, identity, scope, time, precedence, branch overlays;
- exact context resolution and dependency invalidation;
- profile validation and artifact lifecycle;
- renderer/adapters with fake providers;
- idempotent delivery and outcome identity.

### Generative operator tests

- golden source-to-proposal fixtures;
- minimum-question behavior and information sufficiency;
- schema adherence, evidence coverage, unsupported-claim rejection;
- revision preservation and explicit omissions;
- known ambiguity, contradiction, no-hit, partial, branch, ask, and hold cases.

### Semantic continuity tests

```text
intake -> World proposal -> accepted World
World revisions -> artifact context -> campaign brief
brief -> message matrix -> asset variants
artifact version -> render -> publication receipt
measurement -> outcome -> learning proposal -> later context
```

Each test must verify that entity identity, exact revision, scope, time, branch, evidence, authority,
rights, and uncertainty survive every handoff.

## First pilot definition

Limit the first implementation to:

- one Brand workspace;
- 3-5 interview participants;
- text, notes, and a bounded document set;
- one campaign relationship frame;
- one product/offering and up to two audience segments;
- Campaign Brief, Message Matrix, and Social Campaign Pack;
- human approval at World and artifact promotion boundaries;
- local/private runtime with one document and one creative renderer;
- no autonomous publishing.

Measure onboarding time, proposal correction rate, evidence coverage, time to approved brief,
review cycles, repeated questions, and participant acceptance. Expansion should follow observed
workflow value, not schema breadth.

## Reasoning and evaluator record

This architecture applies:

- `boundary-conflation@1`: pass; evidence, meaning, proposal, acceptance, rendering, and action have
  explicit handoffs.
- `ontology-conflation@1`: pass; population, local vocabulary, and shared ontology extension remain
  separate.
- `mention-entity-conflation@1`: pass; raw mentions require conservative identity resolution.
- `evidence-truth-conflation@1`: pass; employee statements remain attributed claims.
- `version-state-conflation@1`: partial; the existing system needs stronger lineage, recorded-time
  selection, frozen revision manifests, and dependency invalidation.
- `local-global-conflation@1`: pass; customer-local vocabulary and Brand state are not promoted
  globally by default.
- `configuration-runtime@1`: pass in the design; live provider capability still requires runtime
  verification.
- `evaluation-schema@1`: partial; artifact-specific evaluators and end-to-end fixtures must be built.

