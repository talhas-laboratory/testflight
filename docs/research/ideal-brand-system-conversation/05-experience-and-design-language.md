# Experience and design language

## Experience principle

The human should not feel like an operator of an agent framework. They should feel that an
intelligent organization is continuously observing, thinking, creating and bringing consequential
decisions to them. (`msg_0032`–`msg_0038`)

The primary interaction evolved from a conventional dashboard and “Marketing Director” chat into a
private intelligence feed inhabited by recognizable specialist agents. (`msg_0128`, `msg_0129`)

## Interaction model

The early three-mode model remains useful:

- **Tell:** state an objective or desired change;
- **Review:** inspect work and decisions requiring human judgment;
- **Ask:** interrogate the system about evidence, reasoning, history or results.

The later feed model adds continuous discovery: the system proactively surfaces a small number of
important observations, hypotheses, recommendations, questions, artifacts and results.

## Feed as the primary interface

> The feed is the interface to the company's intelligence.

It is not an engagement-maximizing infinite scroll. Its purpose is to maximize important decisions
made with minimal noise. Ranking should combine importance, relevance, novelty, urgency, confidence
and required action rather than likes or predicted dwell time. A good day may contain five to seven
items. (`msg_0129`, `msg_0187`)

Example sequence:

```text
Researcher
Customer concern X is increasing. Evidence attached.
  ↓
Strategist
This may indicate a positioning problem. Here are two hypotheses.
  ↓
Brand Guardian
Direction B conflicts with an approved product truth.
  ↓
Human
Discusses, adjusts and approves a bounded experiment.
  ↓
Growth
Reports actual outcome and remaining uncertainty.
```

## Typed feed objects

The feed should display domain objects, not raw agent chatter or runtime logs.

| Type | Purpose |
| --- | --- |
| Observation | What was detected without interpretation |
| External signal | Relevant market, customer, competitor or cultural development |
| Pattern / Insight | A supported synthesis across observations |
| Hypothesis | A contestable explanation or strategic possibility |
| Recommendation | A proposed decision or action with reasons and trade-offs |
| Question | A genuine human input or authority requirement |
| Creation / Artifact | A strategy, narrative, brief, concept or finished object |
| Result | What occurred after action or experiment |
| Learning | A carefully promoted update to future reasoning |
| Approval | A gate requiring explicit decision |

Each type should have a stable information contract and a distinctive but restrained presentation.

## Interaction semantics

User actions are inputs to the intelligence system, so their meaning must be explicit.

- **Like:** weak positive preference or retrieval signal; never canonical truth.
- **Dislike:** weak negative signal; prompts examination rather than deletion.
- **Comment:** adds context or opens discussion.
- **Correct:** asserts that a representation is wrong and creates a high-priority review path.
- **Adjust:** modifies a proposal while preserving its lineage.
- **Approve:** authorizes a decision, state transition or bounded action.
- **Reject:** closes or branches a proposal while retaining history.
- **Save:** marks durable relevance without approving the content.
- **Ask:** opens an agent conversation anchored to the object.
- **Share/tag:** brings another human or agent into the scoped work.

The interface should not make ambiguous reactions perform consequential mutations.

## Progressive disclosure

The feed is a high-level entry point. Every claim or recommendation can be opened into its
structured world object, then traced downward:

```text
feed statement
→ recommendation / insight
→ hypotheses and alternatives
→ supporting and contradicting patterns
→ observations
→ bounded evidence
→ original source
```

The same interface should allow lateral exploration of entities, relations, dependencies, current
state and history. This makes epistemic rigor visible only when wanted, avoiding an overwhelming
research-database experience.

## Product surfaces

The archive converged on the following surfaces. (`msg_0129`, `msg_0179`)

| Surface | User question |
| --- | --- |
| Feed | What matters now? |
| Core / World | What does the system currently understand and approve about the company? |
| Agents | Who is working, what are they doing, and what can they do? |
| Work | Which projects, tasks, experiments, dependencies and approvals are active? |
| Library | What research, source material, artifacts and assets exist? |
| History | What changed, why, and what depended on the previous state? |
| Evidence | Why does the system believe this? |
| Conversation | Discuss this object or decision with a specialist. |
| Setup / Governance | Configure sources, permissions, autonomy, agents and world extensions. |

The earlier Brand Room, Campaign Room, Creative Studio and Insights views can be expressed through
these later surfaces rather than maintained as separate dashboard silos.

## Approval experience

Consequential items come to the human; the human does not hunt for them. An approval object should
show:

- proposed change or action;
- objective and expected effect;
- evidence and reasoning;
- alternatives and trade-offs;
- affected world entities and artifacts;
- confidence and unresolved questions;
- requested authority and limits;
- approve, adjust, discuss, reject or defer actions.

