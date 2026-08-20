from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.validate_brand_research_corpus import validate_corpus  # noqa: E402


def test_anchor_corpus_is_complete_and_question_covered() -> None:
    result = validate_corpus()

    assert result["source_count"] == 24
    assert result["evidence_count"] == 24
    assert result["span_count"] == 24
    assert result["candidate_count"] >= 8
    assert result["covered_question_count"] == 30
    assert result["world_count"] == 9
    assert result["diversity"]["research_lenses"] >= 10
    assert result["diversity"]["methodologies"] >= 8
    assert result["diversity"]["stakeholders"] >= 8
    assert result["diversity"]["geographies"] >= 4


def test_corpus_keeps_conservative_promotion_state() -> None:
    result = validate_corpus()

    assert "held" in result["candidate_statuses"]
