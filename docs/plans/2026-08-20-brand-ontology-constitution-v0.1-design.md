# Brand Ontology Constitution v0.1

Status: accepted for research and implementation planning; Context encoding remains provisional  
Date: 2026-08-20  
Scope: provider-neutral Brand ontology, representation, dependency, time, identity, provenance,
governance, and certification  
Related decisions: ADR 0003 and ADR 0004

## 1. Purpose

This constitution defines the language in which Testflight will research, propose, validate, and
eventually ingest Brand knowledge. It is deliberately smaller than the eventual Brand ontology.
Its job is to prevent the research corpus, model output, Cognee projection, or an early taxonomy
from silently becoming the canonical meaning of the system.

The constitution establishes:

1. the meta-model and deterministic classification rules;
2. the separation between definition, evidence, proposals, accepted state, and projections;
3. portfolio-aware identity and system boundaries;
4. assertion, relationship, representation, dependency, temporal, and provenance contracts;
5. the research and governance process for extending the ontology; and
6. distinct certification gates for the ontology and for each runtime projection.

It does not yet choose the final Brand entity inventory, relationship inventory, evidence
thresholds, or semantic-preservation evaluator. Those are research-driven decisions with explicit
gates below.

## 2. Constitutional principles

The following rules take precedence over convenience in a provider or extraction model:

- Meaning is sequence- and context-dependent. Chunking is an evidence-location mechanism, not a
  semantic boundary.
- Canonical semantics belong to Testflight. Cognee is a rebuildable graph/vector projection.
- An entity, a mention of it, an observed occurrence, and an assertion about it are different
  records.
- Evidence supports or challenges an assertion; evidence is not itself accepted truth.
- Confidence, authority, salience, structural importance, and valence are separate dimensions.
- Truth and applicability are separate. A statement may be accepted while applying only in a
  particular market, audience, channel, product, branch, or time.
- Sequence and correlation do not establish causation.
- Definitions and accepted records are immutable. Change occurs by versioning, supersession,
  revocation, merge/split history, or a new ontology identity.
- Proposals may remain unresolved. `hold`, `branch`, `ask`, `partial`, and `no_hit` are valid
  outcomes.
- Generated stores, caches, indexes, and direct graph edges must be reproducible from canonical
  records and derivation receipts.

## 3. Semantic planes and ownership

Every durable record belongs to one primary plane. Crossing a plane requires a typed handoff and a
derivation receipt.

| Plane | Owns | Must not own |
| --- | --- | --- |
| Definition | ontology definitions, relation contracts, policies, schemas, profile and rule versions | source observations or accepted world facts |
| Evidence | immutable source envelopes, exact spans, observations, acquisition metadata | ontology meaning or acceptance decisions |
| Semantic proposal | extracted mentions, identity hypotheses, candidate assertions, evaluator results | accepted canonical truth |
| Canonical state | accepted identities, assertions, events, bindings, dependency state, merge/split history | provider-specific indexes |
| Runtime projection | Cognee datasets, graph edges, vector indexes, caches, query materializations | irreplaceable evidence or canonical authority |

### 3.1 Primitive ownership

| Object | Primary ownership | Meaning |
| --- | --- | --- |
| `SemanticEntity` | domain/semantic | persistent identity that can recur across contexts |
| `Assertion` | semantic/canonical | contextualized proposition |
| `Event` | domain/semantic | temporally bounded occurrence |
| `Context` | semantic kernel | applicability and scope reference |
| `OntologyDefinition` | definition | immutable semantic contract |
| `RepresentationBinding` | semantic/canonical | activates a representation profile for an entity in context |
| `RepresentationProfile` | definition/governance | composable set of expressive rules |
| `ManifestationRule` | definition/governance | testable expressive constraint |
| `DependencyRule` | definition/governance | declares how dependencies are selected and propagated |
| `DependencyEdge` | derived semantic state | concrete dependency produced under a rule/version |
| `StalenessMarker` | derived semantic state | possible or evaluated impact, never falsity |
| `EvidenceEnvelope` / `EvidenceSpan` | evidence | immutable source and exact grounding |
| `Observation` | epistemic | what an observer or process recorded |
| `DerivationRecord` | universal provenance | why and how a derived record exists |
| `Snapshot` | derived state | reproducible resolved view, not primary evidence |
| `Branch` | runtime/state | overlay for proposals or scenarios |
| `AuthorityGrant` | governance | scoped permission to decide or mutate |