The system can create and evaluate many internal possibilities, but only work that survives its
internal quality gates should consume human attention.

## External interaction channels

The web product owns structured review, world exploration, history, evidence and configuration.
Existing channels such as Slack, email, mobile notification or messaging can carry concise alerts,
questions and approvals. The custom interface should not be hosted inside an individual agent
computer; client-facing state belongs in a stable product application. (`msg_0033`–`msg_0038`)

## Visual system

The core visual rule is:

> **Avatar = expression. UI = container. Motion = meaning.**

The surrounding interface should be quiet, highly legible, spacious, restrained and meticulous:

- neutral or softly tonal surfaces;
- disciplined typography and hierarchy;
- minimal decorative color;
- calm transitions;
- dense detail available through disclosure rather than visible by default;
- accessible interaction states and explicit text labels;
- no generic enterprise dashboard aesthetic;
- no mascot clutter.

Expressive color and movement belong primarily to agents. (`msg_0132`–`msg_0135`)

## Agent character system

The agents are a coherent species of simple abstract creatures rather than robots or explicit
figurative mascots. (`msg_0120`–`msg_0127`)

Shared family traits:

- simple rounded or blob-like anatomy;
- strong silhouette;
- minimal facial implication;
- flat or lightly dimensional graphic treatment;
- common geometry, material and motion principles;
- personality expressed through behavior more than detailed anatomy;
- role-specific form, accent, motif and tempo;
- playful enough to feel alive, serious enough to support trust.

The two uploaded visual references are absent as binaries from the bundle. Therefore this textual
direction is recoverable, but the precise visual corrections made against those images are not.

## Candidate visible agents

- Researcher/Scout: cool blue, observant, scanning, gathering and mapping;
- Strategist: warm amber, calm, arranging and comparing;
- Storyteller: violet/pink, weaving, flowing and shaping meaning;
- Creator: energetic red or warm accent, assembling and externalizing;
- Growth: green, sensing signals, trajectories and change;
- Brand Guardian: graphite/neutral, stable, symmetrical and protective;
- Director: restrained black/white or subtle iridescence, coordinating and presenting.

These colors were design proposals rather than accepted tokens.

## Agent motion language

Avatars are stateful interface components driven by real backend state, not random decorative loops.

Candidate states:

```text
idle
thinking
searching / scanning
reading
comparing
connecting
synthesizing
creating / assembling
reviewing / validating
uncertain
waiting for input
presenting
executing / transmitting
success
error / blocked
```

Each state should have UX meaning and a textual explanation such as “analyzing 14 sources.” Motion
must never be the sole accessibility channel.

## Avatar implementation direction

The archive considered SVG + Motion and Rive. (`msg_0206`–`msg_0218`)

- Use parametric SVG/React shapes for lightweight, adjustable anatomy and responsive rendering.
- Use transform-based animation for most states; reserve path morphing for meaningful organic
  changes.
- Use Motion for ordinary product transitions and simple avatar movement.
- Use Rive when the character requires a sophisticated authored state machine or layered animation.
- Avoid GIF, PNG sequence and video as primary runtime formats.
- Do not begin with full 3D.
- Prove one excellent character and roughly six essential states before designing the full family.

The hard part is craft: a small set of motions must remain legible and pleasant after repeated use.

## Backend-to-avatar contract

```text
runtime event
→ domain event
→ semantic phase
→ avatar state
```

For example, a LangGraph source-quality node may produce `research.evaluating_sources`, which drives
the Researcher comparison animation. The LLM does not directly command animation.

## Frontend implementation candidates

The historical recommendation was: (`msg_0179`)

- Next.js + React + TypeScript for the shell;
- Radix/shadcn-style primitives for accessible, non-distinctive controls;
- TanStack Query for durable product state;
- AG-UI for agent/runtime-to-frontend events;
- assistant-ui primitives for direct conversations, not for the feed;
- Motion for normal UI transitions;
- Rive or SVG/React for characters;
- custom product components for feed objects, evidence, approvals, history and world exploration.

CopilotKit and generative UI were not rejected categorically, but the product should retain a stable
interaction grammar rather than let agents invent the main interface.

## Initial experience slice

The first end-to-end interface should prove:

1. neutral product shell and three feed types: Insight, Recommendation and Result;
2. one Researcher avatar with real execution states;
3. anchored conversation about a feed object;
4. recommendation → discuss → adjust → approve;
5. evidence and provenance drill-down;
6. minimal Core/World, Agents, Work, Library and History views.

The product hypothesis is not merely whether the UI is attractive. It is whether interacting with a
company through a living feed of specialist intelligences is materially clearer and more useful
than a dashboard or generic chatbot.

