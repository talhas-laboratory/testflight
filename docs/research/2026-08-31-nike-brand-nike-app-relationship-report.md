# Connecting Nike Brand and Nike App

**Status:** research-backed semantic proposal; no ontology or workspace records changed  
**Date:** 2026-08-31  
**Question:** What is the cleanest way to connect the Nike Brand entity to the entity currently described as the “Nike Members app”?

The separate [research and reasoning audit](2026-08-31-nike-brand-nike-app-research-reasoning-audit.md) records the hypotheses, exact search route, accepted and rejected evidence, decision checkpoints, and reproducible queries behind this conclusion.

## Executive conclusion

The clean solution is not to make the app a component of Nike in every possible sense, nor to duplicate it as both an `Offering` and an `Experience`.

Keep **one canonical entity: `Nike App`**, with `Offering` as its primary semantic type. Then express its different roles with contextual assertions:

```text
Nike --offers--> Nike App

Nike App --participates_in--> Nike Membership

Nike App --experienced_through--> Personalized app guidance
```

The first assertion is the clean direct connection and can be represented with Testflight’s existing `offers` relationship. The other assertions explain why that connection matters without changing the app’s identity.

If Testflight needs to answer the more specific question, “Through which owned digital touchpoint is Nike encountered?”, add a narrowly defined relationship such as:

```text
Nike App --touchpoint_for--> Nike
```

That assertion must be scoped to the current Nike Membership digital context. It should not replace `offers`; it describes a different role.

The phrase **“Nike Members app” should initially be treated as a mention or possible alias for `Nike App`, not as proof of a second entity**. The current Nike evidence describes `Nike App`, `Nike Membership`, and `Nike Members` as three different things: an offering, a membership layer, and an audience respectively.

## Why the connection felt difficult

The two endpoints are not difficult to identify. The difficulty comes from trying to make one graph edge carry several meanings at once:

- Nike makes the app available.
- The app participates in the Nike Membership ecosystem.
- The app is a digital surface through which people encounter Nike.
- The app delivers personalized product, content, advice, and experience discovery.
- The app has a visual and interaction expression governed by Nike and Membership-specific representation rules.

These are compatible propositions, but they are not synonyms. A single vague edge such as `has_component` or `related_to` hides the useful distinctions. Conversely, turning each role into a separate Nike App entity destroys identity continuity.

The library repeatedly points to the same resolution: **one persistent identity, multiple typed and scoped relations**.

## What already exists in Testflight

The Nike workspace already contains most of the required pieces:

- `ENT-NIKE-OF-005` is **Nike Membership**, modeled as an `offering` that connects access, rewards, experiences, guidance, and services.
- `ENT-NIKE-OF-006` is **Nike App**, modeled as an `offering` providing personalized commerce and content.
- `ENT-NIKE-XP-004` is **Personalized app guidance**, modeled separately as an `experience`.
- `ENT-NIKE-EN-017` is **Nike Members**, modeled as an audience/environment rather than an app.
- `CTX-NIKE-DIGITAL-MEMBERSHIP-CURRENT` scopes Nike Membership and its connected channels, including Nike App.

The relationship inventory already says:

```text
Nike --offers--> Nike Membership
Nike --experienced_through--> Nike digital commerce
Nike Membership --experienced_through--> Member product access and rewards
Nike App --experienced_through--> Personalized app guidance
```

What is absent is the simplest direct assertion:

```text
Nike --offers--> Nike App
```

That relation is already legal under the ontology. `offers` accepts a `brand-system` source and an `offering` target. No new entity type or architectural mechanism is required.

## Recommended semantic topology

### Layer 1: the direct factual connection

Use the existing relation:

```yaml
assertion:
  subject_id: world://brand/nike
  predicate_id: offers
  object_id: ENT-NIKE-OF-006
  context_id: CTX-NIKE-DIGITAL-MEMBERSHIP-CURRENT
  perspective: intended
  status: proposed
  evidence_refs: [EVID-NIKE-011]
```

Meaning: Nike makes Nike App available as an offering.

This is the smallest correct answer to the immediate modeling problem.

### Layer 2: the ecosystem role

Add the constitutionally anticipated `participates_in` relationship:

```yaml
assertion:
  subject_id: ENT-NIKE-OF-006
  predicate_id: participates_in
  object_id: ENT-NIKE-OF-005
  context_id: CTX-NIKE-DIGITAL-MEMBERSHIP-CURRENT
  perspective: intended
  status: proposed
  evidence_refs: [EVID-NIKE-010, EVID-NIKE-011]
```

