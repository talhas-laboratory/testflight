# DeepSeek Harness adapter

DeepSeek Harness is a developer preview with a plugin-first Cordis architecture. This package
is intentionally isolated and pins its CLI release and repository commit. Configuration is kept
in an out-of-tree profile overlay rather than patching its agent loop.

`pnpm --filter @testflight/deepseek-harness-adapter upstream:version` performs an explicit,
networked CLI probe.

## Configurable OpenRouter profile

The tracked [OpenRouter patch](config/openrouter.cordis.patch.yml) replaces the Harness
`llm-pi-ai` seam with a hand-declared OpenAI-compatible route. It references
`OPENROUTER_API_KEY` through `apiKeyEnv` and reads the model from `TESTFLIGHT_DSH_MODEL`; no
credentials or model choice are stored in the repository.

Set a model in the ignored `.env` file, then launch from the repository root:

```sh
TESTFLIGHT_DSH_MODEL=your-openrouter-model ./scripts/run_deepseek_harness.sh \
  "inspect the current Testflight integration boundaries"
```

The default profile is `headless`. Select `web` with `TESTFLIGHT_DSH_PROFILE`; set
`TESTFLIGHT_DSH_BASE_URL` for a compatible proxy. Harness state, sessions, and its isolated pnpm
store live under `.data/deepseek-harness/`, which is ignored by Git.

Use `--dump-config` as the last argument to inspect the composed profile without making an LLM
request:

```sh
TESTFLIGHT_DSH_MODEL=your-openrouter-model ./scripts/run_deepseek_harness.sh --dump-config
```
