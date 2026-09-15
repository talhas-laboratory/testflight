# Brand World v3 modular migration design

Date: 2026-09-14  
Status: phases 0–6 implemented and certified; v3 remains candidate until human review and cutover gates pass  
Target: Testflight Product architecture and product-definition review  
Selected approach: evolutionary replacement with isolated read-only legacy access

## Implementation record

The plan was authorized for implementation on 2026-09-14. Phases 0–6 are now implemented: the
decision and vocabulary boundary; typed World records; eight candidate Brand modules and separate
navigation projection; deterministic legacy inventory and disposition ledger; provider-neutral
World proposal, review, approval, rejection, supersession, merge, query, diff, dependency, and
history services; transactional SQLite persistence; a deterministic 56-record Biotic public-
research migration and authority-review package; and Context Compiler v2 with strict v3 wire
decoding, bounded traversal, sufficiency evaluation, citations, trace, and replay.

`make brand-world-v3-certification` proves the implemented foundation against the actual exported
Biotic branch. `make check` passes for the complete repository. This is not a cutover: no Biotic
record has been silently approved, the `client-approved-v3` branch awaits an authorized human
record review, and phases 7–12 remain later product work.

## 1. Outcome

Replace the current Brand ontology organization with a modular Brand World grammar that can model a
company's reality, meaning, decisions, manifestations, and evolution; compile the correct world
slice for a specialist agent; and support one complete human-governed decision and artifact loop.

The replacement must preserve useful infrastructure, evidence, stable identities, and history while
ensuring that v1/v2 types, projections, and assumptions cannot influence new writes or reasoning.

At completion:

- Brand World v3 is the only writable canonical Brand model.
- Old Brand World data remains available through an isolated, explicitly legacy, read-only route.
- Active applications, agents, workflows, packages, projections, and documentation use v3 only.
- The eight-system map is a rebuildable navigation projection, not the ontology.
- A Biotic Brand World can be constructed, reviewed, approved, compiled for a newsletter task,
  transformed into a reviewable artifact, and updated from outcome evidence.
- A second brand can use the same grammar, runtime, routes, agents, and application without code
  changes to the shared platform.

## 2. Locked design decisions

These decisions define the plan. Changing one requires an explicit proposal before implementation
continues.

1. **Evolutionary replacement, not in-place mutation or greenfield rewrite.** New canonical modules
   are built beside the current implementation and promoted only after semantic and behavioral
   parity gates pass.
2. **Single-write architecture.** During migration, v3 is the only destination for new accepted
   Brand knowledge. There is no v1/v2 dual-write period.
3. **Legacy means read-only.** Existing v1/v2 data, source records, and migration receipts remain
   readable. Legacy schemas and projection code are removed from the active dependency graph.
4. **Universal grammar, brand-specific population.** Shared semantic and Brand-domain contracts do
   not contain Biotic facts. A Brand workspace may add extensions through a governed extension
   contract.
5. **Human sovereignty.** Agents may observe, interpret, propose, compare, generate, and evaluate.
   Only an authorized human decision can promote identity, principle, policy, or other normative
   Brand meaning.
6. **Approval does not erase epistemic type.** An approved belief remains a belief; an approved
   hypothesis remains a hypothesis; an approved public claim is not automatically external truth.
7. **Canonical records are typed.** Entity, State, Event, Relation, Context, Claim, Evidence,
   Decision, Task, Artifact, and Outcome are not stored as variants of one generic record.
8. **Projections never own meaning.** UI maps, search indexes, Cognee datasets, dossiers, feeds, and
   agent packets are reproducible projections over canonical records.
9. **Routes are first-class.** A ContextPacket is one compiled result; the RouteDefinition and its
   evaluation history are durable, inspectable objects.
10. **Biotic newsletter is the golden vertical.** It proves the new Brand World through one complete
    loop before simulation, broad integrations, or additional manifestation domains are added.
11. **One active product shell.** Brand construction, world exploration, specialist work, evidence,
    approvals, and history become modules of one application. Runtime services remain backstage.
12. **No silent migration.** Every legacy object ends as migrated, intentionally archived,
    quarantined, or rejected with a reason and receipt.

## 3. Approaches considered

### A. Patch the current ontology in place

Advantages: least initial code movement; existing applications continue to run.  
Rejected because: mixed semantic levels, generic dossiers, v1/v2 duality, and projection assumptions
would remain embedded in active paths. It cannot meet the no-active-legacy requirement reliably.

### B. Greenfield rewrite

Advantages: visually clean architecture and unrestricted naming.  
Rejected because: it would discard tested evidence, authority, context, branching, dependency,
workflow, operator, and adapter contracts. Recreating these foundations would add risk without
improving the product thesis.

### C. Evolutionary replacement — selected

