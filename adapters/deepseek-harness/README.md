# DeepSeek Harness adapter

DeepSeek Harness is a developer preview with a plugin-first Cordis architecture. This package
is intentionally isolated and pins both its CLI release and repository commit. Future work
should integrate through an out-of-tree Harness plugin or profile overlay rather than patching
its agent loop.

`pnpm --filter @testflight/deepseek-harness-adapter upstream:version` performs an explicit,
networked CLI probe.
