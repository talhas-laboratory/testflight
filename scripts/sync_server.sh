#!/usr/bin/env bash
set -euo pipefail

server="${TESTFLIGHT_SERVER:-talha@192.168.0.102}"
remote_dir="${TESTFLIGHT_REMOTE_DIR:-/home/talha/testflight}"
repository="${TESTFLIGHT_REPOSITORY:-https://github.com/talhas-laboratory/testflight.git}"
branch="${TESTFLIGHT_BRANCH:-main}"

if [[ ! "$server" =~ ^[A-Za-z0-9._-]+@[A-Za-z0-9._:-]+$ ]]; then
  echo "TESTFLIGHT_SERVER has an unsafe format" >&2
  exit 2
fi
if [[ ! "$remote_dir" =~ ^/[A-Za-z0-9._/-]+$ ]] || [[ "$remote_dir" == "/" ]]; then
  echo "TESTFLIGHT_REMOTE_DIR must be a specific absolute path" >&2
  exit 2
fi
if [[ ! "$branch" =~ ^[A-Za-z0-9._/-]+$ ]]; then
  echo "TESTFLIGHT_BRANCH has an unsafe format" >&2
  exit 2
fi

git diff --quiet
git diff --cached --quiet
git fetch origin "$branch"
local_sha="$(git rev-parse HEAD)"
remote_sha="$(git rev-parse "origin/$branch")"
if [[ "$local_sha" != "$remote_sha" ]]; then
  echo "Local HEAD must match origin/$branch before server sync" >&2
  exit 3
fi

ssh -o BatchMode=yes "$server" sh -s -- "$remote_dir" "$repository" "$branch" <<'REMOTE'
set -eu
remote_dir="$1"
repository="$2"
branch="$3"

if [ -d "$remote_dir/.git" ]; then
  git -C "$remote_dir" diff --quiet
  git -C "$remote_dir" diff --cached --quiet
  git -C "$remote_dir" fetch origin "$branch"
  git -C "$remote_dir" checkout "$branch"
  git -C "$remote_dir" merge --ff-only "origin/$branch"
elif [ -e "$remote_dir" ]; then
  echo "Refusing to replace non-Git path: $remote_dir" >&2
  exit 4
else
  mkdir -p "$(dirname "$remote_dir")"
  git clone --branch "$branch" --single-branch "$repository" "$remote_dir"
fi
REMOTE

echo "Server checkout synchronized to $local_sha"