Build v3 behind new package seams, migrate Biotic with a deterministic ledger, prove the complete
loop, switch all active consumers, then isolate old data under a legacy reader. This has the highest
up-front migration discipline but gives both semantic cleanliness and behavioral safety.

## 4. Architectural invariants

Every implementation and migration pull request must preserve these invariants:

- Evidence is not a claim, and a claim is not an entity.
- An interpretation never rewrites its source observation.
- A State has bounded applicability and is not an Entity identity.
- An Event records occurrence; it is not a top-level subject area.
- A Relation has typed participant roles, context, time, and provenance.
- A Decision records authorized commitment; it does not retroactively prove its rationale.
- A Task or workflow run is operational state, not Brand truth.
- Visibility does not imply permission; permission does not imply approval.
- Model output is proposal-only until an owning domain validates and an authorized actor promotes it.
- Accepted meaning, runtime state, analytical measurements, and UI projections remain separate.
- No active module imports a legacy schema, reader, fixture, or projection.
- Every context compilation can be reproduced from exact versions and recorded inputs.
- Every accepted Brand change has an actor, authority, rationale, effective time, derivation, and
  affected dependency assessment.

## 5. Target semantic architecture

### 5.1 Constitutional World grammar

This is the smallest shared grammar. It belongs in `testflight-semantic` and must not import Brand,
application, database, provider, or UI code.

| Primitive | Meaning | Required behavior |
| --- | --- | --- |
| Entity | A referent with identity continuity | Versioned identity; may have many states, claims, names, and contexts |
| State | A bounded condition of one or more entities | Valid time, known time, context, status, derivation |
| Event | A bounded occurrence that can change state | Participants, event type, time, context, evidence |
| Relation | A typed connection with named roles | Subject/object or participant roles, context, validity, provenance |
| Context | Applicability frame | Brand, offering, audience, market, channel, locale, situation, time, dimensions |
| Claim | A proposition about the world | Claim kind, epistemic status, perspective, evidence roles, authority, conflicts |
| Source | An origin that can be revisited | Identity, ownership, capture method, content policy, rights, timestamps |
| Evidence | A bounded source span or measurement | Exact source locus, support/opposition role, limitations, integrity hash |
| Derivation | How one record was produced from others | Operator and version, input refs, output refs, evaluator results |
| AuthorityGrant | Who may do what under which scope | Actor, capability, resources, valid time, constraints |
| Version/Branch | Evolution without destructive overwrite | Parent refs, delta, status, conflict and merge assessment |
| Dependency | Why an upstream change may affect a downstream object | Rule, context overlap, effect, freshness status, review outcome |

`Interpretation`, `Observation`, `Hypothesis`, `Proposal`, and factual or normative assertions are
typed Claim profiles rather than untyped text fields. `Decision` remains a first-class governed
record because it carries choice, alternatives, authority, and resulting state transition.

### 5.2 Brand-domain modules

The canonical Brand ontology is composed of independently versioned modules. Modules can depend only
on the constitutional kernel and explicitly declared Brand modules.

| Module | Owns | Does not own |
| --- | --- | --- |
| `identity` | purpose, beliefs, principles, values, ambitions, tensions, invariants, identity continuity | products, visual assets, audience evidence |
| `organizational-reality` | organization, people/roles, capabilities, practices, technology, resources, operating choices | external perception, campaigns |
| `offering` | products, services, capabilities, benefits, value propositions, proof obligations | customer observations, creative executions |
| `relationships` | customers, audiences, employees, partners, communities, needs, relationship roles | generalized market conditions |
| `environment` | category, market, competition, culture, regulation, social conditions | internal strategy presented as external fact |
| `expression-manifestation` | verbal, visual, symbolic, behavioral, interactive, spatial, event, and artifact expression | company belief itself |
| `governance-decisions` | policies, constraints, decision rights, approvals, strategic decisions, claim permissions | runtime authentication implementation |
| `evolution-learning` | historical eras, changes, experiments, observed outcomes, learning updates, freshness | automatic mutation from performance |

`Experience` and `Perception` are no longer catch-all entity bins:

- Experience is a relationship frame among an actor, touchpoint, offering/expression, event, outcome,
  and context.
- Perception is a scoped observation, association, evaluation, or interpretation held by a named
  perspective about another object.

The familiar eight-system map may still expose Identity, Expression, Offering, Experience,
Perception, Governance, Environment, and Event, but its assignments are declared projection rules.

### 5.3 Intelligence and action grammar

The world stores meaning. The Work and Intelligence planes store what agents and humans are doing
with it.

