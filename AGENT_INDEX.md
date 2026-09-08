# Testflight agent index

This is the repository-wide navigation entrypoint for agents and maintainers. Use it to locate the
smallest relevant module, understand what that module owns, and follow supported connections
between layers. This file is navigation, not domain evidence.

## Start here

| Intent | Start at | Then route to |
| --- | --- | --- |
| Understand the repository or an implementation boundary | `workspaces/testflight-product/architecture/AGENT_INDEX.md` | The owning app, package, adapter, or infrastructure file below |
| Work on product strategy, decisions, UX, customers, marketing, finance, operations, or research | `workspaces/testflight-product/AGENT_INDEX.md` | The smallest of its nine child modules |
| Work on semantic extraction, reasoning, retrieval, persistence, or agent runtime | `reasoning/README.md` | The smallest operator in `reasoning/operators/index.yaml` |
| Create or populate a knowledge child | `.agents/skills/child-container-creator/SKILL.md` | The parent workspace contract and population script |
| Create or run a reusable agent workflow | `workflows/README.md` | `packages/testflight-workflows`, then the LangGraph/runtime adapters |
| Run an agent with scoped context | `adapters/deepseek-harness/README.md` | The context-intelligence plugin and selected workspace |
| Add an external dependency | `docs/integrations/adding-an-upstream.md` | `upstreams/registry.yaml`, then an isolated adapter |
| Change a user-facing surface | `workspaces/testflight-product/experience-design/AGENT_INDEX.md` | `packages/testflight-design-language` and the owning app |

Always preserve source evidence, workspace, authority, time, branch, perspective, uncertainty, and
derivation when crossing a boundary. Configuration and indexes describe routing; they do not prove
runtime behavior or domain truth.

## How the layers connect

```text
Knowledge sources
  -> workspace/container contracts
  -> deterministic validation and projection
  -> Cognee adapter (rebuildable retrieval projection)
  -> context-intelligence package
  -> agent runtime or workflow handler

Agent identity
  -> authenticated workflow principal
  -> MCP/HTTP workflow catalog
  -> workflow access check and workflow authority grant
  -> LangGraph scheduling
  -> registered step handlers
  -> reasoning/operator runtime or authorized action adapter
  -> SQLite run, receipt, proposal, or canonical domain repository

Canonical domain YAML and package contracts
  -> applications and provider-neutral coordinators
  -> replaceable adapters
  -> upstream runtimes, models, storage, and external targets
```

Do not bypass these seams. In particular, Cognee is a projection rather than canonical storage,
model output is a proposal rather than accepted knowledge, and workflow visibility is checked
before its authority bundle is granted.

## Applications

Applications are runnable composition roots. They may connect owned packages and adapters but do
not redefine their contracts.

| Module | What it does | How to use it | Connects to |
| --- | --- | --- | --- |
| `apps/brand-intake-web` | Dependency-free founder-facing Brand intake experience prototype; browser-local data only | Serve with `python3 -m http.server 4317 --bind 127.0.0.1 --directory apps/brand-intake-web` | Experience-design contract and design-language package; no backend yet |
| `apps/brand-lab` | CLI and local explorer for validating, certifying, initializing, and inspecting Brand workspaces | `uv run brand-lab --help` | Brand and semantic packages; SQLite semantic adapter |
| `apps/creative-studio` | Write-capable, project-scoped moodboard and Creative Field surface | Start the operator runtime, then `creative-studio --project-id <id>` | Creative Field, semantic SQLite, creative connectors, operator HTTP runtime |
| `apps/workflow-runtime` | Authenticated shared runtime for declarative workflows over REST and MCP | `make serve-workflow-runtime`, using `workflows/runtime.example.yaml` as the configuration shape | Workflows package, LangGraph, MCP, operator HTTP, workflow SQLite |

## Provider-neutral packages

Packages own stable contracts and reusable logic. They must not import optional upstreams.

