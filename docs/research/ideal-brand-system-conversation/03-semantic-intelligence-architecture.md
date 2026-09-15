# Semantic and intelligence architecture

## 1. The universal model and the company instance

The system requires a reusable semantic skeleton whose structure is stable across companies while
its population is company-specific. Agents should not need a custom implementation for every
client; they should ask the same kinds of questions against a shared model. (`msg_0057`–`msg_0062`)

The archive proposes an **80–90% universal core plus scoped extensions**. A category may be populated,
unknown, not applicable or not connected. Absence must be semantically explicit rather than treated
as empty data.

The conversation never finalized one canonical top-level domain taxonomy. It produced overlapping
entity inventories and application views. That remains a formation task rather than an accepted
decision.

## 2. Candidate domain entities

Across the conversation, the Brand World was expected to represent at least the following families.

### Company and identity

Company, Brand, Purpose, Mission, Belief, Principle, Value, Worldview, Ambition, FounderIntent,
Identity, PointOfView, Expertise, Experience, Taste and StrategicThesis.

### Portfolio and offering

Product, Service, Feature, Capability, Technology, Protocol, Offer, Price, Category, UseCase,
ProductTruth, Benefit, DesiredOutcome and Proof.

### Customer and audience

Audience, ICP, Segment, Persona, Customer, BuyerSelf, IdentitySelf, SocialMediaSelf, Problem, Need,
Motivation, Objection, Trigger, Alternative, DecisionCriterion, CustomerLanguage, Perception,
Behavior and AudienceSignal.

### Social and cultural world

Community, SharedIdentity, Topic, Conversation, Creator, Media, Format, Meme, Trend, Subculture,
CulturalCode, AestheticCode, Ritual, StatusSignal, ParticipationMotive and CommunityRole.

### Market and competition

Market, Category, Competitor, Alternative, PositioningTerritory, CulturalTerritory, Trend,
MarketSignal, SearchDemand and Opportunity.

### Brand strategy and expression

Positioning, Promise, Differentiator, ValueProposition, Narrative, Message, Claim, VoiceRule,
VisualPrinciple, SymbolicConcept, VisualMetaphor, CulturalReference, ArchetypalRole,
MaterialQuality, SpatialMetaphor, MotionMetaphor, ContentTerritory and BrandRule.

### Work and intervention

Objective, Project, Task, Dependency, Campaign, Brief, Creative, Artifact, Element, Composition,
Decision, Recommendation, Action, Approval, Experiment, Variant, Result, Metric and Learning.

### Knowledge and governance

Source, Evidence, Observation, Pattern, Insight, Interpretation, Hypothesis, CandidateFact,
ConfirmedKnowledge, Contradiction, Unknown, Constraint, Permission, Authority, Provenance,
Confidence, ValidityInterval, Revision and Supersession.

These are candidates, not proof that every term deserves a first-class node. The final ontology must
separate referents, events, states, relations, claims, contexts and projections rather than reifying
every useful label. (`msg_0058`, `msg_0165`, `msg_0181`)

## 3. Candidate relationships

The system is relational rather than folder-centric. Recurrent relationships include:

```text
Audience         ─ experiences ─────→ Problem
Problem          ─ driven_by ───────→ Motivation
Product          ─ solves ──────────→ Problem
Claim            ─ supported_by ────→ Evidence
Positioning      ─ targets ─────────→ Audience
Positioning      ─ differentiates_from → Competitor
Narrative        ─ expresses ───────→ Positioning / Belief
Campaign         ─ communicates ────→ Message
ArtifactElement  ─ influenced_by ───→ Context factor
Evidence         ─ supports / contradicts → Hypothesis
Community        ─ centered_on ─────→ SharedIdentity
Audience         ─ participates_in ─→ Community
BrandPrinciple   ─ manifests_in ────→ Product / Artifact
Revision         ─ supersedes ──────→ Revision
Decision         ─ changes ─────────→ World state
```

