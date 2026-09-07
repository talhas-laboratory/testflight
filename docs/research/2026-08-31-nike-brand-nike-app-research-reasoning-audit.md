# Nike Brand–Nike App Research and Reasoning Audit

**Date:** 2026-08-31  
**Companion conclusion report:** [Connecting Nike Brand and Nike App](2026-08-31-nike-brand-nike-app-relationship-report.md)  
**Purpose:** Make the investigation auditable: what was searched, what was found, what was rejected, which conclusions follow from which evidence, and what remains uncertain.

## Scope and epistemic note

This document records a concise, evidence-based rationale and research trace. It does not attempt to reproduce private hidden chain-of-thought. Instead, it exposes the parts required to inspect or challenge the result:

- starting hypotheses;
- search terms and search order;
- files and conversations accessed;
- atomic evidence findings;
- rejected results and rejection reasons;
- decision criteria;
- premise-to-conclusion mappings;
- confidence and unresolved questions.

No ontology records or Nike workspace data were changed during this research.

## The problem as I understood it

The initial wording was:

> Find a clean and elegant solution for connecting two entities: the Nike brand and the Nike Members app.

Before choosing an edge, four questions had to be separated:

1. Are “Nike App” and “Nike Members app” actually the same persistent entity?
2. What semantic type is the app?
3. Which meaning of “connected” is required: ownership, offering, containment, participation, manifestation, or customer touchpoint?
4. Should all meanings be represented by one relation or by several contextual assertions?

Treating any of these as already answered would have made the result look simpler while making it less reliable.

## Starting hypotheses

These were the candidate explanations tested against the local ontology and library.

| ID | Starting hypothesis | Evidence that would support it | Evidence that would reject or limit it |
| --- | --- | --- | --- |
| H1 | Nike App is an `Offering` that Nike `offers` | Existing app entity typed `offering`; valid BrandSystem-to-Offering relation | App is instead modeled as a bounded experience or manifestation |
| H2 | Nike App is a component of the Nike BrandSystem | `has_component` is intended to express the exact business/experience relation | Definition only expresses inclusion in an analytical boundary |
| H3 | Nike App is itself an `Experience` through which Nike is encountered | App lacks independent lifecycle and is modeled as an experience | App has persistent product/service identity and has separate delivered experiences |
| H4 | Nike App is a representation or manifestation of Nike | App identity is only a visual/verbal rendering | Representation rules are modeled separately from the persistent app offering |
| H5 | Nike App is one participant/surface in Nike Membership | Membership context lists the app as a connected channel and official evidence links them | Membership and App are synonymous or unrelated |
| H6 | “Nike Members app” is a second canonical entity | Discriminating official name, ID, lifecycle, or source evidence | The phrase is only shorthand for Nike App or a blend of App, Membership, and audience names |

I did not choose a preferred hypothesis before examining the local entity and relation contracts.

## Traversal strategy

I used a precision-first, child-first traversal:

```text
Nike workspace
  -> Brand ontology relation definitions
  -> Constitution and competency questions
  -> Existing semantic kernel contracts
  -> Indexed conversation corpus by structural analogy
  -> Candidate comparison and operator review
```

The method deliberately starts with the smallest authoritative container. The broad conversation archive was used for design inspiration only after the local Testflight facts and contracts were known.

### Why this order matters

- Searching conversations first could have produced an elegant abstraction incompatible with Testflight’s implemented types.
- Searching only for “Nike” would have found local facts but missed analogous work on multi-role identity and semantic bridge objects.
- Searching the entire archive for broad words like “touchpoint” produced substantial marketing noise.
- Exact local lookup followed by structural analogy provided higher relevance with less semantic overreach.

## Detailed research journal

### Checkpoint 1 — establish whether the two entities already exist

**Local query cluster**

```text
Nike App
Nike Membership
Nike Members
member app
offering
experience
```

**Accepted hits**

