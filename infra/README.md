# Infrastructure

`compose.yaml` starts only an opt-in workspace shell. Persistent services should be added as
separate Compose fragments owned by the experiment or service that needs them. This prevents
early database and platform choices from becoming accidental architecture.

Cloudflare Containers or another managed container host can later run stateless services.
Persistent memory, checkpoints, and knowledge graphs must use an external durable store rather
than a container filesystem.