Relations require meaning, direction, scope, time, provenance and, where relevant, strength or
inheritance policy. A graph edge is not self-explanatory.

## 4. Evidence and epistemic ladder

The conversation repeatedly rejects “source says X, therefore X is truth.” (`msg_0056`, `msg_0062`,
`msg_0137`, `msg_0153`, `msg_0159`)

The proposed ladder is:

```text
RAW SOURCE
  ↓
EVIDENCE / SOURCE SPAN
  ↓
OBSERVATION
  ↓
PATTERN
  ↓
INSIGHT / INTERPRETATION
  ↓
HYPOTHESIS
  ↓
PROPOSAL
  ↓
HUMAN DECISION / VALIDATION
  ↓
CONFIRMED KNOWLEDGE / STRATEGIC PRINCIPLE
```

Rejected, unresolved and superseded material remains represented. A record needs source and
derivation references, actor/authority, confidence or uncertainty, scope, valid time and recorded
time. Contradictory evidence is preserved rather than cleaned away.

The archive commonly used status terms such as `observation`, `hypothesis`, `proposed`, `confirmed`,
`rejected` and `superseded`. These are historical candidate labels; their exact semantics require a
formal contract before implementation.

## 5. Source-specific interpretation

Generic ingestion can parse and index files, but the company-specific intelligence must define what
different sources mean. (`msg_0159`, `msg_0161`, `msg_0165`)

| Source | Intended extraction focus |
| --- | --- |
| Customer interview / sales call | segment, problem, motivation, desired outcome, objection, trigger, alternative, exact language, product perception, evidence strength |
| Founder interview | beliefs, principles, identity, ambition, strategic intent, tensions, rejected directions |
| Website | public claims, positioning, audiences, messaging, offers, proof, visual/verbal expression |
| Competitor material | category, position, claims, audiences, benefits, proof, narrative and changes |
| CRM | commercial/customer signals, segment behavior, revenue and lifecycle facts |
| Analytics | observed behavior, performance changes, anomalies and experiment outcomes |
| Campaign results | performance evidence connected to audience, message, format, artifact and objective |
| Social/comments/DMs | audience questions, language, identity signals, cultural participation and content response |

Source processing may require custom segmentation rules, such as retaining a customer quote with its
question or separating a sales call by speaker and topic transition.

## 6. Entity resolution and truth formation

The knowledge-processing system must handle:

- mentions versus persistent entities;
- duplicates and aliases;
- overlapping or nested entities;
- source-specific perspectives;
- conflicts between public messaging, actual behavior and strategic intent;
- changing facts and future intentions;
- evidence weighting without false certainty;
- candidate interpretations that must stay branched;
- movement from proposal to approved brand knowledge.

For example, a website may say “for every company,” CRM revenue may be enterprise-heavy and a
founder may intend to move downmarket. These are different statements with different actors,
scopes and times—not one `primary_audience` value. (`msg_0137`, `msg_0165`)

## 7. Progressive abstraction

The world should not expose one flat graph or repeatedly summarize summaries. It should retain a
traceable abstraction ladder. (`msg_0167`)

```text
L5  company / strategic model
L4  positioning, principles, current strategic knowledge
L3  synthesized insights and patterns
L2  observations, claims, facts and measured results
L1  bounded evidence and source spans
L0  original source objects
```

An agent begins high and drills lower only when required for sufficiency, verification or conflict
resolution. Every abstraction remains linked back to its derivation.

## 8. Dimensional indexing

The same object may be indexed along many independent dimensions rather than placed in one folder.
(`msg_0183`)

Candidate dimensions include:

- brand, customer, product, market, competitor, social world and performance;
- identity, strategy, expression, artifact and governance;
- topic, audience problem, content territory, format, hook type, funnel role, offer and outcome;
- source type, time, status, confidence, authority and scope;
- task family and agent role;
- abstraction level and evidence depth.