`Actor`, `Artifact`, `Concept`, `Brand`, `Organization`, and `Offering` are entity types, not
meta-model primitives. `Observation` belongs to the epistemic plane. Policies, rules, and
definitions belong to the definition/governance plane.

## 4. Meta-model

### 4.1 SemanticEntity

An object is a `SemanticEntity` when it:

1. has an identity that persists beyond one literal value or source span;
2. can recur across contexts or sources;
3. can have its own assertions, relationships, or history; and
4. benefits from independent reference, resolution, or lifecycle.

Minimum contract:

```yaml
entity:
  id: world://entity/<workspace-or-registry>/<stable-id>
  type_id: world://ontology/type/<type-id>
  identity_scope: workspace | shared
  lifecycle_status: proposed | accepted | deprecated | retired
  created_at: <UTC RFC3339>
  derivation_id: <required unless directly human-authored>
```

Names, descriptions, aliases, and labels are assertions or alias records, not identity.

### 4.2 Assertion

An `Assertion` is the canonical form of a proposition. A simple binary assertion may additionally
be projected as a graph edge, but the edge is never the only canonical record.

```yaml
assertion:
  id: world://assertion/<stable-id>
  subject_id: <entity-or-definition-id>
  predicate_id: <relationship-definition-id>
  object: {entity_id: <id>} # or a typed literal
  context_id: <context-id>
  perspective: intended | expressed | experienced | reported | observed | inferred | hypothesized
  epistemic_status: proposed | accepted | challenged | superseded | revoked
  valid_time: {from: <time-or-null>, to: <time-or-null>}
  known_time: {from: <time>, to: <time-or-null>}
  evidence_refs: [<evidence-span-id>]
  derivation_id: <derivation-id>
```

Qualifiers that change meaning stay on the assertion. They must not be flattened into an
unqualified direct edge.

### 4.3 Event

An `Event` is an occurrence bounded in time that may participate in causal, temporal, or change
relations. It is not a synonym for a stored change record: a real-world launch is an Event; the
acceptance of an assertion is a governance/change event.

### 4.4 Context — provisional encoding

The semantic requirement for Context is accepted; its physical encoding is provisional pending
the first fixtures. The current recommendation is an immutable, content-addressed record shared by
assertions, bindings, rules, manifestations, dependencies, and evaluations.

```yaml
context:
  id: world://context/sha256:<canonical-content-hash>
  brand_system_id: <id-or-null>
  portfolio_id: <id-or-null>
  brand_id: <id-or-null>
  offering_id: <id-or-null>
  audience_ids: [<id>]
  channel_ids: [<id>]
  artifact_type_ids: [<id>]
  locale: <BCP-47-or-null>
  campaign_or_occasion_ids: [<id>]
  branch_id: <id>
  valid_time: {from: <time-or-null>, to: <time-or-null>}
  dimensions: {}
```

Meaningful values such as markets, communities, cultures, channels, and audiences should normally
remain `SemanticEntity` references. The Context record scopes their applicability; it does not
replace them with anonymous strings.

Open decision C-01: validate whether content-addressed Context records provide adequate identity,
queryability, partial matching, and evolution behavior. Do not cement this encoding in canonical
storage until the fixture gate in section 18 passes.

### 4.5 OntologyDefinition

Every type, relationship, facet, and controlled vocabulary term has a stable immutable definition
ID, a release version, status, examples, and counterexamples. A module may add definitions and
subtypes but may never silently redefine an existing ID.

Additive compatible changes increment the ontology minor version. A semantic redefinition creates
a new ID and a declared migration; a breaking release increments the major version. Deprecation
never deletes historical meaning.

## 5. Classification constitution

Apply these tests in order:

1. Is it a temporally bounded occurrence? Classify it as an `Event`.
2. Is it a proposition that can be supported, contradicted, scoped, or revised? Classify it as an
   `Assertion`.
3. Does it have persistent identity and independent history? Classify it as a `SemanticEntity`.
4. Does it connect identities and have reusable semantics? Define a relationship and express each
   use as an Assertion.