Meaning: Nike App is one participating offering/surface within Nike Membership. This is more accurate than saying the app *is* Membership.

The exact relationship contract still needs a small definition and a fixture before acceptance. The ontology constitution already names `participates_in` as part of the intended initial vocabulary, so this is completion of an anticipated relation rather than a new conceptual direction.

### Layer 3: the encounter-surface role, only if needed

If product queries need to distinguish owned touchpoints from offerings in general, introduce:

```yaml
relationship_definition:
  id: touchpoint_for
  definition: >-
    An offering or experience functions as a surface through which a stakeholder
    encounters the referenced Brand within the assertion's declared context.
  source_types: [offering, experience]
  target_types: [brand-system]
  allow_inference: false
```

Then propose:

```text
Nike App --touchpoint_for--> Nike
```

This should remain a qualified assertion using `CTX-NIKE-DIGITAL-MEMBERSHIP-CURRENT`. The context supplies audience, channels, valid time, perspective, and purpose. The relation should not imply that every manifestation of Nike App, in every market and time period, has the same role.

This third layer is optional. Add it only when a competency question requires direct touchpoint retrieval. Otherwise, `offers`, `participates_in`, and the existing experience path are sufficient.

### Layer 4: representation remains separate

The visual, verbal, interaction, behavioral, motion, and artifact expressions of Nike inside the app should use `RepresentationBinding` and representation profiles. They should not be encoded by changing the Nike App entity or using the Brand–App relationship as a style rule.

Conceptually:

```text
Nike semantic identity
  -> global Nike representation profile
  -> Nike Membership digital overlay
  -> app-specific manifestation
```

This preserves one Nike identity while allowing its app manifestation to be more specific.

## Options considered

| Option | Benefit | Problem | Decision |
| --- | --- | --- | --- |
| `Nike --offers--> Nike App` | Existing, precise, direct, type-safe | Does not by itself describe Membership or touchpoint function | **Use as the canonical direct relation** |
| `Nike --has_component--> Nike App` | Already available and visually simple | Means inclusion in an analytical BrandSystem boundary; too broad for the business and experience semantics | Keep only if a declared analytical boundary genuinely requires it |
| `Nike --experienced_through--> Nike App` | Reads naturally | Current contract requires an `experience` target; Nike App is an `offering` | Do not widen the relation merely for this case |
| Reclassify Nike App as `experience` | Makes the previous edge legal | The app has persistent offering identity; using it is an experience, but the app is not itself one occurrence/experience | Reject |
| Duplicate Nike App as offering and experience entities | Gives every role its own node | Creates two identities that must be synchronized and invites contradictory histories | Reject |
| `Nike App --participates_in--> Nike Membership` | Expresses ecosystem structure cleanly | Requires adding the missing relation definition | Add after a small ontology fixture |
| `Nike App --touchpoint_for--> Nike` | Answers direct experience-surface queries | Adds vocabulary that may be unnecessary if no query requires it | Conditional extension |
| Generic `related_to` | Easy | Carries no reusable meaning or constraints | Reject |

## Identity resolution: “Nike Members app”

The current evidence does not justify creating an entity whose canonical label is `Nike Members app`.

The conservative interpretation is:

```text
mention: “Nike Members app”
candidate referent: ENT-NIKE-OF-006 / Nike App
status: alias hypothesis pending discriminating evidence
```

Why this matters:

- `Nike App` is an existing offering with official evidence.
- `Nike Membership` is a distinct offering/system layer.
- `Nike Members` denotes the audience of registered consumers.
- Similar naming is not identity proof.

If official evidence later establishes a separately governed product actually named “Nike Members app,” the hypothesis should split rather than silently overwrite Nike App.

## How the library led to this answer

I used a child-first, evidence-preserving traversal rather than searching every archive indiscriminately.

### 1. Establish the local objects and constraints

I first searched the Nike workspace for exact terms: `Nike App`, `Nike Membership`, `Nike Members`, `offering`, `experience`, `touchpoint`, and the current relationship IDs. This established that the apparent two-entity problem actually involved at least four semantic objects: Brand, App, Membership, and delivered Experience.

### 2. Inspect the relation contracts

I read the definitions of `offers`, `has_component`, and `experienced_through`. This eliminated two tempting shortcuts:

- `has_component` is a broad boundary relation, not the exact semantics sought.
- `experienced_through` cannot point directly to Nike App without violating its target type.

### 3. Inspect constitutional decisions

I checked the ontology constitution for classification, assertions, qualifiers, aliases, portfolio topology, and representation bindings. The decisive rules were:

- a persistent identity remains a semantic entity;
- a reusable connection is a typed relationship whose use is stored as an assertion;
- meaning-changing qualifiers stay on the assertion;
- aliases are evidence, not identity proof;
- `Offering`, `Brand`, and `BrandSystem` remain distinct;
- `participates_in` is already in the intended relation vocabulary;
- one semantic identity can have context-specific representations.

### 4. Search the wider conversation corpus by structural analogy

I then searched the indexed conversation corpus for the *shape* of the problem rather than just Nike vocabulary:

- one entity with multiple roles;
- relation as a semantic bridge;
- part/whole and membership;
- surface, manifestation, and touchpoint;
- typed relations with context, scope, evidence, and state;
- constitutive versus functional relations.

Two conversations were especially useful:

1. **READ_Semantic Context Infrastructure** argues that the missing layer is semantic coordination: a relation should be a structured “bridge object,” not a tag or vague prose. Applied here, the assertion is the bridge object that says not only that Nike and Nike App are connected, but *how* and *under which context*.
2. **Product Surfaces Explanation** distinguishes persistent relations from events and effects, and treats relations as typed channels of influence. Applied here, “Nike offers Nike App,” “Nike App participates in Membership,” and “Nike App is experienced through personalized guidance” must remain different typed channels.

A third conversation, **Thought Tube Algorithm**, reinforced that a connection should carry relation type, context/scope, confidence, and evidence rather than one permanent global weight. This supports keeping the Membership scope on the assertion rather than baking it into Nike App’s identity.

### 5. Apply Testflight’s control operators

I used these operators as review lenses:

- `world://operator/guardrail/ontology-conflation@1`: prevented an offering, an experience, an audience, and an app mention from becoming interchangeable.
- `world://operator/guardrail/mention-entity-conflation@1`: kept “Nike Members app” as a mention/alias hypothesis until identity evidence discriminates it.
- `world://operator/guardrail/identity-provenance-conflation@1`: preserved the distinction between the canonical entity, its evidence sources, and the proposed assertions.

Operator result: **resolved at the semantic-type level; proposed at the assertion level; alias remains a hold pending explicit identity evidence**.

## Success requirements and proofs

The solution is ready for acceptance only when the following fixtures pass:

1. **Direct connection:** querying offerings of Nike returns Nike App through `offers`.
2. **Identity continuity:** Nike App has one canonical entity ID across global, Membership, and app-specific contexts.
3. **No role collapse:** Nike App remains an `offering`; Personalized app guidance remains an `experience`; Nike Members remains an audience/environment.
4. **Membership path:** querying participants in Nike Membership returns Nike App after `participates_in` is defined.
5. **Context preservation:** the Membership relationship resolves only with its declared audience, channels, valid time, and perspective.
6. **Alias safety:** “Nike Members app” resolves to a hypothesis unless an accepted alias/evidence record establishes it as Nike App.
7. **Representation separation:** changing the Membership digital profile does not mutate Nike App’s semantic identity or the truth of `offers`.
8. **Reversibility:** removing or superseding a contextual assertion does not delete either entity.
9. **No vague fallback:** no `related_to` edge is required to answer the intended queries.
10. **Evidence trace:** every proposed relation resolves to source spans and a derivation receipt.

## Remaining decisions

Only two decisions are genuinely open:

1. Does the product need direct queries for **brand-owned touchpoints**? If yes, define and test `touchpoint_for`. If no, derive the answer from `offers`, `participates_in`, context, and experience relations.
2. Is “Nike Members app” merely local shorthand for Nike App, or is it intended to name a distinct product? Keep this unresolved until a source discriminates the possibilities.

Neither question blocks adding the direct `Nike --offers--> Nike App` proposal.

## Accessed material

### Testflight files

