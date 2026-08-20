from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from brand_ontology_fixtures import snapshot_at, validate_all_fixture_worlds  # noqa: E402
from validate_brand_ontology_fixtures import validate_fixtures  # noqa: E402


def test_all_synthetic_worlds_are_executable() -> None:
    worlds = validate_all_fixture_worlds()

    assert len(worlds) == 9
    assert {world.world_id for world in worlds} == {f"SW-{index:03d}" for index in range(1, 10)}
    assert all(world.objects for world in worlds)


def test_fixture_catalog_and_invariants_are_certified() -> None:
    result = validate_fixtures()

    assert result["status"] == "certified"
    assert result["world_count"] == 9


def test_bitemporal_fixture_replays_knowledge_history() -> None:
    world = next(world for world in validate_all_fixture_worlds() if world.world_id == "SW-007")

    before = snapshot_at(
        world,
        valid_at=datetime(2025, 2, 1, tzinfo=UTC),
        known_at=datetime(2025, 2, 1, tzinfo=UTC),
    )
    after = snapshot_at(
        world,
        valid_at=datetime(2025, 2, 1, tzinfo=UTC),
        known_at=datetime(2025, 4, 1, tzinfo=UTC),
    )

    assert before[0].object_value == "calm infrastructure"
    assert after[0].object_value == "observable infrastructure"
