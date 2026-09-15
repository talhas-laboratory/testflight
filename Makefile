.PHONY: setup setup-server-cognee setup-server-deepseek-harness setup-server-context-intelligence setup-server-reasoning-operators setup-server-brand-research setup-server-brand-research-certification run-deepseek-harness build-context-intelligence build-operator-runtime serve-operator-runtime serve-workflow-runtime serve-brand-world serve-world-v3-projection format lint test check registry workflows product-workspace product-workspace-projection brand-research-workspace brand-research-corpus brand-research-fixtures brand-research-projection brand-research-certification brand-world-v3-certification biotic-newsletter-world-context content-fixtures nike-research-workspace nike-research-projection creative-field-certification compose-config sync-server

setup:
	corepack enable
	uv sync --all-packages
	pnpm install --frozen-lockfile

setup-server-cognee:
	./scripts/setup_server_cognee.sh

setup-server-deepseek-harness:
	./scripts/setup_server_deepseek_harness.sh

setup-server-context-intelligence:
	./scripts/setup_server_context_intelligence.sh

setup-server-reasoning-operators:
	./scripts/setup_server_reasoning_operators.sh

setup-server-brand-research:
	./scripts/setup_server_brand_research.sh $(ARGS)

setup-server-brand-research-certification:
	./scripts/setup_server_brand_research_certification.sh $(ARGS)

run-deepseek-harness:
	./scripts/run_deepseek_harness.sh

build-context-intelligence:
	pnpm --filter @testflight/context-intelligence build

build-operator-runtime:
	pnpm --filter @testflight/operator-runtime build

serve-operator-runtime: build-operator-runtime
	node scripts/serve_operator_runtime.mjs

serve-workflow-runtime: build-context-intelligence
	uv run --package testflight-workflow-runtime workflow-runtime

serve-brand-world:
	uv run --package testflight-brand-world brand-world

serve-world-v3-projection:
	@test -n "$(WORLD_V3_DB)" || (echo "Set WORLD_V3_DB to the canonical World SQLite path" >&2; exit 2)
	uv run python scripts/run_world_v3_projection_worker.py --world-db "$(WORLD_V3_DB)" --watch

format:
	uv run ruff format .
	uv run ruff check --fix .
	pnpm run format

lint:
	uv run ruff format --check .
	uv run ruff check .
	uv run python scripts/validate_registry.py
	uv run python scripts/validate_reasoning_operators.py
	uv run python scripts/validate_skill_catalog.py
	uv run --package testflight-workflows python scripts/validate_workflows.py
	uv run python scripts/check_secrets.py
	pnpm run check

test:
	uv run --all-packages pytest
	pnpm test

check: lint test product-workspace brand-research-workspace content-fixtures nike-research-workspace creative-field-certification compose-config

registry:
	uv run python scripts/validate_registry.py

workflows:
	uv run --package testflight-workflows python scripts/validate_workflows.py

product-workspace:
	uv run python scripts/validate_testflight_product_workspace.py
	uv run python scripts/audit_testflight_product_routes.py --summary

product-workspace-projection:
	uv run python scripts/populate_testflight_product_workspace.py --dry-run

brand-research-workspace: brand-research-corpus brand-research-fixtures
	python3 scripts/validate_brand_ontology_workspace.py

brand-research-corpus:
	python3 scripts/validate_brand_research_corpus.py

brand-research-fixtures:
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH=scripts uv run python scripts/validate_brand_ontology_fixtures.py; \
	elif [ -x "$${TESTFLIGHT_COGNEE_VENV:-.venv-cognee}/bin/python" ]; then \
		PYTHONPATH=scripts:packages/testflight-semantic/src "$${TESTFLIGHT_COGNEE_VENV:-.venv-cognee}/bin/python" scripts/validate_brand_ontology_fixtures.py; \
	else \
		echo "uv or TESTFLIGHT_COGNEE_VENV is required for fixture validation" >&2; exit 1; \
	fi

brand-research-projection:
	uv run python scripts/populate_brand_research_workspace.py --dry-run

brand-research-certification:
	uv run python scripts/certify_brand_research_projection.py --help

brand-world-v3-certification:
	uv run --all-packages pytest packages/testflight-semantic/tests packages/testflight-brand/tests packages/testflight-world/tests adapters/sqlite-semantic/tests -q
	uv run --package testflight-brand python scripts/certify_brand_world_v3.py
	pnpm --filter @testflight/context-intelligence test

biotic-newsletter-world-context:
	$(MAKE) build-context-intelligence
	echo '{"objective":"Reason about Biotic’s public Brand World and identify the strongest, safest newsletter territory.","request_id":"request:biotic-newsletter-world-reasoning"}' | TESTFLIGHT_PROJECT_ROOT=$(CURDIR) node packages/testflight-context-intelligence/scripts/compile-biotic-newsletter-world.mjs

content-fixtures:
	uv run python scripts/validate_multimodal_content_fixtures.py

nike-research-workspace:
	uv run python scripts/validate_concrete_brand_workspace.py

nike-research-projection:
	uv run python scripts/populate_concrete_brand_workspace.py --dry-run

creative-field-certification:
	uv run --all-packages python scripts/certify_creative_field.py --report .data/creative-field/certification.json

compose-config:
	docker compose -f infra/compose.yaml config --quiet

sync-server:
	./scripts/sync_server.sh
