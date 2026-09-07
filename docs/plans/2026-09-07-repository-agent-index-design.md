# Repository-wide agent index design

## Decision

Use a concise root `AGENT_INDEX.md` as the universal repository navigation entrypoint while
preserving distributed module and workspace indexes as their local sources of truth.

## Why

A fully generated catalog would enumerate paths reliably but would not explain semantic ownership
or supported connections. Relying only on distributed indexes would preserve local ownership but
would leave a new agent without a discoverable starting point. The root-map approach provides one
stable entrypoint, classifies every layer, and points to the smallest authoritative module without
copying its domain content.

## Contract

The root index must:

- identify every application, package, adapter, domain, top-level knowledge workspace, Testflight
  Product child module, reasoning layer, workflow layer, and infrastructure/operations layer;
- state what each module owns, where it lives, how it is used, and its supported connections;
- distinguish navigation/configuration from evidence and declared state from observed runtime;
- describe the supported knowledge-to-agent, workflow-to-agent, operator-runtime, and persistence
  paths;
- provide creation and validation routes without embedding secrets or generated runtime state; and
- defer detailed behavior to each owning module's local README, index, contract, or registry.

`AGENTS.md` and the repository README link to this index so both automated agents and human readers
encounter it early. Link integrity and the complete repository check are the acceptance tests.

## Reasoning-operator record

- `world://operator/guardrail/boundary-conflation@1`: pass. The index separates domain evidence,
  knowledge projections, application composition, runtime execution, authority, and agent access.
- `world://operator/guardrail/configuration-runtime@1`: partial. The index distinguishes declared
  configuration from runtime proof; live providers and live retrieval are not asserted.
- `world://operator/guardrail/evaluation-schema@1`: pass for this navigation artifact. Structural
  validation, link checks, repository tests, and knowledge-workspace validation are independent
  acceptance dimensions.