The underlying knowledge is not physically duplicated into dozens of stores. Dimensions are typed
metadata, relations, indexes and retrieval policies over one connected world.

## 9. Context Compiler

The Context Compiler is one of the central pieces of IP. (`msg_0062`, `msg_0137`, `msg_0143`,
`msg_0167`, `msg_0183`, `msg_0185`)

```text
agent + task + objective + current state + authority
  ↓
select relevant dimensions
  ↓
start at suitable abstraction
  ↓
retrieve current scoped knowledge
  ↓
evaluate sufficiency and conflicts
  ↓
expand toward evidence when necessary
  ↓
apply permissions and route policies
  ↓
emit ContextPackage with references and omissions
```

It should combine three modes:

1. **Always present:** agent identity, task, essential company principles and hard constraints.
2. **Task-compiled:** the relevant current audience, product, position, evidence, history and
   decisions.
3. **On demand:** tools for targeted expansion into the world.

The compiler must record what an agent actually received so failures can be separated into bad
knowledge, bad context selection and bad reasoning.

## 10. Roads, routes and route policies

The closing primitive model clarifies the compiler. (`msg_0236`)

- Roads are persistent relations in the world.
- Routes are task-specific traversals over those roads.
- Gates determine whether a route may cross a boundary.
- Route policies evaluate recency, authority, confidence, status, relevance, contradiction,
  abstraction and scope.

Routes themselves can become reusable knowledge: a positioning route, campaign route, event route,
artifact route or product-extension route. Their effectiveness can be evaluated and versioned.

## 11. Specialist cognition

Different agents should differ in decision architecture, not merely personality or system prompt.
(`msg_0151`, `msg_0165`, `msg_0171`)

### Researcher

Question decomposition → search → source-quality evaluation → evidence extraction → contradiction
and gap search → synthesis → confidence check.

### Strategist

Objective → strategic tension → competing hypotheses → supporting and disconfirming evidence →
customer relevance → differentiation → trade-offs → critic → recommendation or escalation.

### Storyteller

Brand truth → audience tension → narrative territories → divergence → originality and brand-fit
evaluation → convergence → adaptable story system.

### Brand Guardian

Proposed output → identify claims and dependencies → compare current Brand World → inspect evidence,
voice and constraints → risk → allow, revise or escalate.

### Growth

Signal → anomaly analysis → competing causal hypotheses → evidence → expected impact → experiment
recommendation, with causality uncertainty retained.

### Director

Decompose objective, select specialists, manage dependencies and parallel work, request reviews,
prevent duplication, enforce approvals and decide completion. It manages rather than repeating each
specialist's reasoning.

## 12. Brand version control

The Brand World must preserve evolution rather than overwrite values. (`msg_0222`, `msg_0226`)

```text
main       current approved brand state
commit     accepted entity/relation change
diff       change between two states
branch     proposed strategy or simulated future
merge      approved strategic change
tag        important era or release
history    entity evolution
conflict   incompatible claims or decisions
stale      downstream dependency may no longer fit
```

Every entity can have revisions with evidence, effective intervals, reason for change and actor.
Dependency propagation asks: what remains compatible, what requires review, what conflicts and what
is unknown when an upstream fact changes?

Rates of change differ: purpose may remain stable for years, position for months, a campaign for
days and an artifact for hours. The model should not force them into one lifecycle.

## 13. Inheritance and manifestation

Brand expression is a contextual transformation of shared meaning into concrete choices.
(`msg_0228`)

Candidate inheritance policies:

- `INHERIT_STRICT` — meaning must be preserved;
- `INHERIT_ADAPTIVE` — meaning persists while expression varies;
- `INHERIT_OPTIONAL` — available when context supports it;
- `INHERIT_WEAK` — background influence;
- `OVERRIDE_ALLOWED` — child identity may supersede it;
- `DO_NOT_INHERIT` — explicit separation.

