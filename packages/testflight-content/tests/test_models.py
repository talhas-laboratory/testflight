from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError
from testflight_content import (
    ContentArtifactStatus,
    ContentBundle,
    ContentEpistemicStatus,
    ContentInterpretation,
    ContentOccurrence,
    ContentSegment,
    ContentUnit,
    InterpretationFrame,
    MediaTrack,
    PatternCandidate,
    PatternScope,
    PerceptualObservation,
    SourceEnvelope,
)

FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "reasoning"
    / "fixtures"
    / "content"
    / "multimodal-profile.yaml"
)


def _base_records() -> dict:
    payload = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    sources = tuple(
        SourceEnvelope(
            source_envelope_id=f"source-envelope:{index}",
            project_id="project:test",
            workspace_id="workspace:test",
            source_system="synthetic-social",
            provider_source_id=item["source_envelope_id"],
            acquisition_method="fixture",
            acquisition_receipt_id=f"receipt:{index}",
            recorded_at="2026-09-01T00:00:00Z",
            privacy_classification="synthetic",
            rights_record_id="license:synthetic-profile",
            retention_policy="repository_fixture",
            derivation_id=f"derivation:source:{index}",
        )
        for index, item in enumerate(payload["content_units"], start=1)
    )
    units = tuple(
        ContentUnit(
            content_unit_id=item["content_unit_id"],
            source_envelope_id=sources[index].source_envelope_id,
            content_kind=item["kind"],
            recorded_at="2026-09-01T00:00:00Z",
            published_at=str(item["published_at"]),
            duration_ms=item["duration_ms"],
            profile_subject_id="content-profile:verdant-lab",
            derivation_id=f"derivation:unit:{index}",
        )
        for index, item in enumerate(payload["content_units"])
    )
    tracks = tuple(
        MediaTrack(
            track_id=track["track_id"],
            content_unit_id=unit["content_unit_id"],
            modality=track["modality"],
            status=ContentArtifactStatus(track["status"]),
            limitation=track.get("omission"),
            derivation_id=f"derivation:track:{track['track_id']}",
        )
        for unit in payload["content_units"]
        for track in unit["tracks"]
    )
    segments = tuple(
        ContentSegment(
            segment_id=segment["segment_id"],
            content_unit_id=unit["content_unit_id"],
            start_ms=segment["start_ms"],
            end_ms=segment["end_ms"],
            roles=tuple(segment["roles"]),
            segmentation_method="fixture",
            derivation_id=f"derivation:segment:{segment['segment_id']}",
        )
        for unit in payload["content_units"]
        for segment in unit["segments"]
    )
    observations = tuple(
        PerceptualObservation(
            observation_id=observation["observation_id"],
            content_unit_id=unit["content_unit_id"],
            modality=next(
                track["modality"]
                for track in unit["tracks"]
                if any(anchor == track["track_id"] for anchor in observation["anchors"])
            ),
            observation_type="fixture_observation",
            dimension=observation["dimension"],
            value=observation["value"],
            anchor_ids=tuple(observation["anchors"]),
            observer_id="observer:fixture",
            operator_id="world://operator/creative/observation-extraction",
            operator_version=1,
            epistemic_status=ContentEpistemicStatus(observation.get("status", "observed")),
            derivation_id=f"derivation:observation:{observation['observation_id']}",
        )
        for unit in payload["content_units"]
        for observation in unit["observations"]
    )
    occurrences = tuple(
        ContentOccurrence(
            occurrence_id=item["occurrence_id"],
            content_unit_id=item["content_unit_id"],
            label="calm-expert",
            observation_ids=tuple(item["observation_ids"]),
            derivation_id=f"derivation:occurrence:{item['occurrence_id']}",
        )
        for item in payload["occurrences"]
    )
    patterns = tuple(
        PatternCandidate(
            pattern_id=item["pattern_id"],
            target_scope=PatternScope(item["target_scope"]),
            sampled_content_unit_ids=tuple(item["sampled_content_unit_ids"]),
            occurrence_ids=tuple(item["occurrence_ids"]),
            counterexample_observation_ids=tuple(item["counterexample_observation_ids"]),
            proposition=item["proposition"],
            transfer_conditions=tuple(item["transfer_conditions"]),
            derivation_id=f"derivation:pattern:{item['pattern_id']}",
        )
        for item in payload["pattern_candidates"]
    )
    return {
        "source_envelopes": sources,
        "content_units": units,
        "tracks": tracks,
        "segments": segments,
        "observations": observations,
        "occurrences": occurrences,
        "patterns": patterns,
    }


