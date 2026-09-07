# Brand World Missing Layers — Implementation Design

**Date:** 2026-08-31  
**Status:** Proposed  
**Scope:** Extend the existing Testflight semantic, Brand, federation, Cognee projection, context-intelligence, and explorer architecture. This design does not adopt another framework's kernel and does not replace the current records.

## 1. Outcome

Build the missing layers that turn the current connected Brand knowledge graph into a branch-aware, perspective-aware decision system. The system must be able to:

- distinguish modeled conditions from claims and beliefs;
- preserve several interpretations and hypothetical scenarios at once;
- express relationships involving several participants and conditions;
- compile bounded world views for agents;
- trace research through decisions, creative production, and measurement;
- represent hypotheses and experiments without presenting predictions as observations;
- prepare an explicit future boundary for simulation.

The first release remains descriptive and decision-supporting. It does not execute simulations.

## 2. Product principles

1. **Extend, do not replace.** Existing entities, assertions, contexts, evidence, decisions, dependencies, representation profiles, and federation records remain valid.
2. **Compose records by reference.** New records connect using stable IDs. Avoid a single giant Brand object or deep inheritance tree.
3. **Keep meanings distinct.** A state, claim, belief, perspective, decision, hypothesis, and prediction are different records even when they discuss the same subject.
4. **Store differences, not copies.** Branches are overlays on a parent branch.
5. **No silent promotion.** Hypotheses, scenarios, generated interpretations, and future simulation outputs never become accepted knowledge without an explicit reviewed operation.
6. **Context is mandatory.** Audience, offering, market, channel, time, campaign, locale, branch, and other applicable dimensions remain visible through the whole chain.
7. **Retrieval is bounded.** The intelligence layer receives only permitted and task-relevant records.
8. **Canonical records are provider-neutral.** Cognee, search indexes, and explorer views are rebuildable projections.
9. **No automatic creative rewrite.** Changes mark dependent records for review; authorized decisions create new versions.
10. **Simulation is earned.** A future simulator may consume only explicit scenario specifications with assumptions, variables, mechanisms, and uncertainty.

## 3. Layered architecture

```text
Existing canonical Brand world
entities · assertions · evidence · contexts · versions · representation
                              │
                              ▼
Interpretation layer
state snapshots · perspectives · world branches · relationship frames
                              │
                              ▼
Decision and learning layer
hypotheses · decisions · dependency impacts · experiment plans · outcomes
                              │
                              ▼
Agent context layer
world-view request · resolution policy · resolved world view · context packet
                              │
                              ▼
Future operational layer
scenario specification · compilation · simulation run · predicted outcomes
```

Every layer may reference records below it. A higher layer cannot silently mutate or reclassify a lower-layer record.

## 4. Canonical record additions

### 4.1 `StateSnapshot`

Purpose: describe a modeled condition at a time and context, separately from claims about that condition.

Required fields:

- `state_id`
- `subject_ids`
- `state_type_id`
- `context_id`
- `valid_time`
- `values`: typed qualitative or quantitative values
- `unit_refs` where applicable
- `source_assertion_ids`
- `evidence_refs`
- `status`: proposed, supported, contested, superseded, retired
- `derivation_id`

Rules:

- a StateSnapshot must not contain speaker or belief semantics;
- changes produce a new version rather than overwriting history;
- quantitative values require units and measurement provenance;
- contradictory StateSnapshots may coexist when their branch, context, method, or evidence differs.

### 4.2 `PerspectiveProfile`

Purpose: represent a situated viewpoint rather than a simple perspective label.

Required fields:

- `perspective_id`
- `holder_id`: person, team, audience, instrument, organization, or agent
- `perspective_type_id`
- `context_id`
- `goals`
- `accessible_record_selectors`
- `assumption_ids`
- `salience_rules`
- `known_limitations`
- `valid_time`
- `authority_grant_id`
- `derivation_id`

Compatibility:

- current `Perspective` enum values remain shorthand presets;
- existing assertions may continue using the enum;
- new assertions can additionally reference a full `perspective_id`.