- [`workspaces/brand-nike-research/artifacts/entity-inventory.yaml`](../../workspaces/brand-nike-research/artifacts/entity-inventory.yaml)
- [`workspaces/brand-nike-research/artifacts/relationship-inventory.yaml`](../../workspaces/brand-nike-research/artifacts/relationship-inventory.yaml)
- [`workspaces/brand-nike-research/artifacts/context-profiles.yaml`](../../workspaces/brand-nike-research/artifacts/context-profiles.yaml)
- [`workspaces/brand-nike-research/artifacts/source-catalog.yaml`](../../workspaces/brand-nike-research/artifacts/source-catalog.yaml)
- [`workspaces/brand-nike-research/artifacts/evidence-notes.yaml`](../../workspaces/brand-nike-research/artifacts/evidence-notes.yaml)
- [`domains/brand/ontology/relationship-types/offers.yaml`](../../domains/brand/ontology/relationship-types/offers.yaml)
- [`domains/brand/ontology/relationship-types/has-component.yaml`](../../domains/brand/ontology/relationship-types/has-component.yaml)
- [`domains/brand/ontology/relationship-types/experienced-through.yaml`](../../domains/brand/ontology/relationship-types/experienced-through.yaml)
- [`domains/brand/policies/identity-resolution-v1.yaml`](../../domains/brand/policies/identity-resolution-v1.yaml)
- [`docs/plans/2026-08-20-brand-ontology-constitution-v0.1-design.md`](../plans/2026-08-20-brand-ontology-constitution-v0.1-design.md)
- [`docs/plans/2026-08-27-versioned-visual-language-design.md`](../plans/2026-08-27-versioned-visual-language-design.md)
- [`workspaces/brand-ontology-research/artifacts/candidate-definitions.yaml`](../../workspaces/brand-ontology-research/artifacts/candidate-definitions.yaml)
- [`workspaces/brand-ontology-research/artifacts/competency-questions.yaml`](../../workspaces/brand-ontology-research/artifacts/competency-questions.yaml)
- [`workspaces/brand-ontology-research/artifacts/evidence-notes.yaml`](../../workspaces/brand-ontology-research/artifacts/evidence-notes.yaml)
- [`packages/testflight-semantic/src/testflight_semantic/kernel.py`](../../packages/testflight-semantic/src/testflight_semantic/kernel.py)
- [`packages/testflight-semantic/src/testflight_semantic/context.py`](../../packages/testflight-semantic/src/testflight_semantic/context.py)
- [`reasoning/operators/ontology-conflation.yaml`](../../reasoning/operators/ontology-conflation.yaml)
- [`reasoning/operators/mention-entity-conflation.yaml`](../../reasoning/operators/mention-entity-conflation.yaml)
- [`reasoning/operators/identity-provenance-conflation.yaml`](../../reasoning/operators/identity-provenance-conflation.yaml)

### Conversation corpus

- [`READ_Semantic Context Infrastructure`, conversation `69f73bf9-8bd8-83eb-9e37-89bb83225731`](</Users/talhauddin/Documents/Codex/2026-08-12/mindscape/work/long-conversation-pilot-2026-08-30/corpus/shards/conversation_69f73bf9-8bd8-83eb-9e37-89bb83225731/turns.jsonl:43>) — semantic coordination and relations as structured bridge objects; especially turns with sequence indices 42–47.
- [`Product Surfaces Explanation`, conversation `6a062347-ac38-83eb-a7a2-38b294c132c5`](</Users/talhauddin/Documents/Codex/2026-08-12/mindscape/work/long-conversation-pilot-2026-08-30/corpus/shards/conversation_6a062347-ac38-83eb-a7a2-38b294c132c5/turns.jsonl:180>) — typed relations, relational roles, events/effects, and state deltas; especially the relation and implementation discussions around sequence indices 176–184 and 220–241.
- [`Thought Tube Algorithm`, conversation `6a6287fa-5ac4-83ed-a383-96b54bc5e370`](</Users/talhauddin/Documents/Codex/2026-08-12/mindscape/work/long-conversation-pilot-2026-08-30/corpus/shards/conversation_6a6287fa-5ac4-83ed-a383-96b54bc5e370/turns.jsonl:6>) — state-dependent typed connections with context, scope, confidence, and evidence.

## Final recommendation

Implement the semantics in this order:

1. Propose `Nike --offers--> Nike App` using the existing relation and current Membership context.
2. Confirm or hold the alias hypothesis for “Nike Members app.”
3. Define and fixture `participates_in`; propose `Nike App --participates_in--> Nike Membership`.
4. Add `touchpoint_for` only if a concrete competency question needs the direct touchpoint view.
5. Keep app-specific visual and interaction behavior in representation bindings, not in entity identity or the Brand–App edge.

This gives the graph a clean direct connection while preserving the richer reality around it.
