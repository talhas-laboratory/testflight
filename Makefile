.PHONY: setup format lint test check registry compose-config sync-server

setup:
	corepack enable
	uv sync --all-packages
	pnpm install --frozen-lockfile

format:
	uv run ruff format .
	uv run ruff check --fix .
	pnpm run format

lint:
	uv run ruff format --check .
	uv run ruff check .
	uv run python scripts/validate_registry.py
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