| Object | Owner | Purpose |
| --- | --- | --- |
| AgentDefinition | agent package | Versioned identity, role, responsibilities, tools, scopes, cognition, validators, escalation |
| OperatorDefinition | operator runtime | One reusable reasoning or transformation procedure |
| Task | Work Ledger | Objective, requester, assignee, status, dependencies, expected result, context refs |
| Result/Artifact | Work Ledger/domain package | Durable produced object with lineage, assumptions, uncertainty, and review state |
| Road | Brand World | Persistent semantic Relation or Dependency available for traversal |
| RouteDefinition | context package | Task-specific traversal and selection policy |
| RouteEvaluation | context package | Whether a route supplied sufficient, current, authorized context at acceptable cost |
| Gate | governance/work packages | Evidence, authority, privacy, risk, approval, or quality passage rule |
| ContextPacket | context package | Immutable result of one route execution |
| ContextRunTrace | context package | Exact inputs, selections, exclusions, expansions, omissions, and stop reason |
| Transformation | manifestation package | Meaning-preserving translation from principles and context into instructions or artifacts |
| Outcome/Learning | semantic and Brand packages | Observed consequence and reviewed interpretation; never automatic causality |

The ideal primitive language maps cleanly: Receivers, Interpreters, Transformers, and Externalizers
are capabilities performed by actors, agents, operators, or tools; Roads are Relations and
Dependencies; Routes are compiled traversals; Gates are governed passage policies; Containers are
bounded entities, contexts, workspaces, or compositions rather than one universal storage class.

## 6. Canonical record contracts

### 6.1 Shared envelope

All canonical records carry only shared lifecycle and lineage fields:

```text
id
type_id
schema_version
record_version
workspace_id
module_id
branch_id
lifecycle_status
valid_time
known_time
context_refs
provenance_refs
derivation_ref
authority_ref
created_at
created_by
supersedes_ref
```

Kind-specific payloads remain separate schemas. There is no universal `meaning`, `summary`,
`assertion`, or arbitrary `metadata` payload that allows semantic distinctions to be bypassed.

### 6.2 Agent-readable dossiers

Dossiers are projections selected by semantic kind:

- **Entity dossier:** identity, definitions, active states, typed relations, claims, history,
  dependencies, conflicts, evidence map.
- **Claim dossier:** exact proposition, claim kind, epistemic status, perspective, applicability,
  supporting/opposing evidence, interpretations, conflicts, authority, permitted manifestations.
- **State dossier:** described subjects, value, context, validity, knowledge time, supporting claims,
  prior/next states.
- **Event dossier:** event type, participants/roles, occurrence time, evidence, caused-state-change
  proposals, consequences, uncertainty.
- **Relation dossier:** participant roles, relationship meaning, scope, validity, evidence,
  dependencies, competing frames.
- **Decision dossier:** question, alternatives, selected option, rationale, evidence considered,
  decision maker, authority, effective scope, consequences, supersession.
- **Source/evidence dossier:** original retained content or live reference, exact locus, rights,
  capture integrity, limitations, derived records.
- **Artifact dossier:** purpose, composition, element responsibilities, governing policies, compiled
  contexts, representation dependencies, reviews, versions, outcomes, freshness.

The previous assertion/interpretation/permitted-use/scope/constraints/unknowns/source presentation
is preserved inside the relevant dossiers. It is no longer imposed on every kind.

## 7. Target module and package ownership

Names are proposed; semantic ownership is mandatory even if a package name changes during review.

### 7.1 Existing packages retained and refactored

- `packages/testflight-semantic`
  - Owns the constitutional World grammar, evidence, time, context, authority, provenance, branch,
    dependency, decision, and learning primitives.
  - Removes Brand-specific or UI-specific assumptions.
- `packages/testflight-brand`
  - Owns Brand module composition, extension validation, Brand policies, and typed Brand records.
  - Consumes `testflight-semantic`; never imports storage or provider adapters.
- `packages/testflight-content`
  - Owns immutable source content normalization and occurrences before Brand interpretation.
- `packages/testflight-context-intelligence`
  - Becomes Context Compiler v2 and owns RouteDefinition, RouteEvaluation, ContextRequest,
    ContextPacket, ContextRunTrace, sufficiency, and progressive expansion.
- `packages/testflight-operator-runtime`
  - Continues to execute versioned operators and emit receipts; it does not own agents or Brand truth.
- `packages/testflight-workflows`
  - Continues to schedule declared computation; workflows link to Tasks but do not replace them.
- `packages/testflight-design-language`
  - Remains the shared UI contract.

### 7.2 New packages

- `packages/testflight-world`
  - Provider-neutral application service for Brand World reads, proposals, approvals, rejection,
    history, dependency assessment, and projection events.
- `packages/testflight-work`
  - Generic append-oriented Work Ledger: Task, Result, Artifact reference, WorkEvent, Dependency,
    Review, Discussion reference, Status transition, retry/cancel/resume, and idempotency.
- `packages/testflight-agents`
  - AgentDefinition, roster, operator composition, tool/resource policies, escalation and stopping
    rules, presentation profile, and agent evaluation cases.
