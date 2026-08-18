#!/usr/bin/env python3
"""Validate the upstream registry without fetching or executing upstream code."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "upstreams" / "registry.yaml"
SHA = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_INTEGRATIONS = {"container", "fork", "package", "plugin", "submodule"}


def main() -> None:
    document = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    if document.get("schema_version") != 1:
        raise SystemExit("unsupported upstream registry schema")

    upstreams = document.get("upstreams")
    if not isinstance(upstreams, list) or not upstreams:
        raise SystemExit("registry must contain at least one upstream")

    seen: set[str] = set()
    for entry in upstreams:
        identifier = entry.get("id")
        if not isinstance(identifier, str) or identifier in seen:
            raise SystemExit(f"invalid or duplicate upstream id: {identifier!r}")
        seen.add(identifier)
        if not str(entry.get("repository", "")).startswith("https://github.com/"):
            raise SystemExit(f"{identifier}: repository must be a GitHub HTTPS URL")
        if not SHA.fullmatch(str(entry.get("commit", ""))):
            raise SystemExit(f"{identifier}: commit must be a full 40-character SHA")
        if entry.get("integration") not in ALLOWED_INTEGRATIONS:
            raise SystemExit(f"{identifier}: unsupported integration mode")
        adapter = ROOT / str(entry.get("adapter", ""))
        if not adapter.is_dir():
            raise SystemExit(f"{identifier}: adapter directory does not exist")
        for required in ("license", "release", "runtime", "status"):
            if not entry.get(required):
                raise SystemExit(f"{identifier}: missing {required}")

    print(f"validated {len(upstreams)} pinned upstreams")


if __name__ == "__main__":
    main()
