# Context intelligence Cordis plugin

Status: approved implementation design

## Goal

Give DeepSeek Harness workflow-specific, evidence-grounded Brand context through a native Cordis
plugin while keeping the intelligence engine independent enough to expose later as a standalone
service. Nike and its isolated Cognee dataset are the first configuration, not hard-coded runtime
logic.

## Architecture

```text
DeepSeek main agent
  -> Cordis automatic behavior or compile_context tool
  -> provider-neutral context intelligence engine
  -> dedicated request interpretation model
  -> workflow and retrieval planner
  -> Cognee retrieval port
  -> lightweight deterministic filter
  -> dedicated context synthesis model
  -> packet validator
  -> versioned context packet for the main agent
```

## Observable run journal

Every compilation owns a UUID run id and an append-only local journal. The engine records the
interpretation request and response, each retrieval query, content-addressed evidence references,
filter decisions, synthesis request and response, entity selection/use sets, and the compiled
packet. The Cordis boundary subsequently links the visible final assistant message or terminal
agent error to the same run. Reasoning blocks and credentials are excluded.

Entity provenance uses four distinct sets: configured `selected` ids, structured records actually
`retrieved`, ids merely `mentioned` inside accepted text, and directly retrieved ids whose evidence
was `used` by a compiled statement. A source mention never upgrades to an entity retrieval.

The Cordis shell owns Harness lifecycle integration, automatic activation, and tool registration.
The engine owns request interpretation, workflow planning, retrieval orchestration, filtering,
synthesis, validation, and derivation receipts. Cognee-specific imports stay in a local Python
JSON-lines adapter behind a `KnowledgeRetriever` port. A future HTTP or MCP adapter can replace
that process without changing the engine or Cordis plugin.

The intelligence model is separate from the main agent and configured with
`TESTFLIGHT_INTELLIGENCE_MODEL`. It may use the same provider credential, but never implicitly
inherits `TESTFLIGHT_DSH_MODEL`.

## Activation behavior

The plugin uses hybrid activation:

- a bridge behavior detects brand-dependent creation, adaptation, review, positioning, or
  evaluation turns and biases the normal pipeline toward context compilation;
- an explicit `compile_context` tool always invokes the compiler; and
- unrelated work bypasses the intelligence layer.

Automatic activation is a `bias`, not an override. Its match decision is inspectable and included
in the derivation receipt. Ambiguous or unsupported scope can return `needs_clarification`,
`partial`, or `no_hit` instead of guessing.

## Engine components

- `RequestInterpreter`: converts natural language into a strict context request using the
  dedicated intelligence model.
- `WorkflowPlanner`: selects the workspace, workflow recipe, context profiles, entity and
  relationship types, and smallest retrieval route.
- `KnowledgeRetriever`: retrieves from the explicitly configured dataset.
- `RetrievalFilter`: removes only obvious false retrievals such as wrong workspace/brand,
  navigation documents, missing sources, clear time mismatch, missing held-status disclosure, or
  negligible query connection.
- `ContextSynthesizer`: organizes only accepted evidence into the packet schema.
- `PacketValidator`: checks status, citations, scope, sections, and derivation metadata.

The filter is deliberately permissive beyond those checks. Semantic relevance and conflict
handling belong to the intelligence model, while evidence eligibility remains deterministic.

## Packet contract

Every result uses one versioned envelope with:

- `status`: `ready`, `partial`, `needs_clarification`, `no_hit`, or `unavailable`;
- normalized request and unresolved fields;
- knowledge grouped into identity, audience/environment, expression, offerings/experiences,
  perception/competition, governance/constraints, events, and relationships;
- workflow-specific reasoning instructions;
- conflicts, limitations, omissions, clarification questions, and citations; and
- a derivation receipt containing activation reason, model configuration, selected workspace and
  workflow, queries, accepted and rejected retrievals, operator ids, and evaluator outcomes.

The packet contains evidence and operating instructions, not private chain-of-thought or a
finished asset. DeepSeek remains responsible for the requested work.

## Failure and safety behavior

If the intelligence model fails, exact workflow configuration plus lexical retrieval may produce a
minimal `partial` packet. If Cognee or required configuration is unavailable, the plugin returns
`unavailable`; it does not silently search another dataset or the web. It never writes agent output
back to Cognee and never promotes Brand proposals into canonical state.

The first deployment is co-located on the home server with DeepSeek Harness and Cognee. The plugin
uses the isolated `testflight_brand_nike_research_staging` dataset. Full standalone transport and
interactive clarification/resume behavior are deferred, but their boundaries are present in the
initial contracts.

## Verification

Focused tests cover behavior matching and non-matching, explicit tool invocation, strict request
and packet schemas, workflow route selection, lightweight filter decisions, clarification and
failure statuses, workspace isolation, and provider/retriever substitution. Home-server smoke tests
cover Cordis loading and live retrieval against the isolated Nike staging dataset.

Applied reasoning operators: `boundary-conflation@1`, `configuration-runtime@1`,
`evaluation-schema@1`, `retrieval-reasoning-conflation@1`, `evidence-truth-conflation@1`,
`identity-provenance-conflation@1`, and `workspace-isolation@1`.
