# Concept Lab v1 implementation plan

Date: 2026-09-08
Status: implementation-ready plan; no Concept Lab runtime or knowledge projection exists yet
Owner: talha
Execution board: `docs/workboards/concept-lab-v1/`

## Objective

Build the smallest reliable Concept Lab that lets a Codex user invoke `$concept-lab` or say
“enter the Concept Lab,” converse in a specialized theoretical language, retrieve scoped knowledge
derived from prior discussions, and transform material in both directions:

```text
source material
  -> concepts and distinctions
  -> theory branches and relations
  -> ontology / traversal / agent-composition proposals
  -> technical artifacts

technical artifact
  -> formal assumptions
  -> originating theory
  -> interpretation and source anchors
```

The first version is repository-native and provider-neutral. It adds no UI, model dependency,
live database, background service, or live Cognee population.

## Fixed decisions

These decisions are already authorized for v1 and must not be reopened by implementation tasks:

1. Concept Lab is a sovereign workspace, not a child of the Testflight Product workspace.
2. Testflight Product defines Concept Lab as a product capability; it does not own the Lab's
   speculative knowledge.
3. The two workspaces exchange immutable, source-bearing packets through explicit bridges.
4. Cross-workspace traversal is denied by default. A packet names its exact imported records.
5. Lab outputs are proposals. Promotion into product modules always requires explicit human
   authorization in v1, even when automated evaluators pass.
6. A repo-local `concept-lab` skill is the interaction entry point. Automatic skill discovery stays
   enabled so natural language can activate it; `$concept-lab` is the reliable explicit form.
7. Domain knowledge lives in versioned workspace artifacts, never inside `SKILL.md`.
8. V1 operators are portable instruction contracts. They do not require an executable provider
   route or a registered workflow.
9. Existing semantic, content, federation, context-intelligence, operator, and workspace contracts
   are reused. New primitives are introduced only for concepts and formation packets that have no
   existing owner.
10. The Biotic relational-content theory is the proof case, not a universal ontology.

## Success criteria

V1 is complete when:

- Codex discovers a valid repo-local `$concept-lab` skill and its natural-language triggers.
- The skill can select one of five modes: explore, distill, formalize, form, or trace.
- A canonical Concept Lab workspace and isolated `relational-content` child validate structurally.
- Four versioned operators preserve evidence, branches, abstraction level, and derivation.
- A formation packet can target an existing Testflight Product module without writing to it.
- A reverse trace resolves every technical proposal to theory records and source anchors.
- The Biotic fixture completes the full forward and reverse path without treating a founder thesis
  as customer or scientific evidence.
- Deterministic tests cover boundary, no-hit, ambiguity, bridge authority, and semantic continuity.
- `make check` passes and no live projection or external action occurs.

## Architecture and ownership

### 1. Interaction skill

Path: `.agents/skills/concept-lab/`

The skill owns activation, specialized conversational posture, mode selection, context-loading
order, and output expectations. It must remain short. Conditional guidance belongs in references:

- `references/language.md`: shared vocabulary and distinctions;
- `references/modes.md`: mode routing and return shapes;
- `references/workspace-routing.md`: child-first retrieval and bridge rules;
- `references/formation-targets.md`: ontology, traversal, agent, workflow, schema, and explanation
  targets.

The skill must never contain accumulated domain knowledge or imply persistent runtime state. It
uses the current conversation plus explicit workspace session records. If no session or domain is
named, it may infer only when the current request is unambiguous; otherwise it asks one bounded
question.

### 2. Concept Lab domain contracts

Path: `domains/concept-lab/`

The domain layer defines provider-neutral records:

- `ConceptFragment`: source-anchored candidate meaning;
- `ConceptDefinition`: versioned definition with scope and alternatives;
- `ConceptRelation`: typed, directional, scoped relationship;
- `TheoryBranch`: internally coherent but not necessarily accepted model;
- `TransformationRun`: inputs, operator, configuration, outputs, omissions, and evaluation;
- `FormationPacket`: proposed technical projection and explicit target;
- `ReverseTrace`: technical artifact back to formal, theoretical, interpretive, and source layers.

Do not redefine existing Evidence, Context, WorldBranch, Derivation, AuthorityGrant, ContentUnit,
KnowledgeContainer, or FederationBridge primitives. Reference or compose them.

### 3. Knowledge workspace

Paths:

- `workspaces/concept-lab/`: global routing, policy, source authority, and project registry;
- `workspaces/concept-lab/relational-content/`: first isolated theory domain and Biotic proof case.

The parent routes by project/domain. Children own theory records and transformation outputs. Exact
and lexical retrieval run child-first; bounded same-child hybrid retrieval is only a declared
future option. No parent-wide fallback follows a child no-hit. Generated indexes stay noncanonical.

### 4. Transformational operators

Paths: `reasoning/operators/*.yaml` and `reasoning/operators/index.yaml`

Add four domain-neutral operators:

1. `concept-extraction@1`: source material → anchored fragments, claims, questions, tensions, and
   ambiguities.
2. `theory-synthesis@1`: fragments → definitions, relations, competing branches, invariants, and
   unresolved gaps.
3. `formation-projection@1`: selected theory branch → ontology, traversal, agent-composition,
   workflow, schema, or technical-language proposal.