def _bundle(**updates: object) -> ContentBundle:
    records = _base_records()
    records.update(updates)
    return ContentBundle(
        bundle_id="bundle:synthetic-profile",
        project_id="project:test",
        workspace_id="workspace:test",
        **records,
    )


def test_certified_fixture_maps_to_a_valid_content_bundle() -> None:
    bundle = _bundle()

    assert len(bundle.content_units) == 3
    assert len(bundle.observations) == 11
    assert bundle.patterns[0].target_scope is PatternScope.PROFILE_SAMPLE


def test_unavailable_track_requires_limitation() -> None:
    with pytest.raises(ValidationError, match="require a limitation"):
        MediaTrack(
            track_id="track:missing",
            content_unit_id="content:reel-03",
            modality="audio",
            status=ContentArtifactStatus.UNAVAILABLE,
            derivation_id="derivation:track:missing",
        )


def test_bundle_rejects_unknown_observation_anchor() -> None:
    observations = list(_base_records()["observations"])
    observations[0] = observations[0].model_copy(update={"anchor_ids": ("segment:unknown",)})

    with pytest.raises(ValidationError, match="unknown anchor"):
        _bundle(observations=tuple(observations))


def test_bundle_rejects_cross_unit_occurrence() -> None:
    observations = _base_records()["observations"]
    occurrences = list(_base_records()["occurrences"])
    occurrences[0] = occurrences[0].model_copy(
        update={"observation_ids": (observations[-1].observation_id,)}
    )

    with pytest.raises(ValidationError, match="crosses content-unit"):
        _bundle(occurrences=tuple(occurrences))


def test_bundle_rejects_non_local_pattern_without_independent_units() -> None:
    occurrences = list(_base_records()["occurrences"])
    pattern = _base_records()["patterns"][0].model_copy(
        update={"occurrence_ids": (occurrences[0].occurrence_id,)}
    )

    with pytest.raises(ValidationError, match="independent content units"):
        _bundle(patterns=(pattern,))


def test_bundle_rejects_source_scope_mismatch() -> None:
    sources = list(_base_records()["source_envelopes"])
    sources[0] = sources[0].model_copy(update={"workspace_id": "workspace:other"})

    with pytest.raises(ValidationError, match="source envelope scope"):
        _bundle(source_envelopes=tuple(sources))


def test_bundle_requires_declared_interpretation_frame() -> None:
    interpretation = ContentInterpretation(
        interpretation_id="interpretation:reel-01",
        content_unit_ids=("content:reel-01",),
        frame_id="frame:missing",
        proposition="a bounded fixture interpretation",
        category="brand_posture",
        supporting_evidence_ids=("observation:reel-01:claim",),
        target_scope="content_unit",
        authority="operator-proposal",
        derivation_id="derivation:interpretation:reel-01",
    )

    with pytest.raises(ValidationError, match="unknown frame"):
        _bundle(interpretations=(interpretation,))


def test_interpretation_frame_is_provider_independent() -> None:
    frame = InterpretationFrame(
        frame_id="frame:social-brand-reading-v1",
        version=1,
        question="What expressed brand posture is supported by this profile sample?",
        module_id="module:social-analysis",
        module_version=1,
        target_scope="profile_sample",
        context_id="context:test",
        branch_id="branch:analysis",
        requested_dimensions=("rhetorical", "temporal", "social-strategic"),
        uncertainty_policy="branch",
        output_schema="ContentInterpretation",
        evaluator_refs=("evaluator:evidence-coverage",),
        derivation_id="derivation:frame:social-brand-reading-v1",
    )

    assert frame.inference_depth.value == "descriptive"


def test_segments_require_an_explicit_anchor() -> None:
    with pytest.raises(ValidationError, match="need time, text, or spatial anchors"):
        ContentSegment(
            segment_id="segment:empty",
            content_unit_id="content:reel-01",
            segmentation_method="fixture",
            derivation_id="derivation:segment:empty",
        )
