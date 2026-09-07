# Testflight Workflows

Provider-neutral contracts, validation, compilation and reference execution for reusable agent
workflows. A workflow is a versioned capability: if an authenticated principal can invoke it, the
runtime grants exactly the knowledge and action authority declared by that workflow for that run.
The caller cannot add containers, entities, tools, credentials or actions.

Definitions are ordinary YAML. Steps refer to registered handlers and exchange values through
explicit references such as `$inputs.prompt` and `$steps.retrieve.items`. Dependencies form an
acyclic graph; independent ready steps may execute in parallel. Conditions skip branches, and a
loop step maps one handler over a bounded collection without introducing graph cycles.

Every step may declare a versioned `instruction` with an objective and rules. Model-backed steps
also declare a `prompt` containing system/user templates, a structured output schema, a non-secret
model configuration and an operator-runtime route. Templates can interpolate only explicit
`{{ inputs.* }}` and `{{ arguments.* }}` paths. Knowledge visibility remains a separate `access`
envelope, so prompt text cannot grant itself another workspace or container.

The package intentionally contains no LangGraph, model-provider, storage, retrieval or application
imports. `WorkflowEngine` is the executable reference semantics and the conformance target for
orchestration adapters. LangGraph-specific graph construction and checkpoint selection belong in
`adapters/langgraph`.

The first example is `workflows/examples/evidence-synthesis.yaml`.
