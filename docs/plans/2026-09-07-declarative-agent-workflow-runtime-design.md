# Declarative Agent Workflow Runtime

## Status

Accepted and implemented foundation; the shared service now executes through LangGraph.

## Goal

Allow authorized agents to discover and invoke reusable workflows as typed tools. Authors define a
workflow in YAML: inputs, outputs, bounded knowledge visibility, workflow-level authority, steps,
dependencies, conditions, loops, retries and actions. The agent does not receive direct access to
the underlying containers, credentials or adapters.

## Architecture

```text
agent → filtered workflow catalog → shared runtime API → access decision
      → immutable workflow authority grant → validated execution graph
      → LangGraph adapter → scoped handlers → typed output and receipts
```

`testflight-workflows` owns portable meaning. `adapters/langgraph` owns LangGraph imports and graph
scheduling. Future API, persistence, retrieval, operator and action adapters register handlers
through the stable step-handler port.

## Contract

A workflow declares an agent audience, knowledge envelope, authority bundle, JSON Schema input and
output contracts, a fixed acyclic step graph, and output bindings. Step kinds cover retrieval,
entity resolution, reasoning operators, transformations, actions and bounded map loops. Independent
ready steps may execute concurrently. `when` conditions provide branching without allowing callers
to inject new nodes.

Each node may carry a versioned instruction contract. Model-backed nodes additionally carry a
versioned prompt contract, strict placeholder bindings, a node-specific JSON Schema and a route to
the private operator runtime. Prompt instructions and knowledge authority are intentionally
separate: only the step's validated access envelope decides which workspace/container values may
enter the node. Model invocation also requires the explicit `model.invoke` capability.

Workflow access grants the complete predefined workflow authority for one run. A step may use only
a declared subset. The caller cannot widen workspaces, containers, entities, capabilities, actions
or credential references. Action steps require an explicit action ID and idempotency key.

## Runtime behavior

The portable engine resolves explicit `$inputs`, `$steps`, `$run`, `$item` and `$index` bindings.
The shared application compiles the fixed topology into LangGraph, which schedules nodes and keeps
an in-process checkpoint. Portable handlers still own conditions, bounded loops, retries,
timeouts, authority checks and per-step receipts. Failure policies are `fail`, `hold` or
`continue`. Only successful or partial action results enter the durable SQLite idempotency store.

Agent discovery returns only authorized workflows and exposes their descriptions, JSON Schemas and
side-effect classes. REST and MCP use that filtered catalog rather than exposing raw handler or
container registries. The example is directly assigned to `agent:testflight-research` and has
concrete local retrieval, evidence evaluation, proposal synthesis and proposal dispatch handlers.
Evaluation and synthesis are prompt-backed; retrieval and dispatch stay deterministic. The private
operator runtime performs model/provider preflight, injects the prompt's dynamic structured-output
schema and returns a redacted execution receipt. The workflow handler validates the output again
before LangGraph advances.

## Operator record

The design was checked against these operator contracts:

- `world://operator/guardrail/boundary-conflation@1`: passed plane coverage, handoff completeness
  and rebuildability; workflow meaning, orchestration, knowledge, authority and action remain
  separate.
- `world://operator/guardrail/configuration-runtime@1`: partial until the shared service records
  the complete effective service configuration in durable run receipts. Prompt execution now
  records the selected provider/model and redacted configuration returned by operator preflight.
- `world://operator/guardrail/evaluation-schema@1`: structural and runtime conformance are separate;
  semantic usefulness evaluators remain workflow-specific handlers.
- `world://operator/guardrail/workspace-isolation@1`: static envelope containment is enforced;
  production runtime storage/cache isolation remains required.
- `world://operator/guardrail/retry-idempotency@1`: action keys, bounded retries and replay semantics
  are represented; production durability remains required.
- `world://operator/guardrail/validation-persistence-conflation@1`: validation does not imply
  canonical persistence; workflow authority distinguishes proposal and canonical writes.

## Next increments

1. Replace the example handlers with production retrieval, operator and action adapters as each
   capability is promoted.
2. Add durable LangGraph checkpoint storage and crash resume.
3. Add OAuth 2.1, signed/version-pinned publication and catalog lifecycle management.
4. Add complete JSON Schema validation, event streaming, cancellation and resume APIs.
5. Certify cross-workspace denial, disclosure minimization, crash recovery, action compensation and
   agent tool discovery end to end.

The authenticated REST/MCP composition root and durable SQLite run/idempotency store are now
implemented as the second foundation increment. MCP uses the official pinned Python SDK and
publishes one typed tool per workflow visible to the configured principal.

The first executable certification uses `evaluation-schema@1` inside the evidence loop and
`validation-persistence-conflation@1` at synthesis. Their separate evaluator and persistence
fields are recorded in handler receipts; dispatch remains proposal-only and never writes canonical
product state. `configuration-runtime@1` remains partial because the service does not yet bind a
complete redacted effective-configuration manifest to every run receipt.
