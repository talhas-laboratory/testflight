#!/usr/bin/env python3
"""Validate the provider-free multimodal Content golden fixture."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = REPO_ROOT / "reasoning" / "fixtures" / "content" / "multimodal-profile.yaml"
EXPECTED_GATE_STATUSES = {"hold", "partial", "no_hit"}


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return value


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} contains duplicate IDs")


def validate_fixture(path: Path = DEFAULT_FIXTURE) -> dict[str, Any]:
    payload = _mapping(yaml.safe_load(path.read_text(encoding="utf-8")), "fixture")
    if payload.get("version") != 1:
        raise ValueError("fixture version must be 1")
    if payload.get("fixture_family") != "multimodal-content-profile-gold":
        raise ValueError("unexpected fixture family")
    rights = _mapping(payload.get("rights"), "rights")
    if "analysis" not in _list(rights.get("permitted_use"), "rights.permitted_use"):
        raise ValueError("fixture must be cleared for analysis")

    units = [
        _mapping(item, "content unit")
        for item in _list(payload.get("content_units"), "content_units")
    ]
    unit_ids = [str(item.get("content_unit_id", "")) for item in units]
    _unique(unit_ids, "content units")
    if len(units) != 3:
        raise ValueError("gold fixture must contain exactly three independent content units")

    track_ids: set[str] = set()
    segment_ids: set[str] = set()
    observation_ids: set[str] = set()
    observation_units: dict[str, str] = {}
    unavailable_modalities = 0
    for unit in units:
        unit_id = str(unit["content_unit_id"])
        duration_ms = unit.get("duration_ms")
        if not isinstance(duration_ms, int) or duration_ms <= 0:
            raise ValueError(f"{unit_id} duration must be a positive integer")
        local_tracks = [
            _mapping(item, f"{unit_id} track")
            for item in _list(unit.get("tracks"), f"{unit_id}.tracks")
        ]
        for track in local_tracks:
            track_id = str(track.get("track_id", ""))
            if not track_id or track_id in track_ids:
                raise ValueError(f"invalid or duplicate track ID: {track_id}")
            track_ids.add(track_id)
            if track.get("status") == "unavailable":
                unavailable_modalities += 1
                if not track.get("omission"):
                    raise ValueError(f"unavailable track needs an omission: {track_id}")
        local_segments = [
            _mapping(item, f"{unit_id} segment")
            for item in _list(unit.get("segments"), f"{unit_id}.segments")
        ]
        for segment in local_segments:
            segment_id = str(segment.get("segment_id", ""))
            start = segment.get("start_ms")
            end = segment.get("end_ms")
            if not segment_id or segment_id in segment_ids:
                raise ValueError(f"invalid or duplicate segment ID: {segment_id}")
            if (
                not isinstance(start, int)
                or not isinstance(end, int)
                or not 0 <= start < end <= duration_ms
            ):
                raise ValueError(f"invalid segment range: {segment_id}")
            segment_ids.add(segment_id)
        local_observations = [
            _mapping(item, f"{unit_id} observation")
            for item in _list(unit.get("observations"), f"{unit_id}.observations")
        ]
        for observation in local_observations:
            observation_id = str(observation.get("observation_id", ""))
            anchors = [
                str(item) for item in _list(observation.get("anchors"), f"{observation_id}.anchors")
            ]
            if not observation_id or observation_id in observation_ids:
                raise ValueError(f"invalid or duplicate observation ID: {observation_id}")
            if not anchors:
                raise ValueError(f"observation has no anchors: {observation_id}")
            observation_ids.add(observation_id)
            observation_units[observation_id] = unit_id
        interpretation = _mapping(unit.get("interpretation"), f"{unit_id}.interpretation")
        evidence_refs = [
            str(item)
            for item in _list(
                interpretation.get("evidence_refs"), f"{unit_id}.interpretation.evidence_refs"
            )
        ]
        if not evidence_refs or not set(evidence_refs).issubset(observation_ids):
            raise ValueError(f"interpretation has unknown evidence: {unit_id}")

    allowed_anchors = track_ids | segment_ids
    for unit in units:
        for observation in unit["observations"]:
            unknown = set(observation["anchors"]) - allowed_anchors
            if unknown:
                raise ValueError(f"observation has unknown anchors: {sorted(unknown)}")

    occurrences = [
        _mapping(item, "occurrence") for item in _list(payload.get("occurrences"), "occurrences")
    ]
    occurrence_ids = [str(item.get("occurrence_id", "")) for item in occurrences]
    _unique(occurrence_ids, "occurrences")
    occurrence_units: dict[str, str] = {}
    for occurrence in occurrences:
        occurrence_id = str(occurrence["occurrence_id"])
        unit_id = str(occurrence.get("content_unit_id", ""))
        refs = {
            str(item)
            for item in _list(occurrence.get("observation_ids"), f"{occurrence_id}.observation_ids")
        }
        if unit_id not in unit_ids or not refs or not refs.issubset(observation_ids):
            raise ValueError(f"occurrence references unknown content: {occurrence_id}")
        if any(observation_units[ref] != unit_id for ref in refs):
            raise ValueError(f"occurrence crosses content-unit boundaries: {occurrence_id}")
        occurrence_units[occurrence_id] = unit_id

    patterns = [
        _mapping(item, "pattern")
        for item in _list(payload.get("pattern_candidates"), "pattern_candidates")
    ]
    if not patterns:
        raise ValueError("fixture needs a pattern candidate")
    for pattern in patterns:
        pattern_id = str(pattern.get("pattern_id", ""))
        refs = [
            str(item)
            for item in _list(pattern.get("occurrence_ids"), f"{pattern_id}.occurrence_ids")
        ]
        counterexamples = {
            str(item)
            for item in _list(
                pattern.get("counterexample_observation_ids"),
                f"{pattern_id}.counterexample_observation_ids",
            )
        }
        if not refs or not set(refs).issubset(occurrence_units):
            raise ValueError(f"pattern has unknown occurrences: {pattern_id}")
        if len({occurrence_units[ref] for ref in refs}) < 2:
            raise ValueError(f"pattern needs at least two independent content units: {pattern_id}")
        if not counterexamples or not counterexamples.issubset(observation_ids):
            raise ValueError(f"pattern needs valid counterexamples: {pattern_id}")
        if pattern.get("expected_status") != "scoped_pattern":
            raise ValueError(f"fixture pattern must remain scoped: {pattern_id}")

    gates = [_mapping(item, "gate case") for item in _list(payload.get("gate_cases"), "gate_cases")]
    gate_ids = [str(item.get("gate_case_id", "")) for item in gates]
    _unique(gate_ids, "gate cases")
    statuses = {str(item.get("expected_status", "")) for item in gates}
    if not EXPECTED_GATE_STATUSES.issubset(statuses):
        raise ValueError("fixture must cover hold, partial, and no_hit outcomes")
    if any(not item.get("expected_reason") for item in gates):
        raise ValueError("every gate case needs an expected reason")

    if unavailable_modalities < 1:
        raise ValueError("fixture must include an unavailable modality")
    return {
        "status": "certified",
        "content_unit_count": len(units),
        "track_count": len(track_ids),
        "segment_count": len(segment_ids),
        "observation_count": len(observation_ids),
        "pattern_count": len(patterns),
        "gate_case_count": len(gates),
        "unavailable_modality_count": unavailable_modalities,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    args = parser.parse_args()
    result = validate_fixture(args.fixture)
    print(
        "validated multimodal Content fixture: "
        f"units={result['content_unit_count']} observations={result['observation_count']} "
        f"patterns={result['pattern_count']} gates={result['gate_case_count']} "
        f"status={result['status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
