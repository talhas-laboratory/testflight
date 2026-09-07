from pathlib import Path

from testflight_brand import load_brand_ontology_release

ROOT = Path(__file__).resolve().parents[3]


def test_candidate_brand_ontology_modules_are_versioned_and_endpoint_checked() -> None:
    release, sources = load_brand_ontology_release(ROOT)

    assert release.id == "world://ontology/brand-system-v2"
    assert release.version == "2.0.0-candidate"
    assert release.status == "candidate"
    assert len(sources) == 8
    assert (
        release.relationship("world://ontology/brand/relation/operationalizes").family
        == "strategic"
    )
    assert (
        release.relationship("world://ontology/brand/relation/interprets").family == "perspectival"
    )
