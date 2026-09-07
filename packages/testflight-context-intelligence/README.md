# Context intelligence engine

This package compiles a workflow-specific, evidence-grounded context packet for an agent. It has
no Cordis or Cognee imports. Runtime seams are the `IntelligenceModel` and `KnowledgeRetriever`
interfaces, so the same engine can later sit behind HTTP or MCP without changing its decisions or
packet contract.

The engine deliberately separates retrieval eligibility from semantic synthesis. A small
deterministic filter removes obvious boundary failures; the separately configured intelligence
model interprets and organizes the remaining evidence. It never writes to a knowledge store.

The package also provides a provider-neutral `JsonVisualLanguageResolver`. It composes immutable
visual-language revisions and reusable reference modules by explicit scope and valid time. Audience
segments are ordinary selectors within a brand workspace. The resolver returns typed partial,
needs-clarification, and no-hit outcomes, preserves gaps and rights, and never selects a version by
embedding similarity.