| File | Finding | Effect on hypotheses |
| --- | --- | --- |
| `entity-inventory.yaml` | `ENT-NIKE-OF-005` is Nike Membership, typed `offering` | Membership is not merely an alias for the app |
| `entity-inventory.yaml` | `ENT-NIKE-OF-006` is Nike App, typed `offering` | Strongly supports H1; weakens H3 and H4 |
| `entity-inventory.yaml` | `ENT-NIKE-XP-004` is Personalized app guidance, typed `experience` | Shows the delivered experience is modeled separately from the app |
| `entity-inventory.yaml` | `ENT-NIKE-EN-017` is Nike Members, typed `environment`/audience | Separates the audience from the app and Membership offering |
| `context-profiles.yaml` | Membership context lists `nike-app` among connected channels | Supports H5 without making App and Membership identical |

**Checkpoint result**

The apparent two-node problem is actually a four-object region:

```text
Nike                    Brand/BrandSystem
Nike Membership         Offering / membership layer
Nike App                Offering / digital service
Personalized guidance   Experience delivered through the app
```

`Nike Members` is additionally an audience. This made identity and role separation the main problem.

### Checkpoint 2 — inventory the relationships already asserted

**Local query cluster**

```text
REL-NIKE
offers
experienced_through
has_component
source_id: world://brand/nike
target_id: ENT-NIKE-OF-006
```

**Accepted hits**

- Nike already `offers` Nike Membership.
- Nike is `experienced_through` its digital commerce experience.
- Nike Membership is `experienced_through` member product access and rewards.
- Nike App is `experienced_through` personalized app guidance.
- There is no existing direct Nike-to-Nike-App assertion.

**Checkpoint result**

The graph contains the semantic neighborhood but is missing the direct factual edge. That absence does not imply a missing architectural primitive.

### Checkpoint 3 — test each existing relationship contract

I read the relation definitions rather than inferring their meaning from labels.

| Relation | Contract | Fit for Nike → Nike App | Decision |
| --- | --- | --- | --- |
| `offers` | Brand makes an offering available | Exact source and target types; precise factual meaning | Accept for direct connection |
| `has_component` | BrandSystem includes an item in its declared analytical boundary | Type-valid but semantically broad | Do not use as the primary answer |
| `experienced_through` | Brand or offering is encountered through an `experience` | Nike App is not an `experience` target | Reject direct use without retyping or widening |

**Hypothesis update**

- H1 became the strongest direct connection.
- H2 remained possible only for analytical-boundary queries.
- H3 was rejected because the ontology already distinguishes the app from the experience it delivers.

### Checkpoint 4 — inspect the ontology constitution

The constitution supplied five decisive rules:

1. A thing with persistent identity and independent history is a `SemanticEntity`.
2. A reusable connection is a relationship; each use is a contextual `Assertion`.
3. Qualifiers that change meaning stay on the assertion instead of being flattened into an unqualified edge.
4. Aliases are evidence for identity resolution, not proof of identity.
5. `Brand`, `Offering`, `Experience`, and representation machinery stay distinct.

The constitution also lists `participates_in` in the intended initial relation vocabulary even though that definition has not yet been implemented in the Brand module.

**Hypothesis update**

- H5 gained support: contextual participation is already anticipated by the architecture.
- H6 moved to **hold**: “Nike Members app” cannot become a second entity from naming similarity alone.
- H4 was limited: app-specific visual/interaction behavior belongs in `RepresentationBinding`, but the persistent app itself remains an Offering.

### Checkpoint 5 — search the conversation library by exact structural phrases

The indexed corpus used was:

```text
/Users/talhauddin/Documents/Codex/2026-08-12/mindscape/
  work/long-conversation-pilot-2026-08-30/corpus/structural/index.sqlite
```

I searched the FTS index for exact or near-exact structural concepts rather than Nike-specific wording.

#### Query: `"bridge object"`

**High-value result:** `READ_Semantic Context Infrastructure`

