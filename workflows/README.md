# Declarative workflows

Workflow definitions are versioned YAML capabilities exposed to authorized agents through a shared
catalog. Start from `examples/evidence-synthesis.yaml`.

That example is assigned directly to `agent:testflight-research`. The shared runtime compiles its
four steps into LangGraph and registers the concrete local handlers in `runtime.example.yaml`.

An author normally changes only:

1. `access`: the agents or roles allowed to discover and invoke the workflow;
2. `knowledge`: the maximum workspaces, containers and entities visible during a run;
3. `authority`: every capability and action granted after access succeeds;
4. `inputs_schema` and `outputs_schema`: the agent-facing tool contract;
5. `steps`: registered handler IDs, explicit dependencies and value bindings; and
6. `outputs`: mappings from step results into the public response.

Each step can add a versioned `instruction`. Add `instruction.prompt` when the handler should call
a model. The prompt declares system/user templates, its exact output schema, runtime operator ID,
version, modality and non-secret configuration. Use only `{{ inputs.<path> }}` and
`{{ arguments.<path> }}` placeholders. The step's `access` and `capabilities` remain the binding
authority; prose inside a prompt cannot widen either one. Prompt-backed steps must explicitly
declare `model.invoke`.

Use `$inputs.<name>`, `$steps.<step-id>.output`, `$run.id`, and, inside loop arguments, `$item` or
`$index`. Independent steps with satisfied dependencies can run in parallel. Add `when` conditions
for branches. Use a `loop` step with `foreach` and `max_iterations` for bounded fan-out; workflow
graphs themselves remain acyclic. Every `action` requires declared action IDs and an idempotency
key.

Validate all registered definitions with:

```bash
uv run --package testflight-workflows python scripts/validate_workflows.py
```

Print the authoring JSON Schema with `--schema`.
