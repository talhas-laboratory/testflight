# DeepSeek Harness configuration environment

Status: initial implementation design

## Goal

Provide a reproducible, configurable DeepSeek Harness runtime without modifying the upstream
agent loop or committing provider credentials, model weights, sessions, or profile state.

## Architecture

- The existing TypeScript adapter remains a thin invocation boundary. It pins
  `@deepseek-ai/dsh@0.1.0-rc.7`, validates profile names, and builds a launcher command with an
  optional patch overlay.
- `openrouter.cordis.patch.yml` uses the upstream `@deepseek-ai/dsh-llm-pi-ai` seam. OpenRouter is
  declared as an OpenAI-compatible route with `apiKeyEnv: OPENROUTER_API_KEY` and a model ID
  supplied at runtime by `TESTFLIGHT_DSH_MODEL`.
- `run_deepseek_harness.sh` loads the ignored project `.env`, requires a model ID, selects
  `headless` or `web`, and sets an isolated `DSH_HOME` under `.data`.
- `setup_server_deepseek_harness.sh` validates Node.js and prefetches the pinned CLI into a
  server-local pnpm store. It does not boot an agent or make an LLM request.

## Data flow

1. `.env` supplies the OpenRouter key and model/provider settings.
2. The launcher exports `DSH_HOME` and applies the tracked patch layer.
3. Harness resolves the `openrouter` route through `dsh-llm-pi-ai`.
4. Sessions and profile state stay in ignored `.data/deepseek-harness/` paths.

## Safety and failure behavior

- Missing model, unsupported profile, missing patch, unsupported Node.js, or missing pnpm/Corepack
  fails before the Harness starts.
- The patch contains no credential value. The key is referenced by environment name only.
- `--dump-config` is the boot-free configuration inspection path; setup/version checks do not make
  provider calls.
- OpenRouter model IDs are intentionally not selected by this repository. The user chooses the
  model in `.env`, so model capability and cost remain explicit deployment decisions.

## Future extension

Additional provider routes, reasoning capability declarations, profile-specific patches, and
LangGraph/Cognee bridge plugins can be added as separate overlays without changing this adapter's
invocation contract.