- `packages/testflight-manifestation`
  - ManifestationPolicy, inheritance/representation modes, TransformationRequest/Package,
    ArtifactCompositionGraph, element responsibilities, composition evaluation, and freshness.

### 7.3 Adapters

- `adapters/sqlite-semantic` implements v3 World repositories for local development.
- Add `adapters/sqlite-work` for the Work Ledger or explicitly extend the existing workflow store
  behind separate tables and repository interfaces; the preferred choice is a separate adapter.
- `adapters/cognee` projects accepted v3 records only and contains no canonical write operation.
- `adapters/langgraph` schedules workflows only.
- `adapters/mcp-workflows` exposes authorized workflows and task operations without widening grants.
- `adapters/creative-connectors` remains the authority-gated externalization boundary.
- Production Postgres, OAuth, analytical, and source connectors are postponed until the golden loop
  demonstrates a measured need; their provider-specific code must remain adapters.

### 7.4 Applications

- Add `apps/testflight-web` as the only active human product shell.
- Add or extend a backend composition root, provisionally `apps/testflight-api`, that composes World,
  Work, Context, Agent, workflow, and manifestation services behind authenticated APIs.
- Existing Brand Intake, Brand World, and Creative Studio interactions are migrated as feature
  modules inside the product shell.
- Workflow Runtime and Operator Runtime remain separate backstage services.
- Brand Lab becomes a developer/diagnostic tool or is retired after its diagnostics are available in
  maintained developer tooling.
- Legacy data is available only through `legacy/brand-world-reader`; no active app imports it.

## 8. Brand extension model

A brand workspace can extend the shared ontology only through a versioned extension manifest:

```text
extension_id
brand_workspace_id
base_ontology_version
owning_module
new_type_or_relation_definitions
competency_questions
examples_and_counterexamples
source_and_derivation_refs
migration_rules
agent_visibility
authority_status
```

An extension is accepted only when:

- the shared ontology cannot represent the concept without distortion;
- it does not rename an existing primitive merely for brand language;
- its lifecycle, authority, and retrieval behavior differ materially;
- every new type has competency questions, examples, counterexamples, and validation fixtures;
- shared platform code consumes the extension through generic registry interfaces;
- a second brand without the extension still runs unchanged.

Reusable extensions may later be proposed for promotion into the shared Brand ontology. Client facts
never become shared definitions through that process.

## 9. World lifecycle and authority

### 9.1 Capture-to-acceptance flow

```text
Source capture
→ immutable ContentUnit and Source
→ bounded Evidence
→ Observation proposals
→ Entity resolution
→ Interpretation/Hypothesis proposals
→ coverage and contradiction assessment
→ FDE review
→ client review
→ authorized Decision
→ accepted v3 records on main
→ dependency assessment
→ rebuildable projections
```

Every stage can return `hold`, `partial`, `branch`, `ask`, or `no_hit`. Missing information is never
repaired by plausible prose.

### 9.2 Write operations

The stable World service exposes explicit operations:

```text
observe(source, evidence, scope)
propose(change_set, derivation)
review(proposal, disposition, findings)
approve(proposal, authority_grant)
reject(proposal, authority_grant, rationale)
supersede(record, replacement, authority_grant)
merge(branch, target, conflict_resolution, authority_grant)
assess_dependencies(change_set)
```

There is no generic `saveRecord` endpoint.

### 9.3 Read operations

```text
get(id, version?)
get_state(entity, context, at_time?)
related(id, relation_or_role, scope)
search(query, scope, semantic_kinds, abstraction)
evidence(id)
history(id)
diff(left_ref, right_ref)
dependencies(id, direction, scope)
compile_context(request)
```

All responses identify whether they are canonical records, analytical results, or projections.

## 10. Context Compiler v2

### 10.1 Request

```text
request_id
agent_definition_ref
task_ref
objective
current_work_state_ref
authority_grant_refs
workspace_and_branch
perspective_refs
time_and_scope
desired_abstraction
sufficiency_policy_ref
retrieval_and_expansion_budget
required_output_schema
```

### 10.2 Compilation process

1. Resolve agent, Task, workspace, branch, authority, and route policy.
2. Load always-present identity principles and hard constraints authorized for that agent/task.
3. Select a candidate RouteDefinition for the task family.
4. Traverse exact and lexical roads within the smallest relevant Brand modules.
5. Assemble high-level typed records, conflicts, and active dependencies.
6. Evaluate sufficiency and freshness deterministically where possible.
7. Expand toward evidence, history, or neighboring modules only for a named insufficiency.
8. Apply privacy, disclosure, authority, valid-time, and status gates.
9. Emit the immutable ContextPacket, citations, omissions, unresolved conflicts, and instructions.
10. Persist ContextRunTrace and RouteEvaluation; do not persist a model synthesis as Brand truth.

### 10.3 Route contract

