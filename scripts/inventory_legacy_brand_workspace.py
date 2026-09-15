#!/usr/bin/env python3
"""Emit a machine-readable, read-only inventory of a legacy Brand workspace."""

from __future__ import annotations

import argparse
from pathlib import Path

from testflight_brand import inventory_legacy_brand_workspace


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "workspace",
        type=Path,
        help="Workspace directory containing WORKSPACE.yaml and legacy artifacts.",
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root used to resolve ontology releases and consumer paths.",
    )
    arguments = parser.parse_args()
    inventory = inventory_legacy_brand_workspace(
        arguments.repository_root,
        arguments.workspace,
    )
    print(inventory.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
