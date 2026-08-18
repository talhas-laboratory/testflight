set dotenv-load := true

setup:
    make setup

format:
    make format

lint:
    make lint

test:
    make test

check:
    make check

up:
    docker compose -f infra/compose.yaml --profile workspace up -d

down:
    docker compose -f infra/compose.yaml --profile workspace down

sync-server:
    ./scripts/sync_server.sh

setup-server-reasoning-operators:
    ./scripts/setup_server_reasoning_operators.sh
