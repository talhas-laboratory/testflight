# Technical and agent architecture

## Architectural rule

The product owns meaning, intelligence and interaction semantics. Infrastructure remains behind
small adapters and can be replaced. No external framework should become the ontology of the
product. (`msg_0141`, `msg_0151`, `msg_0153`, `msg_0165`)

## Conceptual layers

```text
1. MEMORY          What does the company know?
2. INTERPRETATION  What does the information mean?
3. CONTEXT         What matters for this task?
4. COGNITION       How should the specialist reason?
5. ACTION          What should happen in the external world?
6. EXPERIENCE      How does the human understand and govern it?
```

The earlier four-layer model—Context, Agents, Execution, Interaction—remains a useful simplified
view. Its two hard rules were: **agents do not own truth; the context system does**, and **agents
decide while execution tools act**. (`msg_0040`)

## Reference architecture from the conversation

```text
SOURCES
files · web · interviews · social · CRM · analytics · product · market
  │
  ├── integration/auth/sync adapter
  ▼
INGESTION + SOURCE-SPECIFIC INTERPRETATION
  │
  ├── semantic knowledge plane
  └── analytical data plane
  │
  ▼
BOX API / WORLD INTERFACE
  │
  ▼
DIMENSIONAL INDEX + CONTEXT COMPILER
  │
  ▼
SPECIALIST REASONING
  │
  ▼
AGENT RUNTIME + WORK LEDGER
  │
  ├── domain tools / MCP / external agents
  ├── approvals and permission gates
  └── domain event translation
  │
  ▼
FEED · EXPLORER · CONVERSATION · WORK · HISTORY
  │
  ▼
EXTERNAL ACTIONS / ARTIFACTS / EXPERIMENTS
  │
  └── results return as evidence
```

## What the product must own

The conversation explicitly treats the following as proprietary or strategically differentiating.
(`msg_0181`)

- Brand/company ontology and semantic contracts;
- source interpretation, extraction and entity-resolution algorithms;
- evidence, truth, approval, contradiction and temporal semantics;
- progressive abstraction and dimensional indexing;
- Box/world API and domain-specific query/write operations;
- Context Compiler, route library and route policies;
- specialist reasoning architectures and domain evaluators;
- Work Model extensions and Director coordination logic;
- feedback and learning semantics;
- domain event vocabulary;
- feed ranking, post types and interaction semantics;
- evidence and world explorer;
- client configuration and onboarding process;
- product visual language, agent identities and motion semantics;
- Artifact Intelligence, Manifestation Engine and simulation logic.

## What should be reused

- file parsers and generic document loaders;
- relational, graph and vector storage primitives;
- embeddings and model hosting;
- OAuth, token refresh and provider sync plumbing;
- workflow checkpointing and generic agent loops;
- sandbox/computer execution;
- authentication and baseline tenant infrastructure;
- frontend accessibility primitives, streaming protocols and animation runtimes;
- tracing, experiment storage and generic retrieval metrics.

## Knowledge and analytical planes

The archive corrects an early temptation to put everything in one graph. (`msg_0169`)

### Semantic knowledge plane

Documents, evidence, observations, entities, relations, identity, positioning, customer insight,
market interpretation, claims, decisions and history. Cognee was recommended as a candidate
infrastructure layer because it offered relational provenance, graph/vector retrieval, custom typed
objects, ingestion and dataset isolation. It should sit behind a `Box` interface.

### Analytical plane

Spend, events, CRM tables, conversion, revenue, funnels, cohorts, experiment results and numeric
metrics belong in an analytical engine. DuckDB was proposed for an early system, with larger
warehouses considered later if real scale requires them.

The Context Compiler joins semantic and quantitative evidence for a task.

## Temporal representation

Graphiti was proposed as an optional temporal/evolving-fact subsystem, not the canonical truth
database. Important change should be represented as versioned facts/relations with validity windows
rather than mutable node properties. It should not be introduced until the base system proves a
real temporal limitation. (`msg_0153`, `msg_0157`, `msg_0165`)

## Stable Box/world interface

Agents and product logic should not import storage-provider types. Candidate operations include:

```text
read
  get(entity)
  related(entity, relation, scope)
  search(query, scope, abstraction)
  evidence(record)
  history(entity)

context
  compile(agent, task, authority)

write
  observe(signal)
  propose(change)
  confirm(change)
  reject(change)
  recordDecision(decision)

feedback
  react(object, signal)
```

Writes need authority, validation, derivation and idempotency; the concise historical interface is a
product boundary, not sufficient implementation detail.

## Agent contract

Every agent is a small typed worker, not a free-form chatbot. (`msg_0042`)