A RouteDefinition includes task family, eligible agent roles, start modules, required semantic kinds,
allowed relation families, abstraction order, mandatory gates, expansion triggers, stop conditions,
budgets, evaluators, version, and evidence of prior effectiveness.

No route may contain client facts. Brand-specific route bindings reference Brand records by stable ID.

## 11. Specialist agents

The first reusable roster contains four agents:

1. **Researcher** — question decomposition, source evaluation, evidence extraction, contradiction and
   gap search, bounded synthesis.
2. **Strategist** — objective, tension, alternatives, supporting/disconfirming evidence, trade-offs,
   recommendation or escalation.
3. **Creator** — translates an approved direction and ManifestationPackage into an artifact while
   preserving locked meaning and claim boundaries.
4. **Brand Guardian** — evaluates claim lineage, identity coherence, manifestation constraints,
   permissions, risk, and freshness; returns allow-for-review, revise, branch, or hold.

The Director is deferred until the Work Ledger proves multi-task coordination needs. Until then, a
deterministic workflow coordinates the four roles. Agent personality and visual identity never
substitute for cognition or permissions.

Each AgentDefinition must include:

- identity and version;
- role, responsibilities, and non-responsibilities;
- allowed semantic kinds, workspaces, tools, and actions;
- operator graph and expected input/output schemas;
- route bindings and always-present context policy;
- validators, escalation rules, and stopping conditions;
- authority ceiling;
- presentation profile;
- golden, adversarial, no-hit, and conflict evaluation cases.

## 12. Work Ledger and domain events

The Work Ledger is the connective product substrate, not another workflow engine.

```text
Task
├── objective and requester
├── assignee or workflow ref
├── Brand/context refs
├── dependencies
├── expected result schema
├── priority and status
├── authority refs
└── work-event history

Result / Artifact
├── producer and Task ref
├── structured output
├── Brand/evidence/context refs
├── assumptions and uncertainty
├── evaluation and review refs
└── version/freshness state
```

Runtime events are translated into stable product events such as `research.started`,
`insight.proposed`, `recommendation.created`, `review.required`, `decision.approved`,
`artifact.exported`, and `outcome.recorded`. Frontend modules never depend on LangGraph node names or
provider event formats.

## 13. Manifestation and artifact intelligence

The first ManifestationPackage compiles:

```text
identity principles and invariants
+ selected strategic decision
+ offering truth and claim boundaries
+ audience/relationship context
+ medium and channel
+ objective and moment
+ representation dependencies
+ local overrides
→ semantic kernel
→ locked constraints
→ adaptive directions
→ optional influences
→ prohibited framings
→ element responsibilities
→ evaluation rubric
```

Representation modes are `canonical`, `adaptive`, and `product_specific`. Constraint force is
expressed separately through `must`, `should`, `may`, and `must_not` rules. This avoids conflating
what an entity is with how strongly one expression must inherit it.

The initial ArtifactCompositionGraph supports a newsletter issue:

- issue, subject line, preheader, opening, distinction, explanation, practical implication, closing,
  feedback prompt, optional product mention;
- element purpose and context packet;
- hierarchy, sequence, rhythm, repetition, tension, and reader-value relations;
- element-level evaluation plus whole-issue evaluation;
- claim/evidence bindings and freshness dependencies.

It must be domain-extensible rather than hard-coded as a universal newsletter schema.

## 14. Unified product experience

The primary application is organized around consequential typed objects, not ontology management.

### Primary routes

- **Feed:** Insight, Recommendation, Approval Request, Result, Question, and Change posts.
- **World:** progressive Brand World map, search, history, diff, evidence, and dependency views.
- **Work:** Tasks, artifacts, dependencies, reviews, and status.
- **Create:** manifestation workspaces beginning with Newsletter.
- **Setup:** sources, people, permissions, agent roster, ontology extensions, and legacy archive.

### Post interactions

Every interaction has explicit semantics:

- acknowledge/like: weak preference signal only;
- discuss: anchored conversation, no truth mutation;
- correct: creates a correction proposal linked to the affected record;
- adjust: creates a revised recommendation/artifact branch;
- approve/reject: requires authority and creates a Decision;
- ask: creates a scoped Task for an agent;
- inspect: reveals reasoning summary, route, world records, evidence, history, and omissions.

The existing Brand World graph becomes the World module. Its visual systems are projection filters.
The existing dossier design becomes semantic-type-aware. Creative Studio's governed action and
review patterns become the Create module. Brand Intake becomes guided Setup/Discover.

## 15. Legacy isolation and readability

### 15.1 Legacy archive contents

Before cutover, create immutable archives for:

- Brand ontology v1 definitions;
- Brand ontology v2 candidate definitions;
- every v1/v2 Brand workspace source record;
- old projection payloads required for faithful reading;
- source catalogs and evidence notes;
- schema documentation;
- record counts and relationship coverage;
- SHA-256 checksums;
- migration mapping and disposition ledger.