### 4.3 `WorldBranch`

Purpose: preserve alternative interpretations, hypotheses, forecasts, and counterfactuals without copying or replacing the accepted world.

Required fields:

- `branch_id`
- `workspace_id`
- `parent_branch_id`
- `branch_kind`: interpretation, hypothesis, scenario, counterfactual, agent-belief
- `label`
- `assumption_ids`
- `created_by`
- `created_at`
- `status`: draft, active, held, merged, rejected, archived
- `visibility_policy_id`
- `derivation_id`

Supporting records:

- `BranchDelta`: add, exclude, replace, or retract a record for this branch;
- `BranchConflict`: record incompatible claims or deltas;
- `MergeAssessment`: enumerate accepted changes, rejected changes, unresolved conflicts, and authority.

Resolution behavior:

1. read the parent chain;
2. apply child deltas in order;
3. preserve unresolved conflicts;
4. never treat the default branch as objective truth;
5. require a reviewed merge to affect an accepted branch.

### 4.4 `RelationshipFrame`

Purpose: describe a situation or relationship with several named participants and conditions.

Required fields:

- `frame_id`
- `frame_type_id`
- `context_id`
- `role_bindings`: role ID to one or more record IDs or values
- `assertion_ids`
- `constraint_ids`
- `valid_time`
- `status`
- `evidence_refs`
- `derivation_id`

Example roles for a campaign targeting frame:

- offering
- audience
- market
- campaign
- channel
- objective
- owner
- budget
- approval
- validity window

Binary assertions remain the canonical simple form and graph projection. A RelationshipFrame groups and qualifies them; it does not erase them.

### 4.5 `HypothesisRecord`

Purpose: preserve a proposed explanation or expected effect as uncertain reasoning.

Required fields:

- `hypothesis_id`
- `branch_id`
- `context_id`
- `input_ids`
- `proposition`
- `mechanism_description`
- `alternative_hypothesis_ids`
- `supporting_evidence_refs`
- `opposing_evidence_refs`
- `assumption_ids`
- `confidence`: optional and explicitly uncalibrated unless a calibration policy exists
- `falsification_conditions`
- `status`: proposed, testable, supported, weakened, rejected, held
- `derivation_id`

### 4.6 `ExperimentPlan`

Purpose: describe how a hypothesis could be tested without confusing an intended test with an observed result.

Required fields:

- `experiment_id`
- `hypothesis_ids`
- `branch_id`
- `context_id`
- `intervention`
- `comparison_or_control`
- `population_selector`
- `assignment_method`
- `metric_ids`
- `success_thresholds`
- `guardrail_metric_ids`
- `time_window`
- `sample_requirements`
- `risk_and_ethics_constraints`
- `status`: draft, approved, running, completed, cancelled
- `authority_grant_id`
- `derivation_id`

Results remain existing Measurements and ObservedOutcomes, connected to the ExperimentPlan through explicit assertions.

### 4.7 `ResolvedWorldView`

Purpose: provide a deterministic, inspectable intermediate result between retrieval and agent context generation.

Required fields:

- `view_id`
- `workspace_ids`
- `branch_id`
- `perspective_ids`
- `context_id`
- `task_type`
- selected entity, state, assertion, frame, decision, hypothesis, constraint, representation, and evidence IDs
- unresolved conflict IDs
- omissions and no-hit sections
- traversal budget and route receipt
- policy and ontology versions
- derivation ID

This record is not prose. It is the structured input from which the intelligence model compiles the final ContextPacket.

## 5. Cross-record interaction rules

The records are designed to cross modules while preserving their roles.

```text
Evidence
  → supports/opposes Claim
  → Claim describes StateSnapshot
  → PerspectiveProfile interprets Claim or StateSnapshot
  → WorldBranch selects assumptions and competing Claims
  → RelationshipFrame binds product, audience, market, and campaign
  → HypothesisRecord proposes an effect
  → DecisionRecord selects an authorized option
  → CreativeBrief and Asset implement that decision
  → ExperimentPlan tests the hypothesis
  → Measurement records observed results
  → Learning informs a later decision
```