5. Does it merely describe another identity without independent lifecycle? Use a typed value.
6. Is it a source record or act of noticing? Place it in Evidence/Observation, not the ontology.
7. Does it govern interpretation or mutation? Place it in Definition/Governance.

Borderline cases must be tested against competency questions. A new entity type is justified only
when independent identity, constraints, relationships, lifecycle, or queries cannot be represented
cleanly with an existing type plus a controlled `kind` value.

Examples:

| Candidate | Classification | Reason |
| --- | --- | --- |
| Acme | Brand entity | recurring identity with relationships and history |
| “trustworthy” in a paragraph | mention/evidence span | source occurrence, not canonical identity |
| Brand uses yellow | Assertion | proposition requiring scope and evidence |
| yellow | typed value or Color entity | entity only if color identity/relations matter |
| 2026 campaign launch | Event | bounded occurrence |
| visual consistency rule | ManifestationRule | definition/governance object |
| analyst noted confusion | Observation | epistemic record |

## 6. Portfolio-aware Brand topology

v0.1 is portfolio-aware from the beginning.

| Type | Constitutional meaning |
| --- | --- |
| `Organization` | organizational or legal actor |
| `Brand` | identity-bearing market entity |
| `Portfolio` | grouping and governance arrangement |
| `Offering` | commercial thing; `Product` and `Service` are initial subtypes |
| `Initiative` | temporary program, campaign, or change effort |
| `BrandSystem` | analytical boundary around a focal brand, not another kind of Brand |

Product-brand and sub-brand are ordinarily roles or relationships of `Brand`, not unrelated
ontological species. The initial relation vocabulary must explicitly distinguish `contains` /
`part_of`, `owns`, `governs`, `offers`, `targets` / `serves`, `participates_in`, `situated_in`,
and perception/experience relations.

The intended/normative system and the observed/perceived system are linked perspectives but are
never collapsed into one state.

## 7. Ontology modules

The initial module boundaries are:

```text
core
organization
offering
audience
market
brand-strategy
expression
artifact
experience
change-governance
```

The target is approximately 20–25 useful entity types in the first researched release, using
broad types plus controlled `kind` vocabularies. Specialization is driven by competency questions,
not a target count. The exact leaf inventory and module placement remain research-driven.

Each module must declare:

- namespace and semantic version;
- imported module versions;
- types, relationships, facets, and controlled terms it owns;
- compatibility and deprecation statements;
- competency questions it enables;
- positive, negative, and boundary fixtures; and
- migration rules for breaking changes.

## 8. Relationship and assertion contracts

The researched core should initially contain roughly 25–35 strong relations. Every relationship
definition must declare:

```yaml
relationship_definition:
  id: world://ontology/relation/<id>
  definition: <necessary meaning>
  family: structural | semantic | evidential | causal | temporal | strategic | expression
  subject_types: [<type-id>]
  object_types: [<type-id-or-literal>]
  inverse_id: <id-or-null>
  directionality: directed | undirected
  cardinality: <constraints-or-null>
  transitive: false
  symmetric: false
  functional: false
  contextual: true
  temporal_behavior: <contract>
  evidence_policy_id: <id>
  subproperty_of: <id-or-null>
  examples: []
  counterexamples: []
  ontology_version: <semver>
  status: candidate | accepted | deprecated
```

Logical properties default to false and must be explicitly opted into. Relation hierarchies must
remain shallow; no aggressive inference follows merely from `subproperty_of`.

Evidence thresholds are selected by a versioned policy and claim type, not hard-coded globally.
Weakly grounded proposals may exist, while identity, causal, and high-impact assertions require
stronger evidence to be accepted.

`supports`, `corroborates`, `contradicts`, and `retracts` primarily connect assertions and evidence.
Contradiction preserves both sides. Supersession expresses temporal replacement and must not be
used as a synonym for disagreement.

## 9. Causal discipline

`causes` is exceptional. It requires either an authoritative explicit causal claim or a supported
mechanism plus evidence meeting the relevant policy. Temporal sequence, correlation, similarity,
or model inference do not qualify.

The initial distinctions are:

- `enables`: makes an outcome possible;
- `constrains`: reduces feasible possibilities;
- `motivates`: expresses an actor-internal reason;
- `drives`: strong, sustained, directional causal contribution;
- `influences`: weaker or non-exclusive directional effect; and
- `precedes`: temporal ordering only.

Competing causal hypotheses remain separate proposed Assertions and share an
`alternative_set_id`. The system may preserve them indefinitely without forcing a winner.

## 10. Representation architecture

Representation must remain generic enough for a shared entity to retain one semantic identity
while its manifestations adapt across systems and contexts.

```text
SemanticEntity
    -> RepresentationBinding
    -> RepresentationProfile
    -> ManifestationRule
    -> evaluated Manifestation
```

### 10.1 RepresentationBinding

A binding says which profile governs an entity in a Context and how constrained the representation
is. Binding modes are `canonical`, `adaptive`, and `local`. Rule strength is separate and uses
`must`, `should`, `may`, or `must_not`.

### 10.2 RepresentationProfile

Profiles are immutable and versioned. They may extend or include other profiles as a directed
acyclic graph. Resolution proceeds from shared/canonical to portfolio, brand, offering, then
campaign/artifact. More specific rules may specialize broader rules but cannot violate protected
canonical invariants without explicit authority.

Conflicts resolve by specificity, authority, and explicit override permission. Equal-authority
conflicts remain unresolved; the evaluator must never silently select a winner.

### 10.3 Representation facets and rules

`RepresentationFacet` is an extensible registry. The core registry begins with:

```text
semantic
symbolic
visual
verbal
interaction
behavioral
motion
artifact
```

Rules use structured YAML/JSON rather than a programming or prose-only DSL:

```yaml
manifestation_rule:
  id: world://representation/rule/<id>
  version: <semver>
  selector: <structured selector>
  condition: <structured predicate>
  facet_id: world://representation/facet/<id>
  deontic: must | should | may | must_not
  constraint: <typed constraint>
  rationale: <text>
  validation_method: deterministic | model | hybrid | human
  severity: info | warning | error | critical
  override_policy_id: <id-or-null>
```

Each evaluated or generated Manifestation retains the represented entity, binding, profile version,
relevant rule versions, Context, inputs, model/tool identity, and generation/evaluation receipts.

### 10.4 Evaluation dimensions

Do not overload one status enum:

```text
Compliance: PASS | PARTIAL | FAIL | UNASSESSABLE
Freshness: CURRENT | POTENTIALLY_STALE | STALE
Findings: CONFLICT | MISSING_EVIDENCE | SEMANTIC_DRIFT | RULE_VIOLATION | ...
```

Semantic preservation combines deterministic invariants where possible, bounded model judgment
where necessary, and evidence. It must not collapse into a single ungrounded “brand fit” score.

## 11. Dependency and freshness architecture

Three dependency mechanisms are required:

1. instance-level: a particular upstream record affects a particular downstream record;
2. type-level: any entity/assertion of a selected type affects matching dependents; and
3. relation-derived: a semantic graph pattern implies possible dependency.

Rules use a structured selector AST/YAML with `entity_id`, `entity_type`, `relation_pattern`,
`scope`, and Context filters. Broad behavior belongs to a versioned `DependencyPolicy`; it must not
be hidden inside a relationship definition.

```yaml
dependency_rule:
  id: world://dependency/rule/<id>
  version: <semver>
  upstream_selector: <selector-ast>
  downstream_selector: <selector-ast>
  trigger_change_types: [<change-type>]
  scope: <context-selector>
  effect: potentially_stale | review_required | invalidate
  propagation: {max_depth: <n>, boundary_policy_id: <id>}
  authority_requirement_id: <id>
```

Materialization is hybrid: accepted, current, high-value concrete dependencies become
`DependencyEdge` records; broad type and relation-pattern dependencies are derived on demand and
may be cached with their rule/version receipt.

Precedence is explicit instance, scoped local, type, relation-derived, then portfolio/default.
Protected canonical invariants remain subject to authority even when a more specific rule exists.

Propagation uses a visited set, cycle detection, policy-defined depth and boundaries, and mandatory
review at risky crossings. Cross-workspace propagation occurs only through a shared entity or an
explicit cross-system rule, with affected-workspace authorization and an audit receipt.