The conversation defines a relation as a structured bridge that explains how A connects to B, why, and what the connection changes or constrains. This reinforced the use of an Assertion as a first-class semantic record instead of a vague graph line.

**Other results:** `Report Summary Architecture` and `Worldbuilding Lens Analysis`.

These were not used as primary evidence because they were farther from entity/relation modeling and added no decisive constraint beyond the stronger source.

#### Query: `"typed relation"`

**High-value result:** `Product Surfaces Explanation`

This conversation distinguishes a stable relation type from an event, applied effect, or state change. It reinforced that these statements should not be collapsed:

```text
Nike offers Nike App
Nike App participates in Nike Membership
Nike App delivers/affords personalized guidance
Nike App functions as a brand touchpoint
```

They are different semantic channels even though they connect overlapping objects.

**Other results:** `brainwalk_11.04. 18:00`, `Context Management Design`, and `Feed surface research`.

They were useful as corroboration but not required to decide the local ontology question.

#### Query: `"relational role"`

**Result:** no direct FTS hit.

This was recorded as a no-hit rather than expanding automatically into unrelated similarity results. The concept was instead supported by the ontology constitution’s treatment of product-brand/sub-brand as roles or relationships.

#### Query: `touchpoint`

**Result:** many hits across marketing, SaaS, storytelling, audits, and agents.

**Rejection reason:** excessive domain noise. The broad query was not used to form the conclusion. Relevant touchpoint meaning came from the local Brand research evidence and ontology instead.

#### Query: `manifestation`

**Result:** many early hits concerned theology and philosophy.

**Rejection reason:** lexical collision. The query did not reliably identify software representation semantics. I returned to the local `RepresentationBinding` documents rather than treating semantic similarity as evidence.

### Checkpoint 6 — inspect the strongest conversation passages

Three conversations survived the precision and relevance gates:

| Conversation | Accepted insight | Application to Nike/App |
| --- | --- | --- |
| `READ_Semantic Context Infrastructure` | Relations should be structured semantic bridges, not tags | Store typed contextual assertions, not `related_to` |
| `Product Surfaces Explanation` | Stable relations, events, effects, and state changes are different objects | Do not use one edge for offering, participation, touchpoint, and experience |
| `Thought Tube Algorithm` | Relation relevance depends on relation type, state/context, confidence, and evidence | Scope Membership-specific roles instead of changing App identity globally |

These conversations were treated as design inspiration, not authoritative facts about Nike.

### Checkpoint 7 — test the candidate solutions against control operators

#### Ontology-conflation test

Question: Does the proposal keep Offering, Experience, audience, relation, and representation separate?

- `Nike --offers--> Nike App`: pass.
- Retype Nike App as Experience: fail.
- Duplicate Nike App by role: fail due to identity fragmentation.
- Put visual rules on the Brand–App edge: fail due to semantic/representation conflation.

#### Mention–entity test

Question: Does the proposal create a canonical entity from the phrase “Nike Members app” without discriminating evidence?

- Automatic new entity: fail.
- Alias hypothesis pointing toward Nike App: pass, status remains unresolved.

#### Identity–provenance test

Question: Can every proposed assertion retain evidence, context, perspective, status, and derivation independently of the entity IDs?

- Contextual Assertion records: pass.
- Unqualified database edge as sole record: fail.

## Evidence-to-conclusion ledger

This is the explicit rationale chain behind the recommendation.

