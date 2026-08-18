#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
venv_dir="${TESTFLIGHT_COGNEE_VENV:-$repo_root/.venv-cognee}"
venv_python="$venv_dir/bin/python"

if [[ ! -x "$venv_python" ]]; then
  echo "Cognee environment is missing: run ./scripts/setup_server_cognee.sh first" >&2
  exit 1
fi

exec "$venv_python" "$repo_root/scripts/populate_reasoning_operator_workspace.py" "$@"