Supported change types begin with:

```text
EntityRevision
AssertionAccepted / AssertionRevoked / AssertionSuperseded
IdentityMerge / IdentitySplit
RelationChanged
RepresentationChanged
PolicyChanged
EvidenceAuthorityChanged
OntologyChanged
```

Freshness lifecycle:

```text
current -> potentially_stale -> stale -> under_review -> reaffirmed | revised | retired
```

A dependency hit means the downstream may need review; it does not make the downstream false.
`potentially_stale` may be automatic. `stale` requires stronger evaluation under policy.

## 12. Identity, aliases, and shared entities

Identity is workspace-local by default. Genuinely shared identities may be promoted to a canonical
shared-entity registry and referenced from workspaces.

Cross-portfolio merge requires identity evidence: external IDs, defining characteristics,
provenance, and temporal compatibility. Similarity alone is insufficient; ambiguity remains
unresolved.

Aliases are first-class records with value, language, scope, valid time, and kind such as `name`,
`former_name`, `abbreviation`, or `translation`. An alias is evidence for resolution, not proof of
identity.

Merge and split operations require a human or explicitly authorized governance policy. They are
reversible and append-only: old identities are preserved with redirects and history. A workspace
may attach scoped assertions and representation bindings to a shared entity without mutating its
canonical identity.

## 13. Authority contract

Authority is a scoped capability, not a boolean attached independently to records. The system must
support at least ontology, identity, workspace, representation, and promotion authority.

```yaml
authority_grant:
  id: world://authority/grant/<id>
  principal_id: <human-agent-service-or-policy-id>
  capabilities: [propose | evaluate | accept | supersede | merge | split | override | promote]
  object_selectors: [<selector>]
  context_selector: <selector>
  valid_time: {from: <time>, to: <time-or-null>}
  issued_by: <authority-id>
  policy_version: <id>
```

Every accepted mutation records the authority used. A model may propose but may not promote an
ontology definition merely because its output is confident.

## 14. Universal derivation and provenance

Every non-source record must be explainable as:

```text
record
  <- produced from source records
  <- by operation, model, service, or human
  <- under definition/policy/operator versions
  <- at a recorded time
```

Minimum receipt:

```yaml
derivation:
  id: world://derivation/<id>
  output_ids: [<id>]
  input_ids: [<id>]
  operation_id: <id>
  actor_id: <id>
  model_or_tool: <identity-and-version-or-null>
  ontology_version: <version>
  policy_versions: [<id>]
  reasoning_operators: [<id-and-version>]
  occurred_at: <UTC RFC3339>
  result: proposed | accepted | rejected | partial | no_hit | held
```

Receipts must be sufficient to reconstruct lineage, not necessarily to reproduce stochastic model
text byte-for-byte.

## 15. Truth and applicability

An Assertion's acceptance status answers what the system currently accepts or preserves as a
hypothesis. Its Context answers where and when it applies. Neither substitutes for the other.

For example, “the brand uses a yellow accent” may be accepted while applying only to the corporate
brand after 2025 and excluding a product brand and long-form editorial. Conflicting contexts may
permit concurrent valid assertions; accidental overlap within an exclusive scope is a validation
error.

## 16. Time, versions, snapshots, and branches

- Store time in UTC RFC3339.
- Use half-open intervals `[from,to)`.
- Null bounds mean unknown or unbounded as explicitly indicated.
- Preserve source timezone and precision (`year`, `month`, `day`, `instant`, or `unknown`).
- Append corrections to knowledge history rather than rewriting it.

Use a new entity version when identity persists but intrinsic definition changes; an Assertion when
a proposition changes; an Event for the real occurrence; a profile version for manifestation logic;
and a Snapshot only for derived resolved state.

A Snapshot is selected by:

```text
ontology_version + branch + scope + valid_as_of + known_as_of
```

Its receipt is content-addressed and resolves active entity versions, assertions, profiles,
bindings, and policies without copying the whole database.

`main` represents accepted current reality. Scenario and experiment branches inherit from a base
snapshot and overlay proposed assertions or profile changes. Merge into `main` requires explicit
review and promotion. Historical state is reconstructed bitemporally rather than stored in special
history branches.

