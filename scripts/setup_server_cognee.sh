#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="${TESTFLIGHT_PYTHON:-python3}"
venv_dir="${TESTFLIGHT_COGNEE_VENV:-$repo_root/.venv-cognee}"

if [[ ! -x "$venv_dir/bin/python" ]]; then
  "$python_bin" -m venv "$venv_dir"
fi

venv_python="$venv_dir/bin/python"
"$venv_python" -m pip install --disable-pip-version-check --upgrade pip
"$venv_python" -m pip install \
  --editable "$repo_root/packages/testflight-core" \
  --editable "$repo_root/adapters/cognee[cognee]"

"$venv_python" - <<'PY'
from testflight_adapter_cognee import CogneeAdapter
from testflight_core import HealthState

report = CogneeAdapter().health()
print(f"cognee adapter: {report.state} — {report.message}")
if report.state is not HealthState.AVAILABLE:
    raise SystemExit("Cognee is not importable in the isolated environment")
PY

echo "Cognee environment ready: $venv_dir"
echo "Activate with: source $venv_dir/bin/activate"