| Module | Owns | Use it when | Main connections |
| --- | --- | --- | --- |
| `packages/testflight-core` | Adapter descriptors, capabilities, and health contracts | Adding or inspecting an upstream adapter | Implemented by adapter boundaries |
| `packages/testflight-semantic` | Evidence, identity, context, time, provenance, authority, branches, perspectives, states, federation, decisions, and learning | A domain needs shared semantic primitives | Brand, Creative Field, SQLite semantic, Cognee projection |
| `packages/testflight-brand` | Brand-system ontology records, assertions, states, modules, and validation | Modeling or validating a Brand world | Brand domain YAML, Brand Lab, semantic package |
| `packages/testflight-content` | Immutable multimodal content units, observations, occurrences, patterns, interpretations, and transformations | Normalizing media before domain interpretation | Source evidence upstream; Brand/Creative Field interpretation downstream |
| `packages/testflight-creative-field` | Moodboard, observation, interpretation, Creative Field, projection, generation, evaluation, and review contracts | Building creative workflows without coupling to providers or UI | Creative Studio, semantic package, connectors, operator runtime |
| `packages/testflight-context-intelligence` | Scoped retrieval filtering, world-view and visual-language resolution, context packets, and traces | Compiling bounded evidence for another agent | Cognee read bridge and DeepSeek Harness context plugin |
| `packages/testflight-operator-runtime` | Executable operator definitions, provider preflight, structured execution, receipts, retries, and local HTTP transport | Running versioned model-backed operators | Canonical reasoning YAML, compatible model provider, Creative Studio and workflow prompt nodes |
| `packages/testflight-workflows` | Workflow schema, access, authority, step graph, prompts, handler contract, validation, catalog, and reference execution | Defining reusable agent workflows | LangGraph adapter, workflow runtime, MCP and SQLite adapters |
| `packages/testflight-design-language` | Code-consumable design tokens and generation contract | Building any user-facing Testflight interface | Canonical experience-design knowledge module and all UI apps |

## Adapters

Adapters isolate replaceable upstreams or infrastructure. New upstream-specific imports belong
inside the adapter and require a pinned entry in `upstreams/registry.yaml`.

| Module | Boundary | How to connect it |
| --- | --- | --- |
| `adapters/cognee` | Converts accepted semantic/content records into isolated, rebuildable Cognee projections and provides read bridges | Install the `cognee` extra; populate a named staging dataset; inject only its provider-neutral read interface |
| `adapters/langgraph` | Compiles a portable workflow definition into a real `StateGraph` and owns checkpoint selection | Construct `LangGraphWorkflowEngine` with the workflow catalog, handler registry, validator, and idempotency store |
| `adapters/mcp-workflows` | Projects authorized workflows as MCP tools and REST endpoints | Give it the workflow runtime service, authenticator, and selected MCP principal |
| `adapters/deepseek-harness` | Pins and launches the external DeepSeek Harness agent runtime | Configure environment-only provider values and run `scripts/run_deepseek_harness.sh` |
| `adapters/deepseek-harness-context-intelligence` | Native Cordis plugin that injects or explicitly compiles scoped context for Harness | Install through `make setup-server-context-intelligence`; point it at an isolated workspace configuration |
| `adapters/sqlite-semantic` | Append-oriented canonical semantic, creative, and content-addressed blob persistence | Inject repository implementations into Brand Lab or Creative Studio; keep databases under ignored `.data/` |
| `adapters/sqlite-workflow-runtime` | Durable workflow run records and action idempotency | Inject its stores into Workflow Runtime; keep the database under ignored `.data/` |
| `adapters/creative-connectors` | Capability-honest text/image target invocation and normalized output receipts | Translate a validated generation packet only after explicit external-action authority |

## Canonical domains

| Module | What it defines | Consumers |
| --- | --- | --- |
| `domains/brand` | Canonical Brand ontology, policies, fixtures, visual-reference types, and ontology-v2 migration source | `testflight-brand`, Brand workspaces, validation and population scripts |
| `domains/creative-field` | Canonical Creative Field dimensions and provider-neutral semantic vocabulary | `testflight-creative-field`, Creative Studio and operator configuration |

Domain definitions are not generated knowledge stores. Change IDs and meanings only through an
explicit version or migration.

## Knowledge workspaces and containers

Every workspace owns its identity, source authority, retrieval policy, lifecycle, registry, and
certification behavior. Route to the smallest relevant child before retrieving.