```text
Agent
├── identity and role
├── goal and responsibilities
├── readable and writable scopes
├── allowed tools and actions
├── expected input/output schemas
├── reasoning procedure
├── quality validators
├── permission and approval policy
├── escalation/stopping rules
└── presentation/personality profile
```

The normal loop is:

```text
read compiled context
→ reason
→ propose plan or result
→ request authorized action
→ validate outcome
→ write evidence/result back through domain boundary
```

## Agent roster

The roster evolved with product scope. The full candidate organization includes:

- **Director:** orchestrates objectives, work and gates;
- **Researcher / Scout:** observes customers, competitors, markets and culture;
- **Strategist:** frames tensions, develops and challenges choices;
- **Brand:** maintains approved identity and positioning knowledge;
- **Storyteller:** develops narrative systems and finds story opportunities;
- **Creative / Creator:** develops artifacts from approved strategies;
- **Growth:** connects work to quantitative evidence and experiments;
- **Brand Guardian:** validates claims, identity, permissions and coherence.

Execution should remain a tool layer rather than an unconstrained “Executor Agent.” For the
social-first product the visible roster was simplified to Scout, Strategist, Creator and Growth;
hidden specialists can remain behind them. (`msg_0042`, `msg_0121`, `msg_0187`)

## Personality, cognition and knowledge

The hybrid runtime model separates three concerns. (`msg_0151`)

```text
PERSONALITY  What kind of actor am I?
COGNITION    How do I approach this problem?
KNOWLEDGE    What do I know in this task and authority scope?
```

The historical recommendation was:

- DeepSeek Harness as a replaceable candidate for persistent identity, sessions, tools, permissions,
  approvals and runtime events;
- LangGraph for selected specialist cognitive procedures;
- Brand World plus Context Compiler for knowledge.

This stack was a prototype recommendation, not an irreversible choice. Harness was considered
architecturally aligned but too immature to be a hard dependency without an adapter.

## Framework ownership boundaries

If Harness and LangGraph are combined:

- Harness owns agent lifecycle, session history, external tools, credentials, approval and audit;
- LangGraph owns temporary internal reasoning branches, loops, critics and decision procedures;
- LangGraph persistence is disabled initially to avoid two sources of truth;
- long-running reasoning may later receive an explicit child thread ID under the parent agent run;
- human approval exists in one layer only;
- real-world tool execution exists in one layer only;
- the outer agent shell should stay thin to avoid redundant nested model calls.

The recommended experiment was a single Strategist or Researcher flow proving context transfer,
tool bridging, event-to-avatar mapping, approval, durability, client isolation and actual quality
gain over a strong prompt. (`msg_0151`)

## Work Model and ledger

Agents coordinate through durable structured work and shared world references, not unbounded chat.
(`msg_0042`, `msg_0173`, `msg_0177`)

### Generic objects

```text
Task
Artifact / Result
Event
Dependency
Status
Agent
Context
```

### Domain extensions

```text
Evidence
Observation
Insight
Hypothesis
Recommendation
Decision
Experiment
BrandChange
Campaign
```

A Task includes objective, requester, assignee, context references, dependencies, expected output,
priority and status. A Result includes producer, structured output, evidence, assumptions,
uncertainty and source references. The append-oriented Work Ledger in a product database powers
dependencies, feed events, audit and replay.

Knowledge remains in the Brand World. Agents exchange references to durable insights and artifacts
instead of copying large prose messages between sessions.

## Director coordination

The Director decomposes goals, assigns tasks, runs independent work in parallel, waits on
dependencies, requests specialist or guardian review, detects duplication and escalates. It is a
manager rather than a super-agent that recomputes every specialist's result.

## Protocol boundaries

The historical architecture distinguishes three communication boundaries. (`msg_0177`,
`msg_0179`)

| Boundary | Candidate protocol |
| --- | --- |
| Agent ↔ tool/context | MCP |
| Internal agent ↔ agent | native runtime plus Work Model |
| External independent agent ↔ system | A2A |
| Agent/runtime ↔ frontend | AG-UI plus custom domain events |

The Work Model's generic pieces should map cleanly to A2A concepts such as AgentCard, Task, Message,
Artifact and context ID, while internal agents do not need to communicate over A2A.

CrewAI, AutoGen, Microsoft Agent Framework and AGNTCY/SLIM were treated as alternative stacks or
future scaling infrastructure, not additions to Harness + LangGraph. Adding overlapping agent
frameworks was rejected.

## Domain event layer

Low-level runtime events should be translated into stable product meaning:

```text
model/tool/runtime events
  ↓
research.searching
research.evaluating_sources
insight.created
hypothesis.proposed
recommendation.created
approval.required
decision.approved
experiment.completed
```

The frontend never needs to know which LangGraph node or Harness plugin produced the event. The same
translation drives feed posts, work state, notifications and avatar motion.

## Model policy

