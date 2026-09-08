import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parent


def load_semantic_cases() -> dict:
    with (FIXTURE_DIR / "semantic_cases.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_biotic_newsletter_compose_semantic_pack_exists() -> None:
    payload = load_semantic_cases()
    assert payload["node_name"] == "biotic_newsletter_compose"
    assert payload["pack_type"] == "semantic_adherence"
    assert payload["cases"]


def test_biotic_newsletter_compose_semantic_case_defines_visible_output_rules() -> None:
    payload = load_semantic_cases()
    cases = payload["cases"]

    requirements = cases[0]["semantic_requirements"]
    assert "review_package.draft" in requirements["target_output_paths"]
    assert "medical advice" in requirements["must_not_express"]
    assert requirements["alignment_paths"]["product_role"]
