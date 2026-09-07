#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
dsh_home="${TESTFLIGHT_DSH_HOME:-$repo_root/.data/deepseek-harness}"
profile="${TESTFLIGHT_DSH_PROFILE:-headless}"
store_dir="$dsh_home/pnpm-store"
pack_dir="$repo_root/.data/context-intelligence-pack"
shim_dir="$repo_root/.data/context-intelligence-bin"

cd "$repo_root"
corepack pnpm install --frozen-lockfile
corepack pnpm --filter @testflight/dsh-context-intelligence build
corepack pnpm --filter @testflight/dsh-context-intelligence health -- --strict
mkdir -p "$pack_dir"
corepack pnpm --filter @testflight/context-intelligence pack --pack-destination "$pack_dir"
corepack pnpm --filter @testflight/dsh-context-intelligence pack --pack-destination "$pack_dir"
engine_tar="$pack_dir/testflight-context-intelligence-0.1.0.tgz"
plugin_tar="$pack_dir/testflight-dsh-context-intelligence-0.1.0.tgz"

mkdir -p "$dsh_home" "$store_dir" "$shim_dir"
corepack enable --install-directory "$shim_dir"
export PATH="$shim_dir:$PATH"
export DSH_HOME="$dsh_home"
profile_manifest="$dsh_home/profiles/$profile/package.json"
remove_if_installed() {
  local package_name="$1"
  if [[ -f "$profile_manifest" ]] && node -e \
    'const value = require(process.argv[1]); process.exit(value.dependencies?.[process.argv[2]] ? 0 : 1)' \
    "$profile_manifest" "$package_name"; then
    corepack pnpm --config.store-dir="$store_dir" dlx @deepseek-ai/dsh@0.1.0-rc.7 \
      plugin --profile "$profile" remove "$package_name"
  fi
}
remove_if_installed @testflight/dsh-context-intelligence
remove_if_installed @testflight/context-intelligence
corepack pnpm --config.store-dir="$store_dir" dlx @deepseek-ai/dsh@0.1.0-rc.7 \
  plugin --profile "$profile" add --force "$engine_tar"
corepack pnpm --config.store-dir="$store_dir" dlx @deepseek-ai/dsh@0.1.0-rc.7 \
  plugin --profile "$profile" add --force "$plugin_tar"

echo "Context intelligence plugin installed in DeepSeek Harness profile: $profile"
