# Testflight integration laboratory design

## Objective

Create a product-neutral space in which many open-source projects can be evaluated, combined,
replaced, and deployed without turning the repository into a tightly coupled source dump.

## Architecture

Testflight is a polyglot integration monorepo. The repository owns contracts, adapters,
experiments, deployment definitions, tests, and documentation. External software is represented
by a registry entry with an immutable commit, release, license, runtime, and integration mode.
Released packages are preferred, service containers come next, and submodules or forks require
a recorded architectural reason.

Adapters are the only locations allowed to import upstream-specific APIs. The initial contracts
describe broad capabilities and health, leaving detailed memory, orchestration, and agent-runtime
interfaces to emerge from real experiments. Cognee begins as an optional memory adapter,
LangGraph as an optional orchestration adapter, and DeepSeek Harness as an isolated plugin/runtime
boundary. None depends on another.

## Data and execution

Applications compose adapters through owned contracts. Experiments can bypass stable contracts
temporarily, but must remain in `experiments/` until their integration boundary is understood.
Code and configuration move through GitHub. Databases, model weights, checkpoints, generated
knowledge stores, and secrets live outside Git and have independent backup policies.

## Failure handling

Adapters load upstream libraries lazily and provide dependency-free health probes. A missing
optional integration degrades only that capability. Upstream upgrades change the registry pin in
the same review as adapter and contract-test changes. Server synchronization permits only clean,
fast-forward checkouts and refuses to replace an existing non-Git directory.

## Testing

Every adapter has descriptor and health tests. The upstream registry is structurally validated,
secret-bearing files and obvious credentials are rejected, Python and TypeScript receive static
checks, and Compose configuration is parsed. Networked upstream smoke tests are explicit rather
than part of the lightweight default suite.

## Operations

Python, Node, uv, and pnpm versions are declared through mise, with Make available as the
portable task runner. GitHub is canonical. This machine and the home server use ordinary clones;
the server is updated over key-based SSH only. Production deployment remains container-oriented
without selecting a provider before a real workload establishes storage and compute needs.