## 17. Research and population workflow

Research spans brand management and architecture, marketing strategy, consumer psychology and
identity, category and positioning theory, organizational identity, product/portfolio strategy,
service design and customer experience, semiotics, visual communication/design systems, narrative
and rhetoric, community/cultural studies, market structure, knowledge representation, causal
inference, temporal databases, and provenance.

Source authority tiers:

| Tier | Use |
| --- | --- |
| A | standards, foundational academic work, peer-reviewed syntheses, authoritative primary research |
| B | major scholarly books and established frameworks |
| C | high-quality professional frameworks and case material |
| D | exploratory practitioner material |
| E | examples only; not ontology authority |

v0.1 research is English-first, while every source and alias carries language metadata so the
ontology is multilingual from the beginning.

Population proceeds in this order:

```text
constitution
  -> research corpus with source metadata
  -> candidate definitions and relation contracts
  -> competency questions
  -> synthetic worlds and counterexamples
  -> evaluated ontology proposals
  -> steward promotion
  -> canonical fixture ingestion
  -> Cognee and other projections
```

Research agents produce proposals. Ontology evaluators produce analysis. Fixtures and competency
questions provide evidence. Only an authorized ontology steward promotes definitions.

## 18. Competency questions and fixtures

Before real Brand ingestion, every mandatory competency question must be representable by the
ontology and testable against synthetic fixtures. The suite must include:

- positive examples;
- negative and counterexamples;
- ambiguous identity and alias cases;
- intended versus observed divergence;
- scoped concurrent truth;
- representation inheritance and equal-authority conflict;
- instance-, type-, and relation-derived dependencies;
- bounded cycles and cross-workspace propagation;
- bitemporal corrections and snapshot reconstruction;
- competing causal hypotheses; and
- no-hit and insufficient-evidence behavior.

The Context encoding decision C-01 passes only if fixtures demonstrate deterministic canonical
hashing, exact and partial scope matching, reusable values, temporal behavior, and non-destructive
extension of optional dimensions.

## 19. Separate certification gates

### 19.1 Ontology certification v0.1

- 100% schema and definition validation;
- 100% of mandatory competency questions representable;
- 100% of critical fixture invariants pass;
- deterministic fixture reconstruction;
- zero unresolved high-severity identity or schema conflicts;
- every accepted relation has examples and counterexamples; and
- every breaking migration is declared.

### 19.2 Projection and retrieval certification v0.1

Each provider projection, including Cognee, is separately tested for:

- projection completeness;
- round-trip resolution to canonical IDs and evidence;
- graph path correctness;
- retrieval precision and bounded semantic recall;
- correct no-hit behavior;
- workspace isolation; and
- deterministic rebuild from canonical records.

An ontology release does not fail merely because one current Cognee retrieval strategy misses a
query. The projection fails its own certification.

## 20. Decision register

The original 50 decision clusters are classified as follows.

### 20.1 Provisionally settled by this constitution

1. small meta-model kernel;
2. deterministic classification rules;
5. extension rules;
6. explicit participation relations;
7. portfolio topology;
8. ontology evolution;
9. workspace-local versus shared identity;
10. cross-portfolio identity evidence;
11. alias records;
12. reversible authorized merge/split;
13. local augmentation of shared identity;
15. relationship contract;
16. shallow relationship hierarchy;
17. opt-in logical properties;
18. assertion-canonical n-ary semantics;
20. assertion/evidence conflict semantics;
21. strict causal gate;
23. competing causal hypotheses;
25. representation binding modes;
27. profile composition DAG;
28. representation inheritance;
29. representation conflict handling;
30. structured rule language;
31. manifestation receipts;
32. separate compliance/freshness/findings;
34. immutable representation versions;
35. structured dependency selectors;
36. hybrid dependency materialization;
37. separate DependencyPolicy;
38. change taxonomy;
39. dependency precedence;
40. bounded propagation;
41. freshness lifecycle;
42. authorized cross-boundary propagation;
43. time conventions;
44. version versus state distinctions;
45. context-scoped concurrent validity;
46. snapshot contract; and
47. branch semantics;
49. ontology promotion governance.

These are provisional until exercised by fixtures and code. A discovered contradiction must be
recorded and resolved through a new decision, not silently patched.