Mandatory barriers:

- Perspective → Claim is allowed; Perspective → shared State mutation is not.
- Hypothesis → Decision input is allowed; Hypothesis → accepted fact is not.
- Branch → ContextPacket is allowed; Branch → parent mutation is not.
- ExperimentPlan → Measurement definition is allowed; planned outcome → observation is not.
- Future simulation output → scenario evidence is allowed; simulation output → empirical evidence is not.

## 6. Runtime flow

### 6.1 Request

The main agent or Cordis plugin sends a `WorldViewRequest` containing:

- task and desired output;
- requested brand or container root;
- known offering, audience, market, channel, campaign, locale, and time;
- requested branch or scenario;
- requested perspective where applicable;
- permitted workspaces and evidence classes;
- retrieval and reasoning budget.

### 6.2 Deterministic resolution

Before model reasoning:

1. validate workspace permissions;
2. route child-first through federation;
3. resolve branch ancestry and deltas;
4. resolve the applicable Context;
5. select requested or default PerspectiveProfiles;
6. retrieve exact and scoped candidates;
7. expand only explicitly allowed relationship frames and dependencies;
8. remove obvious context, branch, time, and permission mismatches;
9. preserve contradictions, no-hits, and missing required dimensions;
10. build `ResolvedWorldView` with a route receipt.

### 6.3 Intelligence compilation

The dedicated intelligence model receives the request plus ResolvedWorldView. It may:

- rank evidence for the current workflow;
- summarize claims without changing status;
- explain conflicts and uncertainty;
- select the load-bearing context for the main agent;
- identify missing information;
- recommend clarification when the result would materially change.

It returns the existing ContextPacket plus new sections for states, branch assumptions, perspectives, frames, conflicts, hypotheses, constraints, and decision lineage.

### 6.4 Main-agent use

The main agent reasons over the bounded packet. Any proposed new knowledge is returned as candidate records with derivation and evidence references. It cannot write accepted knowledge merely by generating an answer or artifact.

## 7. Retrieval behavior

Retrieval should operate in stages:

1. **Identity resolution:** find exact Brand, offering, audience, campaign, and asset identities.
2. **Container routing:** select the smallest child container, then explicit parent supplements.
3. **Applicability filtering:** branch, time, geography, audience, channel, product, and purpose.
4. **Workflow expansion:** follow task-specific relationship families only.
5. **Evidence expansion:** fetch source spans for material claims and decisions.
6. **Conflict expansion:** retrieve opposing claims and unresolved alternatives.
7. **Representation expansion:** resolve applicable visual and verbal language.
8. **Dependency expansion:** fetch downstream or upstream review relationships when relevant.
9. **Budget enforcement:** stop when relevance, hop, record, token, or latency limits are reached.

Retrieval outcomes remain `hit`, `partial`, `no_hit`, `hold`, or `ask`. A parent-wide fallback is not automatic when a child container returns no hit.

## 8. Brand and marketing ontology modules

Keep the current v2 modules and add the following candidate modules independently:

### 8.1 Market and competition

- MarketCategory
- Competitor
- CompetitiveAlternative
- MarketPosition
- Differentiator
- ParityPoint
- CompetitorClaim
- MarketTrend

### 8.2 Customer journey and occasions

- JourneyStage
- CustomerOccasion
- Touchpoint
- Barrier
- Trigger
- ExperienceMoment
- DesiredProgress

### 8.3 Commerce, offer, and economics

- Offer
- Price
- Discount
- Bundle
- Promotion
- CostConstraint
- MarginTarget
- RevenueObjective
- InventoryConstraint

### 8.4 Media and distribution

- Placement
- Format
- MediaPlan
- AudienceDeliveryRule
- PlatformConstraint
- FrequencyPolicy
- SpendAllocation

### 8.5 Experimentation and attribution

- MetricDefinition
- ExperimentPlan
- Treatment
- Control
- MeasurementMethod
- AttributionModel
- ObservedOutcome
- Learning

### 8.6 Governance and production

