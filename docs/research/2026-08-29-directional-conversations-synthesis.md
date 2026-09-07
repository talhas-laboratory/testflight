# Directional conversations: categorized synthesis and Testflight perspective

Status: source-grounded synthesis; proposals are not architectural decisions  
Date: 2026-08-29  
Scope: four supplied ChatGPT conversations, interpreted against the repository state on this date

## 1. Purpose and reading rules

This document preserves and organizes the connected line of thought developed across four
conversations. It distinguishes:

- what the user directly proposed or reported;
- interpretations and recommendations introduced by ChatGPT;
- market claims reported by those conversations but not independently re-verified here;
- repository facts observable in Testflight; and
- proposals that could guide future work but have not been accepted through an ADR or promotion
  gate.

The conversations are evidence of a direction, not canonical truth. Their source text remains the
authority for what was said. This synthesis is a derived interpretation and should remain
revisable.

## 2. Source register

| ID | Conversation | Main subject | Source anchor |
| --- | --- | --- | --- |
| C1 | `READ_Marketing Ontology Problem` | Marketing as semantic representation plus causal intervention; limits of KPI-led optimization | supplied file `1-2026-08-29_chatgpt-read-marketing-ontology-problem.md`, messages 1–8; [shared conversation](https://chatgpt.com/share/6a92cb9c-9944-83ed-862b-755544d81e6d) |
| C2 | `READ_Goal Driven Discovery Style` | Goal-directed exploration, artifact-centered intelligence, personal taste, and movie-night wedge | supplied file `2-2026-08-29_chatgpt-read-goal-driven-discovery-style.md`, messages 1–14; [shared conversation](https://chatgpt.com/share/6a92cb68-dab0-83eb-8d1c-1be0417413d6) |
| C3 | `INTEGRATE_Integrate Directional Thoughts` | Semantic translation architecture, modular ontologies, Cognee boundary, and behavioral specification | supplied file `3-2026-08-29_chatgpt-integrate-integrate-directional-thoughts.md`, messages 1–17; [shared conversation](https://chatgpt.com/share/6a92cbe3-f8c4-83eb-821f-f6d227242b15) |
| C4 | `READ_Forward Deployed Engineers` | Forward deployment, marketing/brand intelligence, company taste, community sensing, founder onboarding, and personal extension | supplied file `4-2026-08-29_chatgpt-read-forward-deployed-engineers.md`, messages 1–52; [shared conversation](https://chatgpt.com/share/6a92cbc0-26a8-83eb-895c-7cb275db650c) |

Market sizes, prices, competitors, platform capabilities, and survey findings below are recorded as
claims reported in C1/C3/C4. Their embedded citations were not independently checked during this
synthesis and should be refreshed before they drive a commercial decision.

## 3. Integrated thesis

The four conversations converge on a single general capability:

> Reliably translate free human expression into a versioned, evidence-bearing semantic model;
> compile the relevant part of that model for a goal; configure transformations through it; and
> preserve the consequences in inspectable artifacts and learning history.

The clearest end-to-end form is:

```text
free expression and external evidence
                ↓
immutable source and provenance
                ↓
meaning-preserving interpretation
                ↓
several plausible semantic configurations
                ↓
selective, high-information clarification
                ↓
versioned and scoped world state
                ↓
goal + task + operator-specific context compilation
                ↓
configured transformation or evaluation
                ↓
artifact / recommendation / authorized action
                ↓
outcome evidence, decision history, and model revision
```

This is better understood as a **semantic translation and control system** than as a note-taking
tool, generic agent, static knowledge graph, brand-guideline RAG system, or social-listening
dashboard.

Three applications sit on top of the same proposed engine:

1. **Company/Brand:** represent a company's identity, product philosophy, customer understanding,
   distinction, taste, evidence, and decisions; use them to guide product, brand, marketing, and
   market interpretation.
2. **Personal:** maintain a local-first, user-owned, contextual and revisable representation of a
   person's goals, taste, beliefs, projects, preferences, and decision history.
3. **Group/Market:** compare private or company models with selectively exposed taste facets or
   external community signals to find overlap, tension, drift, and opportunities.

The company and personal applications should not be collapsed into one ontology. They may share a
semantic kernel, provenance model, compiler interface, and operator contract while retaining
different domain modules, authority rules, privacy boundaries, and evaluation cases.

## 4. Categorized synthesis

### 4.1 Human working model: goal-directed discovery

User-originated observations:

- A clear goal creates orientation, while discovering the route provides energy (C2 M1).
- Awareness becomes energizing when it is related to a goal and anchored in an inner world rather
  than left as mental drift (C2 M5).
- Exploration should feel like an engaging walk. Execution should preserve some discovery rather
  than become purely mechanical (C2 M7).
- Side projects should function as sources of energy, not merely as additional obligations (C2
  M9).

Derived design interpretation:

```text
motivation ≈ clear destination
           + an open but navigable route
           + awareness of current position
           + visible discovery and progress
```

The resulting interaction principle is:

> **Maintain orientation without prematurely collapsing exploration.**

A suitable system should keep the destination, current position, recent discoveries, unresolved
branches, and plausible next directions perceptible. It should behave more like an evolving map or
navigator than a rigid task manager. This is a user-experience hypothesis, not a universal claim
about motivation.

### 4.2 Intelligence is a transformation; its durable output is an artifact

The user rejected the implication that intelligence must be represented as one bounded `Agent`
(C2 M3). The proposed alternative is:

```text
compiled context
+ active associations
+ transformation operators
+ current input
        ↓
artifact
```

Under this view:

- the **intelligence substrate** is a network of concepts, evidence, memories, tools, models, and
  operators;
- an **activation/configuration** selects the relevant part for a goal;
- a **transformation** compares, interprets, synthesizes, simulates, evaluates, or translates;
- an **artifact** externalizes the result; and
- **lineage** records the source, context, transformation, model/tool, and prior artifacts that
  produced it.

An agent remains useful as an operational boundary when persistent identity, continuity,
permissions, responsibility, or tool authority are needed. It should not automatically become the
fundamental semantic unit.

### 4.3 Ontology, state, operators, and artifacts are different layers

C3 developed the following distinction:

| Layer | Role | Must not silently become |
| --- | --- | --- |
| Source/evidence | What was expressed, observed, or acquired | Accepted truth |
| Ontology/definitions | The kinds of things and relations the system can represent | Current belief or runtime state |
| World state | Scoped, versioned claims, goals, preferences, hypotheses, and decisions | A timeless profile |
| Operators | Contracts for transformations and checks | Generic prompts without evaluation |
| Context compiler | Selects the smallest relevant state for a task and goal | Retrieval treated as a conclusion |
| Artifact/action | Externalized result or authorized operation | Evidence about its own correctness |

The central formula proposed across C2–C4 is:

```text
artifact = transformation(input | compiled context, active ontology, goal, state, evidence)
```

The ontology provides stable semantic distinctions. State says which claims, goals, preferences,
and hypotheses currently apply. Operators define what transformations are permitted and required.
The compiler selects the task-relevant configuration. These roles are complementary, not
interchangeable.

### 4.4 The product capability is meaning-preserving translation

C3 frames the system as an automated translation pipeline between representational layers:

```text
human thought = source language
semantic representation = intermediate representation
operator and context compilation = compiler passes
artifact/tool instruction = target representation
```

The reliability requirement is not that every thought maps to one predefined label. A successful
translation must preserve the operational consequences the user intended while retaining:

- source and speaker authority;
- explicit content versus inferred implication;
- context and scope;
- uncertainty and competing interpretations;
- contradictions and rejected alternatives;
- temporal change;
- provenance and derivation; and
- the ability to ask or hold when ambiguity materially changes downstream behavior.

One source span may legitimately propose several semantic objects. For example, “side projects
should produce energy rather than feel like obligations” could be a preference, principle,
decision rule, or project constraint. The system should not force a choice unless the distinction
matters to later behavior.

### 4.5 Candidate ontology configurations and guided discrimination

The conversations explicitly reject both a single universal schema and immediate commitment to one
interpretation (C3 M4; C4 M49–M52).

The proposed mechanism is:

1. interpret the same corpus through several bounded semantic operators;
2. assemble several plausible structural configurations;
3. preserve shared evidence and the differences between configurations;
4. ask short, high-information questions that discriminate between structures;
5. allow `confirmed`, `likely`, `possible`, `contradicted`, and `unresolved` states;
6. permit multiple configurations to remain active when they answer different questions; and
7. revise configurations through later evidence and observed decisions.

For a company, possible dominant configurations might be product-philosophy-centered,
taste-centered, customer-tension-centered, or category-position-centered. For a person, freedom,
creative autonomy, or resistance to externally imposed structure might be alternative organizing
explanations. These are hypotheses about relations, not rival fixed personality labels.

The questionnaire should compare interpretations rather than ask the user to model the domain from
scratch. “Does craftsmanship matter because it increases agency, does agency matter because the
crafted experience is valuable, or are they independent?” is more informative than “What are your
values?”

### 4.6 Founder/personal onboarding: observe before interrogating

The proposed first experience is a roughly seven-day, low-structure capture period (C4 M47–M52):

> Write or speak whatever comes to mind about the company or yourself. Do not organize it or decide
> whether it matters.

The exact duration is an assistant recommendation, not a validated optimum. Its intent is to allow
thoughts to surface in several contexts without turning onboarding into a long questionnaire.

After capture:

```text
express
  → interpret with several operators
  → find repeated structures, tensions, and absences
  → propose configurations
  → ask only discriminating questions
  → publish a provisional model
```

The source corpus remains immutable. The first result should be labeled something like `Company
Model v0.1`, not “the truth about your brand.” Founder belief, customer evidence, public community
signals, market facts, and system inference remain different perspectives.

### 4.7 Marketing: representation upstream, intervention downstream

C1's initial thesis was that marketing is partly an ontology problem:

- it represents brand, customer, market, category, alternatives, needs, capabilities, benefits,
  symbols, meanings, and their relationships;
- strategy selects what should change;
- campaigns, offers, channels, timing, and experiences intervene causally; and
- experiments and KPIs provide outcome evidence.

The corrected formulation after research in C1 is important:

> Modern marketing has powerful measurement and optimization infrastructure, while the
> representation of the market, customer, and brand that determines what should be optimized is
> comparatively less formalized.

C1 reported strong evidence for a short-term/performance bias, but not for the stronger claims that
A/B testing dominates marketing or that an “ontology layer” is a measured industry category.
Therefore:

- “marketing is KPI-driven” is a broad but supported tendency in the conversation's research;
- “marketing is dominated by A/B testing” was explicitly retracted;
- “marketing has an ontology problem” remains a useful product/architecture hypothesis, not an
  established empirical fact; and
- KPIs and experiments should update semantic hypotheses rather than be positioned as their
  opposite.

The intended learning loop is:

```text
semantic model
    → strategic hypothesis
    → intervention/experiment
    → outcome evidence
    → scoped model update
```

### 4.8 Company distinction and taste

C4 proposes that shared foundation models and production tools reduce the scarcity of competent
execution. The resulting strategic hypothesis is that coherent judgment and distinction become
more important, especially in crowded AI categories (C4 M33–M36).

`Taste` is defined here more broadly than aesthetics:

> A learned capacity to distinguish what could be done from what should be done by this particular
> company.

It can govern:

- which products and features belong;
- what is deliberately excluded;
- the preferred relationship between human and automation;
- interaction and visual grammar;
- positioning, narrative, and customer fit;
- acceptable compromises; and
- which category conventions to adopt, adapt, or reject.

The commercially legible promise is **distinction**; taste is the proposed mechanism. The system
should not merely retrieve taste descriptions. It should evaluate proposed outputs against
evidence-bearing principles and explain alignment, tension, or insufficient evidence.

Taste should be learned through decisions as well as statements:

```text
options proposed
    → selection/rejection
    → reason captured or cautiously inferred
    → decision principle proposed
    → later choices test or refine it
```

This makes decision history a valuable semantic asset. It does not justify diagnosing a latent
preference without evidence or user review.

### 4.9 Brand and community taste: observation, interpretation, and drift

C4 narrows community sensing into a marketing workflow rather than a personal-memory feature
(C4 M39–M46).

The proposed product is an **observant interpretive engine of community taste**:

```text
public community signals
+ reviews/support/interviews
+ market and behavioral evidence
        ↓
multi-lens interpretation
        ↓
probabilistic community model
        ↕
versioned brand model
        ↓
alignment / tension / drift / opportunity hypotheses
        ↓
experiments and learning
```

Possible lenses include needs, frustrations, language, narratives, aesthetics, identity and status
signals, category perception, competitor associations, polarization, novelty, saturation, and idea
diffusion. The system should compare explanations rather than reduce the corpus to sentiment.

Two constraints are essential:

1. public social data is a biased observation surface, not “the consumer”; and
2. community movement is evidence for a decision, not an instruction to follow the trend.

The most distinctive output is **drift detection** between `BrandTaste(t)` and
`CommunityTaste(t)`, with sources, affected subcommunities, uncertainty, and alternative strategic
responses. Deliberate divergence may be as valid as convergence.

### 4.10 Portable personal taste and local ownership

C2's movie-night idea supplies a playful wedge for a larger personal system:

```text
private taste representation
    → selectively exposed facet
    → context-specific intelligence
    → recommendation or creative artifact
```

Movie-night consensus is inherently invitational: several people contribute only the relevant
movie-taste facet, the system finds a defensible overlap, and each participant retains a reusable
profile. The longer-term hypothesis is a portable taste layer for restaurants, travel, music,
design, gifts, and other choices.

The proposed business principle is:

> **Own the context; rent the intelligence.**

Storage, identity, ontology formats, provenance, permissions, and portability would be local-first
and ideally open. Paid value comes from useful transformations over user-owned information, not
from charging a person to retain their own representation.

The trust claim should be structural rather than personalized: users should not need the continued
goodwill, leadership, product strategy, or business model of one model provider to preserve their
context. Providers should receive scoped, purpose-bound, time-bound access to the smallest relevant
semantic facet.

This personal application is directionally compatible with the general engine, but it introduces
substantially stricter privacy, consent, deletion, portability, and permission requirements than
the current Brand workspace.

### 4.11 Forward deployment and commercial sequencing

C4 uses the Forward Deployed Engineer model as the commercial and product-development mechanism:

```text
customer reality
  → formulate the real problem
  → instantiate a customer-specific world
  → connect data and tools
  → build/configure a workflow
  → deploy and observe
  → extract repeated primitives into the platform
```

The general substrate stays reusable, while customer data, semantic models, integrations,
workflows, and applications are scoped to each deployment. Forward-deployed work may reveal
missing platform primitives; it is not an absolute prohibition on changing the core.

The reported commercial recommendation evolved as follows:

| Horizon | Proposed offer |
| --- | --- |
| Initial architecture idea | General customizable marketing/brand operating platform |
| First commercial wedge | Forward-deployed, outcome-specific marketing intelligence for a narrow ICP |
| Alternative brand-intelligence wedge | Company distinction/taste and evolving GTM intelligence for funded AI startups |
| Later platform | Reusable company world model, context compiler, operators, evaluators, integrations, and applications |

For DTC brands, C4 initially favored performance creative intelligence: “What should we test next,
and why?” For AI startups, it favored continuously translating a changing product, customer, and
category into a distinctive position and GTM system. It explicitly recommends testing one ICP and
one workflow for the first customers rather than launching both.

The conversations reported adjacent price validation for approximately €3k deployment plus
€1k/month, but did not validate willingness to buy this exact offer. The strongest practical
recommendation was to let a business earn the right to replace a career through paying customers,
retention, a repeatable workflow, and repeatable acquisition—not through market-size reasoning
alone.

### 4.12 Cognee and infrastructure boundaries

C3 concluded that Cognee is a plausible graph/vector memory and retrieval component, not the owner
of semantic meaning or epistemic history.

Proposed ownership:

```text
Testflight-owned
  semantic definitions
  evidence and provenance
  candidate interpretations
  acceptance and state transitions
  ontology configurations
  operator definitions
  context compilation
  evaluation and decision policy

replaceable infrastructure
  ingestion assistance
  graph/vector materialization
  retrieval indexes
  dataset isolation
  ontology grounding
  provider-specific memory APIs
```

This is substantially aligned with Testflight's current architecture: canonical semantics and
evidence stay provider-neutral; Cognee receives a discardable, rebuildable projection.

### 4.13 The correct specification level

C3 identifies **observable semantic behavior** as the most useful boundary between UX intention and
implementation.

```text
human intention
    → semantic behavioral contract
    → evaluation scenario
    → technical implementation
```

For example, “my thought should influence later decisions” is too vague. A testable behavioral
contract is:

> When a new product principle is relevant to a later feature evaluation, the system includes it.
> If it conflicts with an existing principle, neither silently overwrites the other. Both sources
> and the tension remain visible, and clarification occurs only when the distinction changes the
> decision.

Evaluation scenarios should test downstream consequences rather than insist on one internal graph
shape. This keeps the semantics precise while allowing competing technical representations.

## 5. Decision and evidence status

| Direction | Origin/status in the conversations | Current status here |
| --- | --- | --- |
| Goal-directed discovery should guide the experience | User report plus assistant interpretation, C2 | Product hypothesis requiring user testing |
| Artifacts and transformations are more fundamental than agents | User conceptual preference, C2 | Strong semantic design direction; operational agents remain valid boundaries |
| Ontology + state + operators + compiler form the control layer | Jointly developed, C3/C4 | Strong architectural thesis |
| Several ontology configurations may coexist | Jointly developed, C3/C4 | Required behavior for ambiguity; implementation not yet specified end to end |
| Seven-day free-expression onboarding | Assistant recommendation accepted directionally by the user, C4 | Experiment proposal; duration unvalidated |
| Marketing's representation layer is comparatively under-formalized | Corrected assistant research claim, C1 | Plausible and partially supported; not an accepted project fact |
| Company taste can preserve distinction | User direction plus assistant theory, C4 | Strategic/product hypothesis |
| Community-taste drift is a valuable workflow | User direction plus assistant elaboration, C4 | Product hypothesis; data access and validity remain open |
| Local-first personal ontology should be user-owned | User direction, C4 | Separate application thesis with major privacy work |
| Movie night is a viral wedge; charge for intelligence | User direction plus assistant business-model elaboration, C2 | Consumer-product hypothesis |
| Service-first, platform-second | Assistant commercial recommendation, C4 | Sensible go-to-market hypothesis, not a repository architecture decision |
| Cognee is infrastructure, not canonical meaning | Assistant assessment, C3 | Already accepted in Testflight ADR 0003/0004 |
| Semantic behavior and evaluation scenarios should guide engineering | Assistant recommendation, C3 | Strongly aligned with Testflight's operator/evaluation approach |

## 6. Perspective of the Testflight project

### 6.1 What Testflight is today

Testflight explicitly starts as a **polyglot integration laboratory**, not a finished product. Its
purpose is to evaluate replaceable upstream systems behind locally owned contracts and promote
successful experiments into reusable packages or services.

The current repository already contains a meaningful Brand vertical slice:

| Conversation concept | Existing Testflight capability | Maturity/limit |
| --- | --- | --- |
| Preserve raw evidence | `EvidenceEnvelope`, exact `EvidenceSpan`, append-oriented SQLite repository | Implemented canonical boundary; real Brand ingestion still gated |
| Keep mention separate from entity | Occurrence-first extraction and explicit mention/entity guardrails | Implemented initial extraction contract; corpus-level consolidation remains later work |
| Provider-neutral semantic kernel | `SemanticEntity`, `Assertion`, `Event`, provisional `Context`, definitions, identity, time, governance, derivation | Implemented and tested as constitutional contracts |
| Brand ontology | Versioned Brand ontology/policies and a research constitution | Prototype `brand-system.yaml` remains a migration source; researched vocabulary is not fully promoted |
| Epistemic state | Perspective, status, evidence, contradiction, valid/known time, separate score dimensions | Strong contracts exist; complete evolution workflow is not yet a product loop |
| Immutable lineage | `DerivationRecord` and operator/version references | Implemented contract and validation |
| Canonical state separate from memory index | SQLite canonical repository plus rebuildable Cognee projection | Accepted architecture in ADR 0003/0004 |
| Scoped project worlds | Brand workspace templates, isolated research workspaces, dataset routing, certification probes | Implemented for Brand research and Nike staging |
| Compile task-specific context | Provider-neutral context-intelligence engine, workflow planner, packet contract, Cordis adapter | Implemented current slice for Brand workflows; not a universal semantic compiler |
| Preserve retrieval boundaries | Selected/retrieved/mentioned/used distinctions and observable journal | Designed/implemented in current context-intelligence work |
| Make the world inspectable | Read-only Brand World Explorer with deterministic snapshot and planned context | Initial canonical/planned views implemented; live retrieval/trace adapters remain future work |
| Reasoning operators | Versioned guardrail catalog with hold/branch/ask outcomes and evaluators | Implemented controls; the domain-transformational operators imagined in the conversations are not yet a complete runtime family |

The conversations therefore do not require Testflight to reverse its architecture. They largely
explain **why the existing boundaries matter** and suggest the next user-facing and semantic
capability to test.

### 6.2 The most important correspondence

The conversations' proposed compiler pipeline maps closely to Testflight:

```text
CONVERSATION IDEA                 TESTFLIGHT TODAY

immutable thought/source   →      evidence envelopes and spans
semantic proposals         →      occurrences, assertion proposals, epistemic status
ontology/state             →      semantic kernel + Brand ontology + accepted assertions
memory/index               →      rebuildable Cognee projection
task-specific compilation  →      context-intelligence engine and workflow profiles
configured transformation  →      reasoning instructions + guardrail operators
artifact                   →      Brand artifacts / agent output boundary
inspectability             →      derivation receipts, journals, Brand World Explorer
```

The existing project already embodies the key correction from C3: **Cognee is not the system's
meaning**. It is replaceable retrieval infrastructure below canonical evidence and semantics.

### 6.3 What is genuinely missing

The central missing capability is a tested **free-expression → competing semantic
configurations → guided discrimination → downstream consequence** loop.

More specifically:

1. **Capture contract and corpus:** no productized founder/personal free-expression intake,
   episode identity, or cross-entry capture experience exists.
2. **Interpretive operator family:** current operators mainly prevent conflations. The repository
   does not yet have a complete, evaluated family for goal, principle, preference, taste, tension,
   rejection, ambition, product philosophy, customer model, and decision-rule extraction.
3. **Configuration object:** there is no explicit canonical/proposal model for several modular
   ontology configurations that share evidence but differ in hierarchy or explanatory relations.
4. **Discrimination policy:** there is no question-selection mechanism that estimates which
   clarification best separates live configurations.
5. **Semantic transition workflow:** primitives for time, status, contradiction, supersession, and
   derivation exist, but the end-to-end rules for refining, branching, accepting, and retiring an
   interpretation are not yet a user-facing workflow.
6. **Continuity evaluations:** the project needs fixtures that test whether meaning survives from
   raw thought through interpretation, compilation, generation, review, and revision.
7. **Outcome feedback:** Brand post-publication learning is represented directionally, but a closed
   intervention → evidence → claim-update loop is not implemented as a general system.
8. **Taste and decision history:** neither company taste nor personal taste is yet a promoted
   domain module with behavioral tests.
9. **Community observation:** no connector-neutral public-signal evidence model, sampling policy,
   bias model, multi-lens comparison, or drift evaluator exists.
10. **Personal sovereignty:** local-first storage, semantic permissions, consent, selective
    disclosure, portability, deletion, and provider access grants require a separate security and
    privacy architecture.
11. **Commercial application:** the repository intentionally has no finished product, ICP,
    onboarding, billing, or forward-deployment playbook.

### 6.4 Recommended project framing

The cleanest interpretation is to keep Testflight as the integration laboratory and treat the
conversation-derived vision as a set of vertical experiments over shared contracts:

```text
TESTFLIGHT LAB
│
├── shared semantic substrate
│   evidence, identity, assertions, time, context, provenance, authority
│
├── interpretation and configuration runtime
│   proposal operators, alternative structures, discrimination, transitions
│
├── context and operator compiler
│   goal/task selection, smallest relevant configuration, receipts, evaluation
│
├── Brand/company vertical
│   founder model, distinction/taste, community sensing, marketing decisions
│
└── Personal vertical
    local-first world model, permissions, portable taste, personal decisions
```

This preserves modular boundaries:

- shared packages own only cross-domain semantics;
- Brand-specific types stay in `domains/brand` and `testflight-brand`;
- personal semantics should become a separate domain/package rather than extending Brand types;
- Cognee and future stores remain adapters;
- capture, questionnaire, and explorer interfaces remain apps;
- market/community sources use replaceable connectors with registered upstreams; and
- domain operators remain versioned contracts with independent evaluations.

### 6.5 Best next proof

The highest-value next proof is not another broad ontology or a full marketing platform. It is a
bounded semantic-continuity experiment using the supplied conversations or a small founder corpus:

1. preserve 20–50 source episodes with exact spans and speaker authority;
2. define a minimal set of interpretive behaviors, initially `Goal`, `Principle`, `Preference`,
   `Hypothesis`, `Tension`, `DecisionRule`, and `Evidence`;
3. produce at least two genuinely different configurations where the evidence permits them;
4. generate one discriminating clarification question and preserve `unresolved` when appropriate;
5. compile the relevant configuration for a later decision or generative task;
6. verify that the output reflects the intended consequence without converting an inference into
   a user-owned fact; and
7. record correction or acceptance as new evidence rather than overwriting history.

A useful first evaluation scenario already exists in C3:

```text
SOURCE PRINCIPLE
“Exploring ideas should itself feel rewarding; Thought Tube should not become another
productivity tool.”

LATER TASK
“Should we add weekly goal streaks?”

EXPECTED BEHAVIOR
- retrieve the relevant source-backed principle;
- identify the potential tension with productivity mechanics;
- distinguish tension from an automatic prohibition;
- explain which interpretation/configuration produced the concern;
- ask only if the unresolved distinction materially changes the recommendation;
- preserve the resulting decision and rationale as new evidence.
```

This thin slice would test the core differentiator—meaning-preserving translation into later
behavior—while reusing the evidence, semantic, workspace, compiler, evaluator, and Explorer
boundaries already present.

## 7. Questions intentionally left open

- Is the initial user a founder/company, the repository owner personally, or a paying marketing
  customer?
- Which first workflow creates enough value to justify repeated use: founder-model onboarding,
  creative intelligence, category/community radar, or general decision alignment?
- Which semantic distinctions must be canonical and which may remain behavioral/internal?
- Can competing configurations be represented as branches over shared assertions, or do they need
  a distinct configuration model?
- What observation is sufficient to infer a decision principle, and when must the system ask?
- How should structural explanatory fit be evaluated without collapsing it into one confidence
  score?
- What downstream consequence demonstrates that a company or personal model is useful?
- Which parts of community taste can be supported by public data without overstating population
  validity?
- What belongs in the open local-first substrate, and what paid intelligence can sit above it?
- Does the personal application belong in Testflight now, or only after the Brand translation loop
  has produced reusable primitives?

These are valid branches. None needs to be silently resolved to begin the bounded proof above.

## 8. Derivation and evaluation record

### Operator record

| Operator | Version | Use in this artifact |
| --- | --- | --- |
| `world://operator/guardrail/mention-entity-conflation` | 1 | Kept user statements, assistant interpretations, company/product concepts, and repo entities distinct; anchored claims to conversation/message ranges. |
| `world://operator/guardrail/evidence-truth-conflation` | 1 | Labeled reported research, user direction, assistant recommendation, repository fact, and synthesis inference separately. |
| `world://operator/guardrail/boundary-conflation` | 1 | Separated evidence, definitions, semantic proposals, canonical state, runtime projections, artifacts, and authorization. |
| `world://operator/guardrail/ontology-conflation` | 1 | Kept ontology types, current state, storage records, provider projections, and UI/product labels from being treated as equivalents. |
| `world://operator/guardrail/evaluation-schema` | 1 | Evaluated source coverage, invariant preservation, semantic fidelity, and project usefulness as separate dimensions. |

Configuration: system/module abstraction; working depth; conceptual, strategic, and operational
lenses; grounded evidence; uncertainty policy `branch`; mutation `proposal_only`.

### Evaluator results

| Dimension | Result | Notes |
| --- | --- | --- |
| Source/span grounding | Pass | Every material conversation-derived section cites C1–C4 message ranges; exact source files and shared URLs are registered. |
| Speaker/authority preservation | Pass | User proposals and experiences are not relabeled as independently established facts; assistant recommendations remain recommendations. |
| Evidence/status accuracy | Pass | Embedded market research is explicitly reported and not presented as re-verified; repository statements were checked against current files. |
| Contradiction/branch retention | Pass | A/B-testing overstatement, taste/community caveats, multiple configurations, ICP alternatives, and open questions remain visible. |
| Plane and boundary coverage | Pass | Source, proposal, ontology, state, runtime projection, artifact, and action boundaries are explicit. |
| Ontology/storage separation | Pass | Semantic kernel, Brand definitions, SQLite canonical state, Cognee projection, and UI are treated as separate layers. |
| Semantic coverage | Pass with limitation | All 91 source messages were reviewed; repeated elaboration was consolidated by concept rather than reproduced verbatim. |
| Usefulness for Testflight | Pass | Existing capabilities, missing contracts, modular placement, and one bounded next proof are identified. |
| Independent empirical verification | Not performed | Commercial and external technology claims need fresh source verification before investment or market decisions. |

Overall status: **grounded synthesis, proposal-only project interpretation**.