| Workspace | Purpose | Entry point | Population/validation |
| --- | --- | --- | --- |
| `workspaces/testflight-product` | Authoritative modular view of Testflight as a product | `workspaces/testflight-product/AGENT_INDEX.md` | `make product-workspace`; preview with `make product-workspace-projection` |
| `workspaces/reasoning-operators` | Retrieval pack for the canonical reasoning-operator catalog | `workspaces/reasoning-operators/AGENT_INDEX.md` | `scripts/populate_reasoning_operator_workspace.py` |
| `workspaces/brand-template` | Reusable isolated Brand workspace template | `workspaces/brand-template/AGENT_INDEX.md` | `brand-lab init`; validate and certify with Brand Lab |
| `workspaces/brand-ontology-research` | Evidence, questions, candidates, fixtures, and synthetic worlds supporting the Brand ontology | `workspaces/brand-ontology-research/AGENT_INDEX.md` | `make brand-research-workspace`; projection script is provider-specific |
| `workspaces/brand-nike-research` | Concrete public-evidence Brand workspace with entities, relations, world views, and visual language | `workspaces/brand-nike-research/AGENT_INDEX.md` | `make nike-research-workspace`; preview with `make nike-research-projection` |
| `workspaces/brand-hellobiotic-research` | Public-evidence Brand workspace with isolated product-library and internal content-strategy child routes | `workspaces/brand-hellobiotic-research/AGENT_INDEX.md` | Follow its workspace/config/registry contracts and certify each child route |
| `workspaces/brand-seeds` | Bounded seed inputs used to initialize Brand workspaces | Inspect the target seed and its provenance | Consume through workspace initialization; do not treat a seed as accepted evidence |

### Testflight Product child modules

| Child | Owns | Route from |
| --- | --- | --- |
| `product-definition` | Identity, principles, portfolio, capabilities, surfaces, roadmap | Product mission or scope questions |
| `product-decisions` | Proposals, decisions, alternatives, authority, supersession | Decision and approval questions |
| `experience-design` | Design language, content language, tokens, patterns, components, accessibility | UI, UX, language or visual questions |
| `architecture` | Systems, applications, packages, interfaces, data, deployment, dependencies | Implementation and system-boundary questions |
| `customers-market` | Actors, customers, segments, needs, journeys, feedback, market | Customer or market questions |
| `marketing-growth` | Positioning, narrative, messages, campaigns, channels, acquisition, retention | Marketing and growth questions |
| `finance-commercial` | Pricing, revenue, costs, budgets, forecasts, transactions, unit economics | Commercial and finance questions |
| `operations-governance` | Roles, delivery, policies, controls, risk, compliance, incidents | Operational and governance questions |
| `research-learning` | Sources, questions, hypotheses, experiments, metrics, evaluations, outcomes, learning | Research and evidence-synthesis questions |

Create product children through `workspaces/testflight-product/artifacts/extension-contract.yaml`.
Use the child-container skill to scaffold, then add the product-specific module contract, register
the child in the parent topology and module registry, validate, project to staging, and certify.

## Reasoning operators

`reasoning/operators/` is the canonical source. Operators are portable procedures and guardrails,
not hidden prompt memory. Select the smallest operator from `reasoning/operators/index.yaml`.

The catalog contains sixteen guardrails covering boundary, ontology, evidence, truth, identity,
state, retrieval, persistence, workspace, retry, runtime configuration, and evaluation concerns,
plus eight Creative Field transformation/control operators.

To add an operator:

1. Add its versioned YAML contract under `reasoning/operators/`.
2. Register it in `reasoning/operators/index.yaml`.
3. Extend the validator and add evaluator fixtures.
4. Rebuild the reasoning-operator workspace projection.
5. If it is model-executable, add a typed runtime definition and provider capability in
   `packages/testflight-operator-runtime`.
6. Run `make check`.

## Workflows and agents

Workflow YAML is the portable source; LangGraph is the orchestration implementation.

| Module | Role |
| --- | --- |
| `workflows/registry.yaml` | Versioned catalog of published workflow definitions |
| `workflows/examples/evidence-synthesis.yaml` | Four-node example: retrieve, evaluate records, synthesize, dispatch |
| `workflows/runtime.example.yaml` | Non-secret principals, handler modules, endpoints, and runtime composition |
| `packages/testflight-workflows` | Portable schema and execution semantics |
| `adapters/langgraph` | Real LangGraph graph compiler and execution engine |
| `apps/workflow-runtime` | Authenticated composition and lifecycle service |
| `adapters/mcp-workflows` | Agent-facing discovery and invocation tools |
| `adapters/sqlite-workflow-runtime` | Durable runs and idempotency |
| `packages/testflight-operator-runtime` | Prompt-backed node execution against a configured model provider |

To add a workflow:

1. Define access, knowledge, authority, input/output schemas, steps, prompts, and output mappings.
2. Register or reuse explicit handler modules.
3. Add the definition to `workflows/registry.yaml` and its modules to runtime configuration.
4. Run `make workflows`, then add an end-to-end runtime test.

To connect an agent today:

1. Add an ID, roles, and environment-backed token reference to runtime `principals`.
2. Grant workflow visibility through the workflow's `access.agent_ids` or `access.roles`.
3. Connect the external agent to the authenticated MCP endpoint or REST API.
4. After access succeeds, the runtime supplies the complete workflow authority and knowledge
   envelopes to its steps; the caller cannot widen either envelope.

An agent principal is currently an authenticated ID and role set, not a complete versioned agent
definition. Model profile, persona, tool bundles, knowledge defaults, deployment, and lifecycle are
still owned by the external agent runtime/configuration.

## Infrastructure, registries, and operations

| Path | Purpose | Use |
| --- | --- | --- |
| `upstreams/registry.yaml` | Immutable upstream release, commit, license, runtime, and adapter registry | Update before adding an external dependency |
| `infra/compose.yaml` | Opt-in local workspace composition | Validate with `make compose-config` |
| `.env.example` | Names and safe defaults for local-only configuration | Copy to ignored `.env`; never add credentials to tracked files |
| `scripts/` | Validation, projection, certification, setup, serving, and synchronization entrypoints | Prefer the corresponding `make` target when one exists |
| `.agents/skills` | Repository-local agent procedures | Start at `.agents/skills/AGENT_INDEX.md` and its catalog |
| `docs/decisions` | Accepted architecture decisions | Add an ADR for forks, vendoring, submodules, or material boundaries |
| `docs/plans` | Design and implementation plans | Use for proposed designs; do not treat plans as observed runtime state |
| `docs/operations` | Operational runbooks | Use for environment-specific execution and recovery |
| `docs/workboards` | Durable multi-agent implementation history | Use for task history, not canonical domain evidence |

## Supported connection recipes

### Knowledge to an agent

1. Resolve the workspace and smallest child route.
2. Apply workspace, branch, perspective, entity, time, classification, and result limits.
3. Retrieve lexical/BM25 first; use bounded same-child hybrid only on an in-domain miss.
4. Compile selected evidence through `testflight-context-intelligence`.
5. Inject the cited context packet through the agent adapter/plugin.

### Workflow as an agent tool

1. Authenticate a workflow principal.
2. Discover only authorized workflow descriptors through MCP or REST.
3. Invoke the workflow with inputs matching its JSON Schema.
4. Let LangGraph schedule nodes while Testflight enforces step semantics and authority.
5. Read the durable run result and receipts using the same principal.

### Model-backed operator execution

1. Select a canonical operator contract and version.
2. Construct a scoped invocation with disclosure references and an idempotency key.
3. Send it to the private operator HTTP runtime.
4. The runtime performs provider capability preflight before any model call.
5. Validate the structured result again at the domain/workflow boundary before persistence.

### Canonical persistence and retrieval projection

1. Validate and accept a typed semantic record through its owning application/domain policy.
2. Persist accepted state through the SQLite semantic boundary.
3. Build a deterministic projection with stable source and workspace identity.
4. Populate an isolated Cognee staging dataset.
5. Certify retrieval; rebuild the projection instead of editing generated state.

## Creation and verification checklist

| Creating | Required route | Minimum verification |
| --- | --- | --- |
| Package | Provider-neutral contract under `packages/`; register Python or pnpm workspace membership | Unit tests, import/type check, architecture inventory |
| Application | Composition root under `apps/`; depend only through owned package/adapter seams | Application tests, documented run command, authority boundaries |
| Adapter | Upstream registry first; descriptor, dependency-free health, docs, tests | Registry validation, health test, adapter contract tests |
| Root knowledge container | Workspace identity, index/config, topology, sources, registry, probes, lifecycle | Structural validation, deterministic dry run, staging certification |
| Child container/module | Child-container skill plus parent-specific extension contract and registration | Generic child validation and parent workspace validation |
| Operator | Canonical YAML, index entry, evaluators; runtime definition when executable | Operator catalog validation, fixtures, provider preflight tests |
| Workflow | YAML definition, registry entry, handlers, runtime configuration | Workflow validation, LangGraph compile, authorization and end-to-end tests |
| Agent principal | ID, roles, environment token reference, workflow access | Authentication denial/allow tests and filtered discovery |

Before committing any material change, run:

```bash
make check
```
