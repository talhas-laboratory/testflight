# DeepSeek Harness context intelligence plugin

This native Cordis plugin connects DeepSeek Harness to the provider-neutral Testflight context
intelligence engine. It registers `compile_context` and optionally injects a context snapshot on
the first model step of brand-dependent workflow turns.

The plugin does not import Cognee. It starts the Cognee adapter's read-only JSON process bridge,
explicitly scoped to the configured staging dataset. Configure the separate intelligence model:

```sh
TESTFLIGHT_INTELLIGENCE_MODEL=provider/model-id
TESTFLIGHT_INTELLIGENCE_BASE_URL=https://openrouter.ai/api/v1
TESTFLIGHT_INTELLIGENCE_API_KEY_ENV=OPENROUTER_API_KEY
```

The intelligence model is never inherited from `TESTFLIGHT_DSH_MODEL`. Without it, the engine may
still return a `partial` packet using exact workflow configuration and lexical evidence. No path
writes to Cognee.

## Visual-language context

When enabled by the workspace configuration, the plugin loads a provider-neutral visual-language
manifest and resolves it before model synthesis. Resolution is deterministic: explicit brand,
product, offer, campaign, audience-segment, channel, geography, occasion, and valid-time selectors
choose an immutable profile revision. A global profile can be composed with compatible audience or
offer overlays. Versions are never selected by embedding similarity, and conflicts or missing
scope return a typed partial/no-hit result.

The manifest is modular. A reference can represent a palette, typography role, grid, image
direction, motion principle, UI pattern, example, or a future registered kind. Each reference
retains authority, epistemic status, rights, source/evidence ids, and limitations. Public
observations are marked for inspiration or analysis; they do not become proprietary production
rules. The Nike pilot lives in
`workspaces/brand-nike-research/visual-language/manifest.json`.

Use `inspect_visual_language` to resolve a scope and date directly. It returns the governing
profile revisions, composed references, omissions, and conflicts without calling either the
intelligence model or the main Harness model.

## Inspection traces

Each context compilation creates an owner-readable append-only journal under
`.data/context-intelligence/traces/<run-id>/`. Events are written as the run progresses, so an
interrupted run remains inspectable. Exact evidence bodies are content-addressed once under the
run's `evidence/` directory; journal events reference their hashes instead of duplicating them.

The packet receipt distinguishes selected, directly retrieved, merely mentioned, and actually
used entity IDs. The Harness lifecycle link adds the final visible assistant response to the same
journal while excluding reasoning blocks. Use the `inspect_context_trace` tool with the returned
`runId`; set `includeEvidence: true` only when exact raw evidence text is needed.

Traces never contain credentials or hidden chain-of-thought and are never written to Cognee. The
default retention is 200 runs or 30 days. Configure `traceDirectory`, `traceMaxRuns`, and
`traceMaxAgeDays`, or their `TESTFLIGHT_CONTEXT_TRACE_*` environment equivalents, to change local
storage and retention.
