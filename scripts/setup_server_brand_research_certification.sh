#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
venv_dir="${TESTFLIGHT_COGNEE_VENV:-$repo_root/.venv-cognee}"
venv_python="$venv_dir/bin/python"

if [[ ! -x "$venv_python" ]]; then
  echo "Cognee environment is missing: run ./scripts/setup_server_cognee.sh first" >&2
  exit 1
fi

export PYTHONPATH="$repo_root/scripts:$repo_root/packages/testflight-semantic/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$venv_python" "$repo_root/scripts/certify_brand_research_projection.py" "$@"