- Team
- Role
- Agency
- Approval
- OwnershipAssignment
- Budget
- Deadline
- LegalConstraint
- BrandSafetyConstraint
- PlatformPolicy

All additions stay candidate until competency questions, examples, counterexamples, fixtures, and integrity tests pass.

## 9. Storage and projection

### Canonical storage

- append-only or versioned provider-neutral records;
- stable IDs and explicit supersession;
- derivation graph for every generated record;
- authorization checked before persistence;
- no generated databases or indexes committed to the repository.

### Cognee projection

Project each canonical record as a typed document with:

- record ID and record kind;
- branch and context selectors;
- participant IDs and relationship roles;
- evidence and derivation references;
- lifecycle and epistemic status;
- workspace and permission scope;
- compact retrieval text plus exact structured metadata.

Frames become a hub node plus role edges in the graph projection. Branch deltas and perspective-specific claims remain tagged and must not be merged into unscoped facts.

### Explorer

Add views for:

- State versus Claims;
- branch tree and branch differences;
- perspective comparison;
- relationship-frame participants;
- decision and evidence lineage;
- hypothesis and experiment status;
- applicable contexts and constraints;
- downstream dependency impact.

## 10. API and package boundaries

### `packages/testflight-semantic`

Own provider-neutral records and deterministic operations:

- `states.py`
- `perspectives.py`
- `branches.py`
- `relationship_frames.py`
- `hypotheses.py`
- `experiments.py`
- `world_views.py`

No Cognee or DeepSeek imports are allowed here.

### `packages/testflight-brand`

Own Brand-specific modules, validation, relationship roles, and competency questions. It imports the semantic package, never a runtime adapter.

### `adapters/cognee`

Own projection, retrieval, and reconstruction mappings. It must not invent semantic status or branch resolution.

### `packages/testflight-context-intelligence`

Own WorldViewRequest contracts, ResolvedWorldView-to-ContextPacket compilation, intelligence-model prompts, clarification behavior, and trace receipts.

### Cordis plugin

Own activation, runtime configuration, and main-agent tool exposure. Keep the internal service behind interfaces so it can later run as a standalone process.

### Brand Lab explorer

Own read-only inspection and comparison views. It must display canonical status, evidence, branch, context, and omissions rather than inferring missing facts.

## 11. Failure and uncertainty behavior

- Missing required context produces `ask` or `partial`, not guessed applicability.
- Unknown branch produces `no_hit` or `hold` depending on authority implications.
- Conflicting accepted claims remain visible and prevent false synthesis.
- Missing evidence yields an unsupported or held candidate.
- Branch merge with unresolved conflicts yields a MergeAssessment but no mutation.
- A stale upstream record marks dependent views and assets potentially stale.
- An invalid RelationshipFrame is rejected when required roles or referenced records are absent.
- A PerspectiveProfile cannot expose records outside its holder's permissions.
- Intelligence-model failure returns the deterministic ResolvedWorldView and a partial packet where safe.
- Cognee unavailability never destroys canonical records; retrieval reports the unavailable projection.

## 12. Testing strategy

### Unit tests

- record validation and immutability;
- branch overlay resolution;
- conflict preservation and merge assessment;
- state/claim separation;
- perspective visibility and non-interference;
- frame role integrity;
- hypothesis status and evidence polarity;
- experiment plan/result separation;
- context, time, and permission filtering;
- deterministic world-view IDs and route receipts.

### Generative-node tests

- packet compilation follows the selected branch and perspective;
- no unsupported claim becomes accepted;
- missing material information triggers the minimum clarification;
- summaries preserve evidence, conflict, time, and authority;
- context packets stay within size and relevance budgets.

### Semantic-continuity tests

- research → insight → decision → brief → asset;
- asset → experiment → outcome → learning → later decision;
- ICP revision → matching dependency impact only;
- branch assumption survives retrieval, compilation, generation, and review;
- perspective-specific interpretation is never converted into a shared state.

### Synthetic worlds

Add fixtures for:

