#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="${TESTFLIGHT_PYTHON:-python3}"
venv_dir="${TESTFLIGHT_COGNEE_VENV:-$repo_root/.venv-cognee}"
uv_bin=""

cd "$repo_root"

if [[ ! -e "$repo_root/.env" ]]; then
  umask 077
  {
    printf 'DATA_ROOT_DIRECTORY=%s\n' "$repo_root/.data/cognee/data"
    printf 'SYSTEM_ROOT_DIRECTORY=%s\n' "$repo_root/.data/cognee/system"
    printf 'COGNEE_LOGS_DIR=%s\n' "$repo_root/.data/cognee/logs"
  } > "$repo_root/.env"
fi

if command -v uv >/dev/null 2>&1; then
  uv_bin="$(command -v uv)"
elif [[ -x "$HOME/.local/uv" ]]; then
  uv_bin="$HOME/.local/uv"
fi

if [[ -n "$uv_bin" ]]; then
  "$uv_bin" venv --allow-existing --python "$python_bin" "$venv_dir"
elif [[ ! -x "$venv_dir/bin/python" ]]; then
  "$python_bin" -m venv "$venv_dir" || {
    echo "Python cannot create a venv; install uv or python3-venv and retry" >&2
    exit 1
  }
fi

venv_python="$venv_dir/bin/python"
if [[ -n "$uv_bin" ]]; then
  "$uv_bin" pip install --python "$venv_python" \
    --editable "$repo_root/packages/testflight-core" \
    --editable "$repo_root/packages/testflight-semantic" \
    --editable "$repo_root/packages/testflight-brand" \
    --editable "$repo_root/adapters/cognee[cognee]"
else
  "$venv_python" -m pip install --disable-pip-version-check --upgrade pip
  "$venv_python" -m pip install \
    --editable "$repo_root/packages/testflight-core" \
    --editable "$repo_root/packages/testflight-semantic" \
    --editable "$repo_root/packages/testflight-brand" \
    --editable "$repo_root/adapters/cognee[cognee]"
fi

"$venv_python" - <<'PY'
from pathlib import Path

from testflight_adapter_cognee import CogneeAdapter
from testflight_brand import load_brand_ontology
from testflight_core import HealthState
from testflight_semantic import Context, SemanticEntity

Context()
SemanticEntity(
    entity_id="health-check:brand",
    type_id="world://ontology/type/Brand",
    workspace_id="health-check",
    canonical_label="Health check",
    definition_version="0.1.0",
)
load_brand_ontology(Path.cwd())

report = CogneeAdapter().health()
print(f"cognee adapter: {report.state} — {report.message}")
if report.state is not HealthState.AVAILABLE:
    raise SystemExit("Cognee is not importable in the isolated environment")
PY

echo "Cognee environment ready: $venv_dir"
echo "Activate with: source $venv_dir/bin/activate"
