#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
dsh_home="${TESTFLIGHT_DSH_HOME:-$repo_root/.data/deepseek-harness}"
profile="${TESTFLIGHT_DSH_PROFILE:-headless}"
model="${TESTFLIGHT_DSH_MODEL:-}"
patch_file="${TESTFLIGHT_DSH_PATCH:-$repo_root/adapters/deepseek-harness/config/openrouter.cordis.patch.yml}"
store_dir="$dsh_home/pnpm-store"

cd "$repo_root"
if [[ -f "$repo_root/.env" ]]; then
  set -a
  # .env is local-only and is required to hold the provider credential reference.
  # shellcheck disable=SC1091
  . "$repo_root/.env"
  set +a
  dsh_home="${TESTFLIGHT_DSH_HOME:-$dsh_home}"
  profile="${TESTFLIGHT_DSH_PROFILE:-$profile}"
  model="${TESTFLIGHT_DSH_MODEL:-$model}"
  patch_file="${TESTFLIGHT_DSH_PATCH:-$patch_file}"
  store_dir="$dsh_home/pnpm-store"
fi

case "$profile" in
  headless|web) ;;
  *)
    echo "TESTFLIGHT_DSH_PROFILE must be headless or web" >&2
    exit 2
    ;;
esac
if [[ -z "$model" ]]; then
  echo "Set TESTFLIGHT_DSH_MODEL to an OpenRouter model id before launching" >&2
  exit 2
fi
if [[ ! -f "$patch_file" ]]; then
  echo "Harness patch file does not exist: $patch_file" >&2
  exit 2
fi

mkdir -p "$dsh_home" "$store_dir"
export DSH_HOME="$dsh_home"

run_pnpm() {
  if command -v corepack >/dev/null 2>&1; then
    COREPACK_ENABLE_DOWNLOAD_PROMPT=0 corepack pnpm "$@"
  elif command -v pnpm >/dev/null 2>&1; then
    pnpm "$@"
  else
    echo "pnpm or Corepack is required to run DeepSeek Harness" >&2
    exit 1
  fi
}

run_pnpm --config.store-dir="$store_dir" dlx @deepseek-ai/dsh@0.1.0-rc.7 \
  --profile "$profile" --patch "$patch_file" "$@"