4. `formation-trace@1`: proposed artifact → formal assumptions, theory branch, transformations,
   and source anchors.

Each operator returns `ready`, `partial`, `branch`, `ask`, `hold`, or `no_hit` as applicable and
records its evaluator outcomes. Existing guardrails remain composed around these transformations.

### 5. Product bridge

The bridge is an exchange contract, not shared mutable storage.

Product → Lab uses an `InquiryPacket` containing the question, product locus, constraints, allowed
sources, requested abstraction, and authority. Lab → Product uses a `FormationPacket` containing
the theory branch, target module, proposed change, source lineage, alternatives, evaluations, and
`canonical_write: false`.

The receiving product route is chosen by current module ownership:

| Formation target | Product module |
| --- | --- |
| capability, outcome, roadmap | `product-definition` |
| system, package, interface, runtime boundary | `architecture` |
| open question, hypothesis, experiment, evaluation | `research-learning` |
| accept, reject, hold, supersede | `product-decisions` |
| interaction or language proposal | `experience-design` |

The bridge must not copy customer or brand facts into Testflight Product without a separately
authorized, provenance-bearing import.

## Transformation modes

| Mode | Input | Output | Default evidence posture |
| --- | --- | --- | --- |
| `explore` | question, intuition, or artifact | conceptual map and productive questions | exploratory |
| `distill` | conversation or sources | anchored concept fragments and distinctions | grounded |
| `formalize` | selected fragments | theory branches, relations, invariants, alternatives | grounded |
| `form` | selected theory branch | reviewable technical FormationPacket | grounded |
| `trace` | technical artifact or packet | ReverseTrace with missing-link report | citation required |

The skill can move between modes only when the preceding output is sufficient. It must not hide a
mode transition inside prose.

## Data and state rules

- Raw discussions are immutable source records or stable references to existing artifacts.
- Interpretation and theory are revisioned, branchable, and may contradict each other.
- A transformation never edits its input; it emits a new record and derivation receipt.
- Accepted product decisions may return to the Lab as bounded constraints, not universal truths.
- Session records store selected workspace, domain, branch, mode, source refs, and open questions.
- V1 has no global “active session” pointer; the task context or invocation names the session.
- Sensitive or personal material requires a declared classification and cannot enter fixtures.

## Failure behavior

- Missing source anchors → `hold` for distillation or trace.
- Multiple defensible interpretations → `branch`, never silent selection.
- Unknown target module → `ask` before formation.
- Unsupported cross-workspace access → `hold` with a boundary receipt.
- Child retrieval miss → `no_hit`, not parent-wide semantic search.
- Structurally valid but semantically weak output → `partial` or `revise`.
- Any attempted canonical product write → reject; emit a proposal packet instead.

## Verification strategy

Tests must inspect behavior and continuity, not generated wording. The fixture suite will verify:

1. every concept fragment resolves to a source anchor;
2. disagreement produces two branches rather than a flattened synthesis;
3. formation preserves selected branch, scope, uncertainty, and alternatives;
4. bridge traversal remains disabled without an explicit grant;
5. target-module routing follows the existing product module contract;
6. reverse tracing detects missing derivation edges;
7. “vegan” is not transformed into a biological mechanism;
8. a founder hypothesis does not become a customer fact;
9. the skill routes the five request shapes to the correct mode;
10. out-of-domain and insufficient-context requests return typed non-success outcomes.

No model call is required for the deterministic acceptance suite. A later human evaluation may
assess conversational usefulness separately.

## Execution order

```text
TASK-001 decision
  -> TASK-002 contracts
      -> TASK-003 workspace
      -> TASK-005 operators
  -> TASK-004 bridge (needs 002 + 003)
  -> TASK-006 skill (needs 003 + 005)
  -> TASK-007 validation (needs 002–006)
  -> TASK-008 Biotic rehearsal
  -> TASK-009 final documentation and gates
```

Only TASK-001 begins in `ready`. Every later task starts in `backlog` and moves to `ready` only
when its dependencies are verified.

## Instructions for the implementing model

For every task:

1. Read repository `AGENT_INDEX.md`, this plan, the board protocol files, and only the task's
   listed prerequisites.
2. Claim exactly one task and append an update before editing implementation files.
3. Treat “fixed decisions” above as constraints, not questions to redesign.
4. Do not edit files assigned to later tasks unless the current task explicitly lists them.
5. Preserve semantic distinctions and source references at every transformation.
6. Use `apply_patch` for edits and prefer existing repository scripts for scaffolding or validation.
7. Run the task's targeted checks before `make check`.
8. Record exact commands, outcomes, changed files, and residual risks in the task packet.
9. Stop with `hold` when authority, workspace identity, or source lineage is missing.
10. Commit one task per commit with a narrow message; do not combine adjacent tasks for speed.

## Explicitly deferred

- Dedicated Concept Lab UI or app.
- Persistent enter/exit runtime state.
- Model-provider integration or executable operator registration.
- Declarative Concept Lab workflows exposed over MCP/REST.
- Live subscriber, customer, or private conversation ingestion.
- Live Cognee projection or retrieval certification.
- Automatic product-workspace promotion.
- Generalization from the Biotic proof case to all brands without new evidence.