A Manifestation Policy can contain a semantic kernel, invariants, desired qualities, prohibited
framings, channel-specific translations and version history. It emits instructions rather than a
finished artifact.

```text
shared essence
  + child identity
  + product truth
  + audience
  + medium
  + objective
  + cultural context
  + current state
  ↓
manifestation package
```

This applies across language, symbolism, color behavior, typography, imagery, spatial arrangement,
motion, interaction, product behavior, community and event design.

## 14. Canonical shared entity representation

A crucial distinction emerged between shared essence and a recurring shared entity. (`msg_0230`,
`msg_0232`)

- A shared essence such as empowerment may adapt across products.
- A shared entity such as Bitcoin, a protocol, a recurring agent concept or a symbolic object may
  require one recognizable cross-product semantic and expressive identity.

The entity may own canonical terms, semantic associations, symbolism, geometry, iconography, color
behavior, motion, diagram grammar, copy patterns, examples and anti-examples. Local context decides
prominence and composition but does not independently reinvent the entity.

Candidate `representation_mode` values are `canonical`, `adaptive` and `product_specific`.

## 15. Artifact Intelligence Layer

An artifact is a composition, not one generation. (`msg_0223`, `msg_0224`)

The system must represent:

- global factors: objective, audience, brand state, campaign, channel and emotional direction;
- element-specific factors: headline tension, visual grammar, proof, CTA friction;
- relational factors: complementarity, hierarchy, contrast and semantic interaction;
- medium factors: format, pacing, density and affordances;
- situational factors: culture, competitor activity, fatigue, launch stage and recency.

The Artifact Composition Graph includes the artifact, its elements, each element's context and the
composition qualities joining them: hierarchy, contrast, rhythm, tension, density, pacing, balance,
repetition, surprise, narrative arc and emotional direction.

Generation proceeds in stages:

```text
objective
→ artifact strategy
→ composition direction
→ element responsibilities
→ element-specific context compilation
→ element generation
→ composition review
→ Brand Guardian
→ audience simulation
→ revision
→ approval
```

Element quality and whole-composition quality are evaluated separately. Two strong components can
still produce a poor whole.

## 16. Simulation and strategic pre-testing

Simulation is structured counterfactual reasoning over evidence-backed audience and world models,
not a digital oracle. (`msg_0198`–`msg_0203`)

Proposed maturity levels:

1. **Audience panel:** 5–20 evidence-grounded archetypes react independently.
2. **Population:** a distribution of motivations, awareness, identity, price sensitivity and media
   habits produces response clusters.
3. **Community/social:** actors see and influence one another over several rounds.
4. **Calibrated strategic world:** simulated outcomes are compared with real experiments so the
   system learns its biases and competence boundaries.

Outputs distinguish synthetic response, prediction/hypothesis and actual result. The system should
ask “for whom, why and what trade-off?” rather than declaring one universal winner.

## 17. Agentic Content Lab

The Content Lab responds to cheap generation by making selection and judgment the product.
(`msg_0204`, `msg_0205`)

It evaluates strategic fit, audience relevance, brand fit, originality, clarity, credibility,
social value, commercial value, community fit, risk and portfolio contribution. It generates
deliberate variation, conducts internal tournaments, tests interpretation across audience models,
and brings humans only the few ideas that deserve attention.

Human approval should not be the garbage-collection step for hundreds of generations. Internal
evaluation must narrow the field first.

## 18. Feedback and learning

The system learns through a controlled ladder. (`msg_0129`, `msg_0137`, `msg_0153`, `msg_0165`)

- reaction/like: weak preference or retrieval signal;
- comment: contextual information;
- correction: stronger evidence of an error;
- explicit approval/rejection: governance decision;
- external outcome: evidence relevant to hypotheses;
- repeated calibrated outcomes: potential model update.

A like is not truth. A winning campaign is not automatic causal proof. Every recommendation should
retain context, reasoning version, evidence, human decision, action and outcome so later evaluation
is possible.

