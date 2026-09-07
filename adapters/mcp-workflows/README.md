# MCP Workflows adapter

Agent-facing transport boundary for the shared workflow runtime. It uses the pinned official MCP
Python SDK and exposes authorized workflows through MCP tools. The generic discovery and invocation
tools support every workflow; startup can additionally project each visible workflow as a named,
typed tool.

The adapter does not decide access or grant authority. It receives an already authenticated
`WorkflowPrincipal` and calls the provider-neutral runtime service. MCP annotations describe side
effects to clients but are never treated as authorization.

Streamable HTTP should be bound to localhost during development. Production deployment requires
OAuth audience validation and an explicit transport-security allowlist.