### 20.2 Research-driven

- #3 core entity inventory;
- #4 exact module vocabulary and boundaries;
- #14 core relationship inventory;
- #19 claim-sensitive evidence requirements;
- #22 Brand-domain nuances of causal vocabulary;
- #24 useful Context axes;
- #26 representation facet inventory;
- #33 semantic-preservation evaluation;
- #48 research corpus; and
- #50 competency coverage and thresholds.

### 20.3 Added cross-cutting contracts

- A. formal Context contract — semantic role accepted, encoding C-01 still open;
- B. formal Authority system — accepted provisionally;
- C. universal Derivation/provenance — accepted provisionally; and
- D. explicit truth/applicability distinction — accepted provisionally.

## 21. Migration from the current Brand prototype

`domains/brand/ontology/brand-system.yaml` version 1.0.0 is the current prototype and remains a
valid record of earlier work. Its eight broad component types and fourteen relationships must not
be silently redefined in place.

Before implementation changes canonical records:

1. inventory each current type and relation against this constitution;
2. classify it as retained, specialized, deprecated, or projection-only;
3. create new immutable IDs for semantic changes;
4. publish an explicit mapping and migration fixture;
5. reconstruct old fixtures under both versions; and
6. certify any Cognee cutover side-by-side.

The version number and namespace for the researched ontology release remain an implementation
decision. The constitution does not authorize an in-place rewrite of `1.0.0`.

## 22. Implementation sequence and gates

### Phase 0 — constitutional schemas

Define provider-neutral schemas for Context, OntologyDefinition, AuthorityGrant, DerivationRecord,
RepresentationBinding/Profile/Rule, DependencyRule/Edge, and StalenessMarker.

Gate: classification fixtures pass; C-01 is accepted or replaced; no schema imports Cognee.

### Phase 1 — research workspace

Create source metadata, claim proposal, competency-question, candidate-definition, and evaluator
artifacts with authority tiers and language metadata.

Gate: one source can be traced from evidence span to proposal and evaluator receipt without
promotion.

### Phase 2 — candidate ontology

Research the ten open clusters, propose the 20–25 entity types and 25–35 relations, and build
positive/counterexample fixtures.

Gate: ontology certification passes before real corpus ingestion.

### Phase 3 — canonical persistence

Add append-oriented storage, bitemporal resolution, identity/alias history, branches, snapshots,
representation resolution, and dependency materialization.

Gate: replay, concurrency, merge/split reversibility, and workspace isolation tests pass.

### Phase 4 — Cognee projection

Map accepted canonical records to Cognee datasets and graph/vector structures. Preserve canonical
IDs, assertion qualifiers, evidence references, and derivation receipts.

Gate: independent projection/retrieval certification passes and rebuild is deterministic.

### Phase 5 — agentic population

Use configured inference adapters for research proposals and evidence-grounded extraction. Keep
promotion authority outside the model and preserve `partial`, `no_hit`, `hold`, and `branch`.

Gate: end-to-end semantic continuity and source-grounding tests pass on a bounded corpus before
expansion.

## 23. Reasoning-operator evaluation record

This persisted design was routed through the following guardrails from
`reasoning/operators/index.yaml`:

| Operator | Version | Design-time evaluator result | Runtime work still required |
| --- | --- | --- | --- |
| `world://operator/guardrail/ontology-conflation` | 1 | pass: primitives, entity types, evidence, policy, and provider projection have explicit ownership | mapping and adapter-thinness tests |
| `world://operator/guardrail/boundary-conflation` | 1 | pass: five planes, typed handoffs, authority, and reversible projection boundaries are named | handoff completeness tests |
| `world://operator/guardrail/version-state-conflation` | 1 | pass: definitions, entities, assertions, events, profiles, snapshots, and branches have separate change semantics | replay and concurrent-validity tests |
| `world://operator/guardrail/identity-provenance-conflation` | 1 | pass: workspace/shared identity, aliases, evidence, merge/split history, and universal derivation are separate | identity-resolution and lineage proof tests |

The results are design evaluations, not runtime certification. Where implementation evidence does
not yet exist, this document explicitly records the remaining test rather than upgrading the result
to a proven runtime guarantee.