1. competing positioning branches;
2. observed StateSnapshot with conflicting team claims;
3. one campaign RelationshipFrame with product, ICP, market, channel, budget, and approval;
4. customer and strategy-team perspectives over the same product;
5. hypothesis and experiment with an inconclusive outcome;
6. branch merge containing one accepted delta and one unresolved conflict;
7. unauthorized perspective access;
8. future-simulation readiness without executable mechanisms.

### End-to-end acceptance case

Request: create a Nike App acquisition asset for first-time runners in Germany on Instagram.

The result must show:

- child-first Nike App routing;
- selected accepted branch;
- applicable customer and Brand perspectives;
- relevant StateSnapshots and claims;
- campaign RelationshipFrame;
- decision lineage and governing visual language;
- conflicts, assumptions, and missing information;
- exact evidence references;
- no contamination from unrelated audiences, markets, branches, or historical visual languages.

## 13. Migration and compatibility

1. Introduce new records as additive candidate contracts.
2. Keep current assertion and Perspective enum APIs working.
3. Add optional `perspective_id`, `branch_id`, and richer evidence-link fields through versioned models rather than breaking current fixtures.
4. Generate initial StateSnapshots only from explicitly selected accepted assertions or measurements; do not backfill everything automatically.
5. Create RelationshipFrames only where several existing assertions clearly describe one situation.
6. Keep `main` as the current default branch but create a real WorldBranch record for it.
7. Rebuild Cognee projections after canonical validation.
8. Compare old and new retrieval packets on golden requests before switching defaults.
9. Retain a compatibility packet mode during rollout.
10. Remove compatibility behavior only after all existing Nike probes and mock requests pass.

## 14. Implementation phases

### Phase 0 — Contract and corpus inventory

- map existing models and projection fields to the new records;
- classify compatibility, extension, or migration needs;
- freeze golden retrieval traces for current Nike requests;
- define IDs, statuses, and versioning rules.

**Gate:** no ambiguous ownership between semantic, Brand, adapter, and runtime packages.

### Phase 1 — States and evidence polarity

- implement StateSnapshot;
- add typed support, opposition, qualification, and inconclusive evidence links;
- enforce measurement units and temporal scope;
- add state/claim explorer view.

**Gate:** conflicting claims can refer to one state without overwriting it.

### Phase 2 — Branches

- implement WorldBranch, BranchDelta, BranchConflict, and MergeAssessment;
- implement deterministic overlay resolution;
- create explicit `main` branch records;
- add branch-aware projection and explorer tree.

**Gate:** two positioning alternatives coexist and retrieve independently.

### Phase 3 — Perspectives

- implement PerspectiveProfile and selector/visibility rules;
- retain enum compatibility;
- add perspective-aware retrieval and comparison UI.

**Gate:** customer and internal-team views can disagree without changing shared records.

### Phase 4 — Relationship frames

- implement role definitions, frames, validators, and binary projections;
- add campaign and offer frame types;
- expose participant and constraint views in the explorer.

**Gate:** one campaign situation is retrieved as a coherent qualified bundle.

### Phase 5 — Hypotheses and experiments

- implement HypothesisRecord and ExperimentPlan;
- link existing Measurement, ObservedOutcome, and Learning records;
- add falsification, alternative, and inconclusive-result behavior.

**Gate:** expected effects remain separate from observed outcomes.

### Phase 6 — World-view compiler

- implement WorldViewRequest and ResolvedWorldView;
- integrate federation, branch, perspective, applicability, conflict, evidence, representation, and dependency resolution;
- extend ContextPacket and trace receipts;
- add clarification mode for material gaps.

**Gate:** deterministic selection is inspectable before model synthesis.

### Phase 7 — Marketing expansion

- add the six ontology modules in Section 8;
- populate only evidence-backed Nike examples needed for certification;
- create competency questions and retrieval probes for every module.

**Gate:** all new types have evidence basis, examples, counterexamples, fixtures, and no-hit tests.

### Phase 8 — Runtime rollout