| Evidence-backed premise | Conclusion supported | Confidence |
| --- | --- | --- |
| Nike App already has a persistent Offering entity | Do not create a second role-specific App entity | High |
| Personalized app guidance already exists as a separate Experience | Do not retype Nike App as Experience | High |
| `offers` permits BrandSystem → Offering | Use `Nike --offers--> Nike App` as the direct relation | High |
| `has_component` means analytical boundary inclusion | Do not use it as the sole semantic explanation | High |
| Membership context includes Nike App as a channel | App has a scoped role in Membership | Medium-high |
| Constitution anticipates `participates_in` | Add that relation as the clean ecosystem link | Medium-high pending contract fixture |
| Assertions preserve context and evidence | Store each role as its own qualified assertion | High |
| Aliases are not identity proof | Hold “Nike Members app” as an alias hypothesis | High |
| Representation profiles can specialize one identity by context | Model app expression separately from app identity | High |
| Direct touchpoint retrieval is not yet shown as a required competency question | Make `touchpoint_for` optional, not mandatory | Medium |

## Why the final topology was chosen

The candidate was evaluated on seven criteria:

1. **Semantic precision:** each relation should answer a distinguishable question.
2. **Identity stability:** one real-world app should retain one canonical identity.
3. **Type safety:** relation endpoints must satisfy their contracts.
4. **Context sensitivity:** Membership-specific meaning must not become a timeless global fact.
5. **Evidence traceability:** each assertion must retain sources and derivation.
6. **Minimal ontology growth:** use existing vocabulary before inventing new primitives.
7. **Future query utility:** the graph should answer direct, ecosystem, experience, and representation questions without ambiguity.

The selected topology scored best because it uses one existing direct relation and adds only the missing distinctions when a query needs them:

```text
Direct commercial/service fact:
Nike --offers--> Nike App

Membership structure:
Nike App --participates_in--> Nike Membership

Delivered experience:
Nike App --experienced_through--> Personalized app guidance

Optional encounter-surface view:
Nike App --touchpoint_for--> Nike
```

## Alternatives rejected and exact reasons

### One `related_to` edge

Rejected because it cannot answer *how* the two entities are related, cannot constrain downstream reasoning, and provides no reusable relation semantics.

### One `has_component` edge

Rejected as the primary answer because it only states that the app lies inside a declared BrandSystem boundary. It does not distinguish offering, Membership participation, or touchpoint function.

### Direct `experienced_through` edge to the app

Rejected under the current contract because its target must be an Experience. Widening the target type for one fixture would weaken the ontology’s useful Offering/Experience distinction.

### App as a representation of Nike

Rejected as an identity classification. The app contains manifestations of Nike, but it also has persistent service/product behavior and history. Its visual and interaction expression can be governed by representation bindings without reclassifying the entity.

### Separate entities for “Nike App as offering” and “Nike App as touchpoint”

Rejected because role is not identity. Duplication would create synchronization, history, and merge problems.

### Mandatory `touchpoint_for` relation immediately

Deferred because the current direct question is already answered by `offers`. A new relation should be justified by a competency question, not only because it sounds expressive.

## Uncertainty and holds

### Hold 1 — alias identity

It remains unproven that “Nike Members app” is an accepted alias for Nike App. Current evidence makes this plausible, but not certain enough for automatic identity mutation.

### Hold 2 — touchpoint vocabulary

The local evidence supports the idea that Nike App is an owned digital touchpoint, but the product requirement for a direct `touchpoint_for` query has not yet been demonstrated. This is a modeling option, not a required conclusion.

### Hold 3 — participation direction and inverse

Before implementing `participates_in`, Testflight should define its endpoint types, direction, inverse, and whether Membership is treated as an Offering, ecosystem, or both within the current Brand module.

## Reproducible search recipe

From the Testflight repository:

```bash
rg -n -i \
  'Nike App|Nike Membership|Nike Members|experienced_through|has_component|offers' \
  workspaces/brand-nike-research domains/brand docs/plans
```

Conversation corpus schema inspection:

```bash
sqlite3 /Users/talhauddin/Documents/Codex/2026-08-12/mindscape/work/long-conversation-pilot-2026-08-30/corpus/structural/index.sqlite \
  '.schema turns_fts'
```

Example precise corpus query:

```bash
sqlite3 -header -column \
  /Users/talhauddin/Documents/Codex/2026-08-12/mindscape/work/long-conversation-pilot-2026-08-30/corpus/structural/index.sqlite \
  "SELECT c.title, t.conversation_id, t.turn_id
   FROM turns_fts t
   JOIN conversations c USING(conversation_id)
   WHERE turns_fts MATCH '\"bridge object\"'
   LIMIT 10;"
```

Repeat the FTS query with `"typed relation"`, `"relational role"`, `touchpoint`, and `manifestation`. Record no-hits and reject domain-noisy results rather than forcing them into the evidence set.

## Complete access log

### Local Testflight evidence and contracts

- [`workspaces/brand-nike-research/artifacts/entity-inventory.yaml`](../../workspaces/brand-nike-research/artifacts/entity-inventory.yaml)
- [`workspaces/brand-nike-research/artifacts/relationship-inventory.yaml`](../../workspaces/brand-nike-research/artifacts/relationship-inventory.yaml)
- [`workspaces/brand-nike-research/artifacts/context-profiles.yaml`](../../workspaces/brand-nike-research/artifacts/context-profiles.yaml)
- [`workspaces/brand-nike-research/artifacts/source-catalog.yaml`](../../workspaces/brand-nike-research/artifacts/source-catalog.yaml)
- [`workspaces/brand-nike-research/artifacts/evidence-notes.yaml`](../../workspaces/brand-nike-research/artifacts/evidence-notes.yaml)
- [`workspaces/brand-nike-research/artifacts/asset-workflow-context.yaml`](../../workspaces/brand-nike-research/artifacts/asset-workflow-context.yaml)
- [`domains/brand/ontology/brand-system.yaml`](../../domains/brand/ontology/brand-system.yaml)
- [`domains/brand/ontology/entity-types/offering.yaml`](../../domains/brand/ontology/entity-types/offering.yaml)
- [`domains/brand/ontology/entity-types/experience.yaml`](../../domains/brand/ontology/entity-types/experience.yaml)
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

### Reasoning operators

- [`reasoning/operators/ontology-conflation.yaml`](../../reasoning/operators/ontology-conflation.yaml)
- [`reasoning/operators/mention-entity-conflation.yaml`](../../reasoning/operators/mention-entity-conflation.yaml)
- [`reasoning/operators/identity-provenance-conflation.yaml`](../../reasoning/operators/identity-provenance-conflation.yaml)

### Conversation shards

- [`READ_Semantic Context Infrastructure`](</Users/talhauddin/Documents/Codex/2026-08-12/mindscape/work/long-conversation-pilot-2026-08-30/corpus/shards/conversation_69f73bf9-8bd8-83eb-9e37-89bb83225731/turns.jsonl:43>)
- [`Product Surfaces Explanation`](</Users/talhauddin/Documents/Codex/2026-08-12/mindscape/work/long-conversation-pilot-2026-08-30/corpus/shards/conversation_6a062347-ac38-83eb-a7a2-38b294c132c5/turns.jsonl:180>)
- [`Thought Tube Algorithm`](</Users/talhauddin/Documents/Codex/2026-08-12/mindscape/work/long-conversation-pilot-2026-08-30/corpus/shards/conversation_6a6287fa-5ac4-83ed-a383-96b54bc5e370/turns.jsonl:6>)

## Audit conclusion

The conclusion was not derived from the phrase “Nike Members app” alone. It emerged from four converging constraints:

1. the current Nike workspace already treats Nike App as a persistent Offering;
2. the relation contract already provides the correct direct BrandSystem-to-Offering predicate, `offers`;
3. the constitution requires roles, contexts, aliases, and representations to remain separate from identity;
4. the conversation library consistently favors typed, contextual bridge relations over vague or overloaded connections.

Therefore the least distorting solution is:

```text
one Nike App identity
+ existing direct `offers` assertion
+ scoped Membership participation
+ separate delivered experiences
+ optional touchpoint relation when a query proves it necessary
```

This is both the minimal local fix and the solution most consistent with the broader design library.