### 15.2 Read-only boundary

Legacy content is moved under `legacy/brand-world/v1` and `legacy/brand-world/v2`, or an equivalent
explicit archive root. A minimal `legacy/brand-world-reader` may provide GET-only access.

Enforcement is structural, not conventional:

- the reader package exposes no repository write interface;
- the archived store/file permissions are read-only in deployment;
- no POST, PUT, PATCH, DELETE, promotion, context compilation, or projection-to-active-world route
  exists;
- the active API cannot resolve legacy IDs except through an explicit `/legacy/...` request;
- agents and workflows cannot include the legacy workspace in KnowledgeAccess;
- Cognee and other active projections exclude legacy datasets;
- no active package can import from `legacy/` according to dependency and lint checks.

### 15.3 Migration disposition ledger

Every legacy ID receives exactly one disposition:

- `migrated` — maps to one or more v3 IDs with transformation and evidence continuity;
- `archived_only` — remains readable but intentionally has no active equivalent;
- `quarantined` — ambiguous, malformed, or authority-sensitive; requires human resolution;
- `rejected` — invalid duplicate or projection artifact, with explicit rationale.

The ledger records old ID/version, new refs, transformation rule/version, input hash, output hash,
information loss, reviewer, decision, and timestamp.

### 15.4 Definition of “no leftover traces”

At final cutover:

- there are zero imports of v1/v2 contracts outside `legacy/`, migration fixtures, and historical
  documentation;
- there are zero active API schemas, UI labels, feature flags, database writes, context routes, or
  Cognee projections using v1/v2 semantic types;
- the default Brand World API has no fallback to a legacy resolver;
- no dual-write, lazy conversion, alias type, or compatibility branch remains;
- old apps are removed from active registries and workspace membership;
- current indexes, architecture inventories, make targets, runbooks, and product surfaces name only
  maintained modules;
- superseded docs carry a clear historical marker and point to v3;
- the only legacy entrypoint is explicit, read-only, and excluded from agent retrieval.

## 16. Migration phases and gates

### Phase 0 — approve the contract

Deliverables:

- Product proposal selecting the managed Brand World plus Biotic newsletter loop.
- ADR selecting evolutionary replacement and legacy-read-only policy.
- v3 vocabulary and naming register.
- scope and non-goals.

Gate:

- User approves the constitutional grammar, Brand modules, first loop, and legacy policy.
- No implementation begins with unresolved semantic ownership.

### Phase 1 — inventory and freeze v1/v2

Deliverables:

- Machine-readable inventory of every v1/v2 type, relation, field, record, endpoint, projection,
  import, test, UI label, documentation reference, and runtime consumer.
- Baseline hashes, record counts, relation counts, source/evidence coverage, and screenshots.
- Forbidden-symbol and dependency lists for cleanup validation.
- Legacy write freeze.

Gate:

- Every current object and consumer has an owner and disposition category.
- Existing relevant tests pass before migration work.

### Phase 2 — implement the constitutional kernel

Deliverables:

- Versioned v3 semantic schemas and validators.
- Decision and change-set contracts.
- Schema conformance, property, temporal, authority, branch, and provenance tests.
- No Brand-specific facts or projection labels in the kernel.

Gate:

- Each primitive passes examples, counterexamples, round-trip serialization, invalid-state, and
  authority tests.
- Ontology-conflation evaluators pass.

### Phase 3 — implement modular Brand ontology

Deliverables:

- Eight canonical Brand modules and dependency manifest.
- Extension contract and validator.
- Competency questions and synthetic fixtures per module.
- Eight-system projection rules stored separately.

Gate:

- No circular module imports.
- Every current useful Biotic concept has a valid mapping or explicit quarantine reason.
- The eight-system view can be rebuilt without adding semantic meaning.

### Phase 4 — implement World service and persistence

Deliverables:

- Provider-neutral World service and repository ports.
- SQLite v3 adapter with append-oriented versions and transactional change sets.
- Proposal/review/approve/reject/supersede/merge operations.
- History, diff, evidence, relations, and dependency reads.

Gate:

- Failed or unauthorized change sets leave no partial writes.
- Accepted history can be reconstructed at arbitrary supported time/branch points.
- Storage schemas do not leak into domain contracts.

### Phase 5 — migrate Biotic as the golden world

Deliverables:

- Deterministic migration rules and disposition ledger.
- Migrated public-research branch preserving all evidence and uncertainty.
- Separate FDE/client-approved branch populated through explicit review decisions.
- Coverage, contradiction, missing-information, and relation-integrity report.

Gate:

- One hundred percent of legacy IDs have dispositions.
- Zero dangling canonical relations.
- No unsupported interpretation is promoted.
- User approves the resulting Biotic world as the golden semantic fixture.

### Phase 6 — Context Compiler v2

Deliverables:

- Request, RouteDefinition, RouteEvaluation, sufficiency, packet, and trace contracts.
- High-level-first traversal with bounded expansion.
- World and visual-language resolvers over v3 only.
- Exact trace inspection and replay.

Gate:

- Agent/task changes produce explainably different packets from the same world.
- Missing authority, stale evidence, conflict, and budget exhaustion return correct non-success states.
- No legacy record can enter a v3 ContextPacket.

### Phase 7 — Work Ledger and specialist definitions

Deliverables:

- Work package, persistence adapter, and domain-event translator.
- Researcher, Strategist, Creator, and Brand Guardian definitions.
- Operator compositions and evaluation fixtures.
- Workflow runs linked to Tasks and Results by stable references.

Gate:

- Retry, cancellation, partial completion, review, reassignment, and resume preserve idempotency and
  lineage.
- Seeded unsupported claims and authority violations are caught by Brand Guardian.

### Phase 8 — Manifestation and newsletter composition

Deliverables:

- ManifestationPolicy and TransformationPackage contracts.
- Newsletter ArtifactCompositionGraph profile.
- Existing newsletter workflow migrated to v3 context, Work, Artifact, and Guardian contracts.
- Element and whole-composition evaluation.

Gate:

- Every factual sentence resolves to approved claim permissions and evidence.
- Locked meaning survives plan, packet, draft, revision, and review.
- Strong elements in a deliberately incoherent composition fail whole-artifact evaluation.

### Phase 9 — unified application

Deliverables:

- One authenticated shell with Feed, World, Work, Create, and Setup modules.
- Progressive type-aware dossiers.
- Anchored discussion and semantic actions.
- Approval center with complete consequence information.
- Legacy Archive entry clearly separated from current Brand World.

Gate:

- A user can complete the golden loop without opening a runtime console or editing YAML.
- Keyboard, focus, reduced motion, empty, loading, error, partial, hold, and no-hit states pass.
- UI never presents a projection or agent proposal as canonical truth.

### Phase 10 — single-write cutover

Deliverables:

- v3 becomes the only canonical Brand write path.
- Active workspace registries, APIs, workflow definitions, Context Compiler, and applications switch
  to v3.
- v1/v2 stores and files become immutable legacy archives.
- Rollback snapshot and cutover receipt.

Gate:

- Complete golden loop passes on production-like local deployment.
- Data hashes and migration ledger reconcile.
- Rollback restores pre-cutover readability without accepting legacy writes.

### Phase 11 — active legacy eradication

Deliverables:

- Remove old package exports, projectors, handlers, routes, apps, make targets, feature flags, tests,
  and documentation from active modules.
- Move historical fixtures and schemas into the legacy boundary.
- Update `AGENT_INDEX.md`, Product architecture, registries, source catalogs, and runbooks.
- Generate a zero-active-reference audit.

Gate:

- Forbidden-symbol scan reports zero unapproved legacy references.
- Dependency graph proves no active-to-legacy edge.
- Fresh install and full test run succeed without loading the legacy archive.
- Explicit legacy GET reads still reproduce preserved records and hashes.

### Phase 12 — complete loop and second-brand proof

Deliverables:

- Human-approved newsletter export.
- Bounded qualitative and quantitative outcome capture.
- Reviewed LearningUpdate and dependency/staleness proposal.
- Second isolated brand workspace using the same contracts without shared-code modification.
- FDE onboarding effort and exception log.

Gate:

- The system demonstrates source → world → context → cognition → decision → manifestation → reality
  → learning with complete lineage.
- Second-brand exceptions are configuration/extension records, not platform code branches.

## 17. Test strategy

### Contract and invariant tests

- semantic kind separation;
- temporal and branch correctness;
- context overlap and scope narrowing;
- authority and decision transitions;
- provenance and derivation completeness;
- dependency and freshness evaluation;
- extension-module isolation;
- no generic metadata escape hatch.

### Migration tests

- deterministic input/output hashes;
- complete disposition ledger;
- preserved IDs or explicit ID mappings;
- relation endpoint integrity;
- evidence/source continuity;
- no status or authority elevation;
- idempotent re-run;
- quarantine behavior;
- read-only legacy access.

### Semantic continuity tests

- source assertion survives evidence, observation, interpretation, approved claim, context packet,
  content plan, draft, and review without meaning drift;
- correction changes only the affected branch/record;
- v3 projection reproduces expected navigational placement without changing type;
- conflicting perspectives remain separately inspectable.

### Agent and context tests

- task/agent-specific context selection;
- high-level-first expansion and explicit stop reason;
- disconfirming evidence inclusion;
- insufficiency, no-hit, conflict, stale, and unauthorized cases;
- exact ContextRunTrace replay;
- specialist procedure adherence and Guardian adversarial cases.

### Work and runtime tests

