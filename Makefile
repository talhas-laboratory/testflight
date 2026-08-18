.PHONY: setup setup-server-cognee setup-server-deepseek-harness setup-server-reasoning-operators run-deepseek-harness format lint test check registry compose-config sync-server

setup:
	corepack enable
	uv sync --all-packages
	pnpm install --frozen-lockfile

setup-server-cognee:
	./scripts/setup_server_cognee.sh

setup-server-deepseek-harness:
	./scripts/setup_server_deepseek_harness.sh

setup-server-reasoning-operators:
	./scripts/setup_server_reasoning_operators.sh

run-deepseek-harness:
	./scripts/run_deepseek_harness.sh

format:
	uv run ruff format .
	uv run ruff check --fix .
	pnpm run format

lint:
	uv run ruff format --check .
	uv run ruff check .
	uv run python scripts/validate_registry.py
	uv run python scripts/validate_reasoning_operators.py
	uv run python scripts/check_secrets.py
	pnpm run check

test:
	uv run pytest
	pnpm test

check: lint test compose-config

registry:
	uv run python scripts/validate_registry.py

compose-config:
	docker compose -f infra/compose.yaml config --quiet

sync-server:
	./scripts/sync_server.sh