- expose branch, perspective, and scenario options through the Cordis plugin;
- retain current automatic behavior with accepted-main defaults;
- deploy behind a runtime flag;
- compare new and compatibility packets;
- promote after retrieval, quality, latency, and safety gates pass.

**Gate:** existing mock request quality does not regress and new branch/perspective requests pass.

### Future Phase 9 — Simulation boundary

- introduce ScenarioSpecification compiled from a WorldBranch;
- require explicit variables, state domains, mechanisms, interventions, timing, uncertainty, and assumptions;
- validate semantic fidelity before execution;
- run through pluggable runtime adapters;
- store SimulationRuns and PredictedOutcomes in scenario branches only;
- compare predictions with empirical Measurements through explicit evaluation records.

This phase begins only after hypotheses and experiments demonstrate sufficient structured data.

## 15. Rollout policy

- All new types start as candidate.
- Initial default remains accepted `main` branch with no explicit PerspectiveProfile unless the workflow requires one.
- Read-only explorer support ships before agent write support.
- Candidate record creation is allowed before accepted-record promotion.
- Human or explicitly delegated authority is required for branch merge, accepted StateSnapshot creation, decision acceptance, experiment approval, and ontology promotion.
- Runtime telemetry captures route, branch, perspective, selected IDs, omissions, conflicts, token size, latency, and evaluator results without logging restricted source payloads.

## 16. Success criteria

The implementation is complete when:

1. agents can retrieve the same Brand world through different explicit branches and perspectives;
2. states, claims, beliefs, hypotheses, predictions, and observations remain distinguishable end to end;
3. complex marketing situations retrieve as coherent frames rather than disconnected sentences;
4. each ContextPacket explains why every material record was included;
5. conflicts and missing information are surfaced rather than silently resolved;
6. changes affect only context-matching downstream records;
7. existing Nike knowledge and visual-language behavior remain compatible;
8. Cognee can be fully rebuilt from canonical records;
9. the explorer makes branches, viewpoints, relationships, decisions, and evidence browsable;
10. a future ScenarioSpecification can be created without redesigning the descriptive layers.

## 17. Recommended first delivery slice

Implement Phases 0–4 together as the first coherent foundation:

- StateSnapshot and evidence polarity;
- WorldBranch and overlay resolution;
- PerspectiveProfile;
- RelationshipFrame;
- explorer support;
- Cognee projection and retrieval filters;
- four synthetic certification worlds;
- one Nike App read-only demonstration.

Then implement hypotheses, experiments, and the world-view compiler. This order establishes the semantic distinctions before model-backed context compilation depends on them.

## 18. Reasoning and evaluation receipt

- Architecture guardrails: `world://operator/guardrail/ontology-conflation@1`, `world://operator/guardrail/local-global-conflation@1`, `world://operator/guardrail/retrieval-reasoning-conflation@1`, `world://operator/guardrail/validation-persistence-conflation@1`.
- Scope: product extension of the existing Testflight system; external frameworks used only as inspiration.
- Evaluator result: proposed design preserves semantic roles, local applicability, provider boundaries, and validation-versus-persistence separation.
- Implementation receipt (2026-08-31): StateSnapshot, EvidenceLink, WorldBranch,
  BranchDelta, PerspectiveProfile, RelationshipFrame, and ResolvedWorldView are
  implemented as provider-neutral semantic contracts. The candidate Brand module
  and 11 certified synthetic worlds cover the new distinctions. A Nike
  Membership/Nike App read-only overlay is stored in
  `workspaces/brand-nike-research/artifacts/world-modeling.yaml` and resolved
  in Brand Lab before retrieval or model synthesis.
- Runtime receipt (2026-08-31): context-intelligence accepts an injected
  WorldViewResolver, records its selected IDs, omissions, and conflicts, and
  includes the resolved view in ContextPacket before evidence synthesis. The
  default remains explicitly `not_resolved` when no resolver is configured.
- Evaluator result: semantic core tests, Brand Lab request-to-view continuity,
  context-runtime resolver tests, and the full `make check` gate pass. The
  overlay remains candidate and proposal-only; it does not alter accepted Nike
  facts or generated Cognee state.
