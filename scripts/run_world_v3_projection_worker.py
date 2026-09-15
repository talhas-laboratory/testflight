#!/usr/bin/env python3
"""Run one durable, accepted World v3 -> Cognee graph rebuild job.

The script is intentionally a single-writer command.  Run it from one service
process (or schedule it), never from multiple desktop sessions against Ladybug.
"""

from __future__ import annotations

import argparse
import asyncio
import time
from pathlib import Path

from testflight_adapter_cognee import WorldV3ProjectionWorker
from testflight_adapter_sqlite_semantic import SQLiteWorldRepository
from testflight_world import WorldService


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world-db", type=Path, required=True)
    parser.add_argument(
        "--manifest-root",
        type=Path,
        default=Path(".data/world-v3-projections"),
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="continuously claim jobs; required for automatic projection updates",
    )
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=2.0,
        help="idle delay in watch mode (default: 2 seconds)",
    )
    args = parser.parse_args()
    if args.poll_seconds <= 0:
        parser.error("--poll-seconds must be positive")
    with SQLiteWorldRepository(args.world_db) as repository:
        worker = WorldV3ProjectionWorker(
            outbox=repository,
            world=WorldService(repository),
            manifest_root=args.manifest_root,
        )
        while True:
            result = asyncio.run(worker.run_once())
            if result is not None:
                print(result)
            elif not args.watch:
                print("No pending World v3 projection job.")
                return 0
            if args.watch:
                time.sleep(args.poll_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
