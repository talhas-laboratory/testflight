# Reasoning-operator workspace

This is the container pack for the 16 reasoning guardrail operators. The
canonical contracts live in [`../../reasoning/operators/`](../../reasoning/operators/);
this workspace references them instead of copying them.

The workspace has two uses:

1. Agents can read the tracked pack locally and route a task through the
   smallest operator without needing Cognee.
2. The home-server population command can rebuild the dedicated Cognee dataset
   `testflight_reasoning_operators` from the same Git revision.

Start with:

- [`AGENT_INDEX.md`](AGENT_INDEX.md) for routing;
- [`AGENT_CONFIG.yaml`](AGENT_CONFIG.yaml) for policy and quality gates;
- [`WORKSPACE.yaml`](WORKSPACE.yaml) for identity, scope, and topology; and
- [`resource_registry.json`](resource_registry.json) for source metadata.

## Populate the server projection

Validate without touching Cognee:

```bash
uv run python scripts/populate_reasoning_operator_workspace.py --validate-only
```

Preview the exact bounded documents:

```bash
uv run python scripts/populate_reasoning_operator_workspace.py --dry-run
```

After the checkout is synchronized on the home server:

```bash
make setup-server-reasoning-operators
```

The command writes only ignored runtime state under `.data/cognee/`. It is
idempotent by operator/version/source identity and records a redacted report;
it never writes an API key to the repository or output.

## Retrieval posture

Route to the smallest child view, use lexical/BM25 retrieval first, escalate
only to bounded same-container hybrid search on an in-domain lexical no-hit,
and use graph traversal only for explicit path queries. Index/config documents
are navigation/policy sources, not final answers. An unsupported query returns
`NO_HITS`.
