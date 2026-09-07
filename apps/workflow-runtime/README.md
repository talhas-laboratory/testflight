# Workflow Runtime

Shared, authenticated composition root for declarative workflows. It loads the tracked workflow
registry, registers explicitly configured handler modules, stores runs and action idempotency in an
ignored SQLite database, executes the step graph through LangGraph, and exposes REST plus MCP
through the owned transport adapter.

The example uses the existing operator runtime for its prompt-backed evaluation and synthesis
nodes. Start that private runtime with provider configuration supplied only through the
environment, then start the workflow service:

```bash
# terminal 1
make serve-operator-runtime

# terminal 2
TESTFLIGHT_WORKFLOW_TOKEN_RESEARCH='local-secret' workflow-runtime \
  --config workflows/runtime.example.yaml
```

REST is available on `127.0.0.1:8782`; MCP is mounted at `/mcp/` when `mcp_principal_id` is set.
Both surfaces require the selected agent's bearer credential; `/health` is the only public route.
The tracked configuration assigns the evidence-synthesis workflow to
`agent:testflight-research` and registers local handlers that retrieve the scoped research catalog,
evaluate records, synthesize a proposal, and dispatch that proposal into ignored runtime data.
Handler modules are loaded only from explicit configuration and must expose
`register_workflow_handlers(registry, configuration)`.

The workflow runtime sends rendered prompts, scoped arguments, disclosure references and the
node's output schema to `127.0.0.1:8781`. It never reads provider credentials. The operator runtime
performs provider preflight and returns provider/model identity in a redacted receipt; the workflow
handler validates the returned JSON again before LangGraph can advance.

LangGraph owns graph scheduling and an in-process checkpoint seam. SQLite owns durable run records
and action idempotency; durable LangGraph checkpoints and crash resume remain a later increment.

The local bearer-token authenticator is an initial deployment seam. Internet-facing deployment
must replace it with OAuth 2.1 audience validation and an explicit MCP transport-security allowlist.