The system should express model roles such as `cheap_extraction`, `deep_strategy`, `classification`
or `creative_exploration`; a model gateway maps them to providers and supplies fallback, budgets,
rate limits and cost tracking. LiteLLM was the historical candidate. Models remain replaceable.
(`msg_0048`, `msg_0169`)

## Integrations

Nango was proposed for OAuth, credentials, syncing, retries, rate limits and tenant-specific external
API access. The product should own only the semantic mapping from provider objects into Brand World
and analytical objects. (`msg_0169`)

Start with a few reliable connections rather than a broad fragile catalog. Candidate sources
included website/files, CRM, analytics, social, Slack/Notion/Drive, ads, CMS, call transcripts and
customer research.

## Persistent computer / sandbox

The original Cloudflare Computer research produced a durable insight: an agent benefits from a
persistent workspace while compute can be elastic underneath it. But the conversation later removed
“a computer per client” from the V1 critical path. (`msg_0004`, `msg_0026`, `msg_0137`)

Use on-demand sandbox/computer execution when tasks require code, browser work, heavy file
transformation, scraping, native binaries or artifact production. Normal product and knowledge state
belongs in durable databases and object storage.

Cloudflare Computer was preview-only in the historical research. Daytona and E2B were considered
more immediately practical alternatives, with any provider hidden behind an execution interface.

## Observability and evaluation

Langfuse was proposed for traces, prompts, datasets, human scoring and experiments. Ragas was
proposed for retrieval/context precision, recall, faithfulness and noise evaluation. DSPy was
explicitly postponed until real cases and trustworthy scoring data exist. (`msg_0169`, `msg_0171`)

The development loop is:

```text
real task
→ context + reasoning + action trace
→ human correction and outcome
→ evaluation dataset
→ retrieval and domain metrics
→ revised algorithm
→ controlled comparison
```

Important evaluation dimensions include extraction accuracy, evidence grounding, entity resolution,
context sufficiency, strategic relevance, differentiation, originality, brand coherence, decision
quality, hallucination, latency and cost.

## Supporting infrastructure decisions

- Trigger.dev: postpone until non-agent durable background jobs accumulate.
- OpenFGA: postpone until resource-level authorization exceeds tenant/role/tool scopes.
- Infisical: postpone until infrastructure-secret complexity warrants it; customer OAuth remains in
  the integration layer.
- PostHog: use for the product's own behavior analytics and experiments, not as part of the Brand
  World.
- Mem0: do not add initially because it duplicates agent-session and company-memory systems; it may
  later hold only human-specific conversational preferences.
- OpenClaw: optional replaceable channel/runtime adapter, not a required per-client foundation.
  (`msg_0045`–`msg_0048`, `msg_0169`, `msg_0175`)

## Security, privacy and autonomy

The conversation treated security and EU privacy as product concerns rather than infrastructure
marketing claims. (`msg_0027`, `msg_0028`, `msg_0137`)

Required semantics include:

- tenant and dataset isolation;
- role, agent, resource and tool scopes;
- data classification and provider restrictions;
- auditable source, context, model, tool and action history;
- explicit approval for consequential decisions and actions;
- idempotent execution and failure recovery;
- credential isolation and bounded access;
- retention/deletion policies and data-processing agreements;
- model/provider privacy configuration appropriate to the client.

The historical privacy model classified data before it entered a general-purpose agent workspace:

- **Green:** public brand material, public competitor research, generated assets, strategy and
  aggregated/anonymized performance data;
- **Yellow:** CRM records, identities, customer feedback, sales conversations and individually linked
  analytics, requiring explicit processing, access and retention rules;
- **Red:** health, sensitive HR, financial-account and other special-category or large raw personal
  datasets, excluded from a general-purpose workspace by default.

Data minimization was preferred to copying entire source systems into agent storage: query only the
records required, process them in a bounded environment and delete temporary personal data.
Compliance must account for every processor in the chain—models, generation providers, analytics,
CRM and execution targets—not merely the hosting vendor. GDPR compliance and EU data residency are
separate requirements. (`msg_0028`)

Autonomy progresses from draft-only to approval-required to bounded guardrails. “Fully autonomous”
is not a default; permission is specific to action, budget, channel and risk.

## Historical implementation sequence

The archive recommended proving a narrow loop before the complete platform:

1. one company and manually configured Brand World;
2. website/document ingestion with provenance;
3. Researcher, Strategist and Brand Guardian;
4. Context Compiler and typed recommendations;
5. feed, discussion, adjustment and explicit approval;
6. evidence drill-down;
7. one real agent/runtime bridge;
8. a few reliable integrations;
9. decision/outcome instrumentation;
10. expand into Storytelling, Content Lab, simulation, execution and richer manifestation only after
    the core proves useful.

The final architecture is broad; the first deployed application must remain narrow.
