import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parent


def load_cases() -> dict:
    with (FIXTURE_DIR / "cases.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_testing_context() -> dict:
    with (FIXTURE_DIR / "testing_context.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_biotic_newsletter_compose_golden_pack_exists() -> None:
    payload = load_cases()
    testing_context = load_testing_context()
    assert payload["node_name"] == "biotic_newsletter_compose"
    assert payload["node_type"] == "planner"
    assert payload["cases"]
    assert testing_context["node_name"] == "biotic_newsletter_compose"


def test_biotic_newsletter_compose_cases_cover_required_contracts() -> None:
    payload = load_cases()
    cases = payload["cases"]
    testing_context = load_testing_context()

    assert {case["case_id"] for case in cases} == {
        "positive_golden",
        "edge_unknown_context",
        "failure_missing_evidence",
        "guardrail_product_pressure",
        "regression_claim_lineage",
    }
    assert testing_context["semantic_success_definition"]
    assert testing_context["prohibited_outcomes"]
    assert "composition_id must survive compose" in testing_context["preservation_rules"][0]
