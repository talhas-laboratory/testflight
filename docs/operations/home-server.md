# Home server synchronization

The server is a deployment/build checkout; GitHub remains the source of truth.

## One-time access setup

1. Ensure the SSH service is running and port 22 is reachable from this machine.
2. Create a dedicated SSH key if one is not already available.
3. Install only the public key in the server user's `authorized_keys`.
4. Verify non-interactive access with `ssh -o BatchMode=yes home-server true`.

Do not put a password or private key in this repository.

## Synchronize

Commit and push `main`, then run:

```bash
make sync-server
```

Override the defaults with `TESTFLIGHT_SERVER`, `TESTFLIGHT_REMOTE_DIR`,
`TESTFLIGHT_REPOSITORY`, or `TESTFLIGHT_BRANCH`. The script refuses dirty local and server
checkouts, non-fast-forward changes, unsafe paths, and password prompts.

## Cognee environment

The server uses Python 3.12 and keeps Cognee isolated from the system interpreter. The bootstrap
uses `uv` when available; install it once in the user account if needed:

```bash
UV_INSTALL_DIR="$HOME/.local" UV_NO_MODIFY_PATH=1 \
  curl -LsSf https://astral.sh/uv/install.sh | sh
```

After syncing the checkout, run:

```bash
cd /home/talha/testflight
./scripts/setup_server_cognee.sh
source .venv-cognee/bin/activate
```

The script installs the pinned Cognee release through the owned adapter and finishes with the
adapter health probe. `.venv-cognee/` is ignored and never synchronized through Git.