- authorization-filtered discovery;
- task dependencies and parallel-safe ordering;
- retries and idempotent external action;
- cancellation and resume;
- partial/hold propagation;
- runtime-event to domain-event translation;
- provider preflight and disclosure limits.

### Experience tests

- complete golden user journey;
- evidence and history drill-down;
- correction, adjustment, approval, rejection, and branch semantics;
- accessibility and reduced motion;
- visual regression against design-language contract;
- explicit separation of current and legacy worlds.

### Cleanup tests

- forbidden import scanner;
- active registry and workspace inventory validator;
- legacy route method test allowing GET/HEAD only;
- fresh-install test with legacy directory unavailable;
- no default query, context, search, or projection includes legacy;
- stale docs and command scanner;
- architecture ownership and circular-dependency validation.

## 18. Acceptance criteria for the complete system

The migration is complete only when all are true:

1. One canonical v3 Brand grammar and module registry exist.
2. All active Brand writes use explicit domain operations over v3.
3. Every legacy ID has a disposition and remains readable through the archive where required.
4. No active dependency, fallback, flag, alias, projection, or context route uses v1/v2.
5. Biotic's approved world is distinct from its public-research evidence branch.
6. A human can inspect and approve every normative Brand commitment.
7. Agents receive task-, state-, authority-, time-, and abstraction-specific context with a replayable
   trace.
8. Specialist cognition is versioned and evaluated independently of personality and provider.
9. The newsletter loop preserves meaning and evidence through an authorized human review/export.
10. Outcomes return as evidence and produce reviewed learning rather than automatic truth changes.
11. The active application is coherent and accessible, with legacy clearly separated.
12. A second brand runs without modifications to shared packages or agent code.
13. All repository quality gates pass from a fresh checkout.
14. Product and architecture workspaces accurately describe observed runtime state.

## 19. Explicit non-goals for the migration

- broad autonomous execution;
- a large connector marketplace;
- production-scale analytical warehouse;
- audience simulation before real calibration evidence;
- a visible Director agent before Work Ledger coordination proves the need;
- supporting every artifact medium in v3.0;
- automatically promoting client extensions into the universal ontology;
- preserving old APIs as active compatibility aliases;
- using graph, vector, model, or workflow-provider types as canonical semantics.

## 20. Implementation workstreams

The phases should be delivered through bounded workstreams with one owner each:

- `W1` Product decision and semantic constitution
- `W2` v1/v2 inventory, freeze, and legacy archive
- `W3` constitutional semantic kernel
- `W4` modular Brand ontology and extensions
- `W5` World service and canonical persistence
- `W6` Biotic migration and human approval
- `W7` Context Compiler and routes
- `W8` Work Ledger and domain events
- `W9` specialist agents and evaluations
- `W10` manifestation and newsletter artifact intelligence
- `W11` unified product application
- `W12` cutover, cleanup, legacy verification, and second-brand certification

No workstream may introduce a local substitute for an upstream contract owned by another stream.
Cross-stream handoffs use accepted schemas and fixtures, not copied prose.

## 21. Formation packet

- mode: `form`
- operator: `world://operator/concept-lab/formation-projection@1`
- selected theory branch: layered Brand World grammar with evolutionary replacement and isolated
  read-only legacy access
- source refs:
  - `docs/research/ideal-brand-system-conversation/01-ideal-system-substrate.md`
  - `docs/research/ideal-brand-system-conversation/03-semantic-intelligence-architecture.md`
  - `docs/research/ideal-brand-system-conversation/04-technical-and-agent-architecture.md`
  - `docs/research/ideal-brand-system-conversation/08-current-vs-ideal-base-product.md`
  - `docs/plans/2026-09-14-brand-world-grounding-dossier-design.md`
  - `domains/brand/ontology/brand-system.yaml`
  - `domains/brand/ontology-v2/manifest.yaml`
- derivation refs:
  - `world://operator/guardrail/boundary-conflation@1`
  - `world://operator/guardrail/ontology-conflation@1`
- target workspace: `world://workspace/testflight-product`
- target modules: `architecture`, `product-definition`, `research-learning`, then
  `product-decisions` for explicit promotion
- authority: proposal only
- `canonical_write: false`
- alternatives:
  - in-place ontology patch — rejected for active legacy contamination risk
  - greenfield rewrite — rejected for loss of tested semantic/runtime foundations
- evaluator results:
  - `formation-schema`: pass
  - `formation-invariants`: pass
  - `formation-semantics`: pass
  - `formation-usefulness`: pass
  - `plane-coverage`: pass
  - `handoff-completeness`: pass at design level; runtime proof remains a phase gate
  - `reversibility`: pass by immutable archive, migration ledger, and rebuildable projections
  - `typed-consistency`: pass at proposed contract level
  - `adapter-thinness`: pass at proposed boundary level
- unresolved promotion boundary: this design does not become accepted Product architecture until the
  user approves it and a Product decision records that promotion.
