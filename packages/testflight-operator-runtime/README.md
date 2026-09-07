# Testflight Operator Runtime

Provider-neutral execution boundary for versioned reasoning operators. Operators are registered
with typed input/output validators and providers advertise capability manifests. Preflight checks
scope, disclosure, modality, structured-output support and policy before any provider call.

The runtime returns proposal, partial, branch, ask, no-hit, hold or failed outcomes and records a
receipt with provider/model identity, redacted configuration, disclosure references, attempts and
call counts. Idempotency is keyed by the caller-supplied operation key. The OpenAI-compatible
adapter uses `fetch` directly so provider SDKs remain outside the domain and can be replaced by a
fake or another compatible endpoint.

The runtime also registers `runtime://testflight/workflow/prompt-step` for prompt-backed LangGraph
nodes. A trusted workflow supplies its versioned prompt contract and node-specific JSON Schema in
configuration. The provider receives that schema as strict structured-output guidance, while the
workflow runtime independently validates the result before the next node runs.

`createOperatorRuntimeHttpServer` exposes the same runtime through a bounded local `POST /execute`
JSON endpoint and `GET /health`. The transport accepts snake_case invocation fields used by the
Python Creative Studio adapter and returns normalized snake_case receipts. It is an application
boundary, not a public internet API; authentication, process supervision and network exposure are
owned by the composition root.

For a Luna deployment, configure the compatible provider with `modelId: "gpt-5.6-luna"` and pass
`reasoning_effort: "max"` in the invocation configuration. The runtime records the model and
redacts credentials in its receipt; it does not make the model a domain dependency.

The repository composition-root launcher is `make serve-operator-runtime`. It builds this package,
reads `TESTFLIGHT_OPERATOR_BASE_URL` and the environment named by
`TESTFLIGHT_OPERATOR_API_KEY_ENV`, and binds the local transport to `127.0.0.1:8781` by default.
Keep this endpoint private; it is intended to be called by Creative Studio, not exposed directly to
clients or the public internet.
