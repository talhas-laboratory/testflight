#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
node_bin="${TESTFLIGHT_NODE_BIN:-node}"
dsh_home="${TESTFLIGHT_DSH_HOME:-$repo_root/.data/deepseek-harness}"
store_dir="$dsh_home/pnpm-store"

cd "$repo_root"

if ! command -v "$node_bin" >/dev/null 2>&1; then
  echo "Node.js is required; set TESTFLIGHT_NODE_BIN or install Node.js 22+" >&2
  exit 1
fi
node_major="$($node_bin -p 'Number(process.versions.node.split(".")[0])')"
if [[ "$node_major" -lt 22 ]]; then
  echo "DeepSeek Harness requires Node.js 22 or newer (found $($node_bin --version))" >&2
  exit 1
fi

mkdir -p "$dsh_home" "$store_dir"

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

version="$(run_pnpm --config.store-dir="$store_dir" dlx @deepseek-ai/dsh@0.1.0-rc.7 --version)"
if [[ "$version" != "0.1.0-rc.7" ]]; then
  echo "Unexpected DeepSeek Harness version: $version" >&2
  exit 1
fi

echo "DeepSeek Harness ready: $version"
echo "DSH_HOME: $dsh_home"
echo "Launch with: ./scripts/run_deepseek_harness.sh"
