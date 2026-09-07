import pytest
from testflight_adapter_creative_connectors import (
    ConnectorPreflightError,
    ImageTargetAdapter,
    TextTargetAdapter,
    compile_generation_packet,
)
from testflight_creative_field import FieldProjection


def _projection(modality: str) -> FieldProjection:
    return FieldProjection(
        projection_id=f"projection:{modality}",
        field_version_id="field:one@1",
        request_id="request:one",
        lens="hero",
        modality=modality,
        principles=("Keep quiet confidence",),
        tensions=("precise and warm",),
        exclusions=("literal copying",),
        dimension_mappings={"visual": {"summary": "restrained"}},
        grounding_reference_ids=("asset:one",),
        sufficiency="sufficient",
        derivation_id="derivation:projection",
    )


def test_text_and_image_adapters_receive_only_compiled_supported_packets() -> None:
    text_packet = compile_generation_packet(
        _projection("text"),
        TextTargetAdapter(lambda packet: "a grounded text artifact").manifest,
        disclosure_manifest_id="disclosure:one",
        grounding_asset_ids=("asset:one",),
        permitted_asset_ids=("asset:one",),
    )
    image_packet = compile_generation_packet(
        _projection("image"),
        ImageTargetAdapter(lambda packet: b"PNG").manifest,
        disclosure_manifest_id="disclosure:one",
        grounding_asset_ids=(),
        permitted_asset_ids=(),
    )
    text_result = TextTargetAdapter(lambda packet: "a grounded text artifact").invoke(
        text_packet, invocation_id="invoke:text"
    )
    image_result = ImageTargetAdapter(lambda packet: b"PNG").invoke(
        image_packet, invocation_id="invoke:image"
    )
    assert text_result.output is not None
    assert text_result.output.media_type == "text/plain"
    assert image_result.output is not None
    assert image_result.output.media_type == "image/png"
    assert text_result.receipt.disclosure_manifest_id == "disclosure:one"


def test_connector_preflight_rejects_uncleared_assets_and_wrong_modality() -> None:
    adapter = TextTargetAdapter(lambda packet: "never called")
    with pytest.raises(ConnectorPreflightError, match="not permitted"):
        compile_generation_packet(
            _projection("text"),
            adapter.manifest,
            disclosure_manifest_id="disclosure:one",
            grounding_asset_ids=("asset:restricted",),
            permitted_asset_ids=(),
        )
    with pytest.raises(ConnectorPreflightError, match="does not accept"):
        compile_generation_packet(
            _projection("image"),
            adapter.manifest,
            disclosure_manifest_id="disclosure:one",
        )


def test_connector_failure_is_normalized_without_field_mutation() -> None:
    adapter = TextTargetAdapter(lambda packet: (_ for _ in ()).throw(RuntimeError("target down")))
    packet = compile_generation_packet(
        _projection("text"),
        adapter.manifest,
        disclosure_manifest_id="disclosure:one",
    )
    result = adapter.invoke(packet, invocation_id="invoke:failed")
    assert result.output is None
    assert result.status.value == "failed"
    assert result.receipt.errors == ("target down",)
