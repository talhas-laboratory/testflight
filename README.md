# Testflight

Testflight is a polyglot integration laboratory for evaluating and combining open-source
software behind stable, locally owned interfaces.

The repository deliberately starts without a product. Its job is to make experiments
reproducible, upstream upgrades reviewable, and successful integrations easy to promote into
reusable packages or independently deployable services.

## Principles

- Keep upstream projects replaceable through adapters.
- Pin every upstream release or commit in `upstreams/registry.yaml`.
- Prefer package releases and service containers over copied source.
- Use submodules or forks only when a documented experiment requires upstream changes.
- Keep code in Git; keep secrets, model weights, databases, and generated data outside Git.
- Make every adapter testable without requiring every other adapter.

## Repository map

| Path | Purpose |
| --- | --- |
| `apps/` | Runnable experiments and future products |
| `packages/` | Stable contracts and shared libraries |
| `adapters/` | Replaceable upstream integrations |
| `services/` | Independently deployable processes |
| `experiments/` | Disposable, time-boxed proofs of concept |
| `infra/` | Local and deployment infrastructure |
| `upstreams/` | Source, version, license, and integration registry |
| `docs/` | Designs, decisions, and research |
| `scripts/` | Setup, validation, and synchronization tools |

## Quick start

Prerequisites are Python 3.13, Node.js 24, `uv`, and Corepack/pnpm. `mise` can install the
versions declared in `.mise.toml`, but it is optional.

```bash
make setup
make check
```

If `just` is installed, equivalent commands are available through `just setup` and
`just check`.

Install an upstream only when working on it:

```bash
uv sync --all-packages --extra cognee --extra langgraph
pnpm --filter @testflight/deepseek-harness-adapter upstream:version
```

On the home server, set up Cognee in its own ignored virtual environment with:

```bash
./scripts/setup_server_cognee.sh
```

See [the integration guide](docs/integrations/adding-an-upstream.md) before adding another
project and [the server guide](docs/operations/home-server.md) before enabling synchronization.

## Current integrations

- Cognee: optional Python memory adapter with lazy dependency loading.
- LangGraph: optional Python orchestration adapter with lazy dependency loading.
- DeepSeek Harness: isolated Node integration boundary and pinned CLI probe.

No integration is coupled to another yet.
