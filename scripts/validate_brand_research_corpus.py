#!/usr/bin/env python3
"""Validate the bounded Brand research anchor corpus and proposal layer."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = REPO_ROOT / "workspaces/brand-ontology-research"

SOURCE_REQUIRED = {
    "id",
    "title",
    "authors",
    "year",
    "canonical_url",
    "source_type",
    "authority_tier",
    "research_lenses",
    "methodology",
    "stakeholder_perspective",
    "geography",
    "language",
    "use",
    "status",
}
EVIDENCE_REQUIRED = {
    "id",
    "source_id",
    "locator",
    "evidence_status",
    "note",
    "supports",
    "limitations",
}
SPAN_REQUIRED = {"id", "source_id", "note_id", "locator", "span_mode"}
CANDIDATE_REQUIRED = {
    "candidate_id",
    "semantic_kind",
    "module",
    "proposed_version",
    "status",
    "necessary_definition",
    "inclusion_rules",
    "exclusion_rules",
    "examples",
    "counterexamples",
    "source_refs_or_fixture_refs",
    "competency_question_ids",
    "uncertainty",
    "derivation_id",
    "reasoning_operators",
    "evaluator_receipt",
}
ALLOWED_SOURCE_TIERS = {"A", "B", "C", "D", "E"}
ALLOWED_EVIDENCE_STATUS = {
    "observed",
    "reported",
    "inferred",
    "hypothesized",
    "normative",
    "retracted",
    "unresolved",
}
ALLOWED_CANDIDATE_STATUS = {
    "proposed",
    "evaluated",
    "accepted",
    "held",
    "rejected",
    "deprecated",
}


def _load(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a mapping")
    return payload


def validate_corpus(root: Path = REPO_ROOT) -> dict[str, Any]:
    workspace = root / "workspaces/brand-ontology-research"
    sources = _load(workspace / "artifacts/source-catalog.yaml").get("sources")
    evidence = _load(workspace / "artifacts/evidence-notes.yaml").get("notes")
    spans = _load(workspace / "artifacts/evidence-spans.yaml").get("spans")
    candidates = _load(workspace / "artifacts/candidate-definitions.yaml").get("candidates")
    questions = _load(workspace / "artifacts/competency-questions.yaml").get("questions")
    worlds = _load(workspace / "artifacts/synthetic-worlds.yaml").get("worlds")

    if not isinstance(sources, list) or len(sources) != 24:
        raise ValueError("anchor corpus must contain exactly 24 sources")
    if not isinstance(evidence, list) or len(evidence) != len(sources):
        raise ValueError("every anchor source must have one bounded evidence note")
    if not isinstance(spans, list) or len(spans) != len(evidence):
        raise ValueError("every evidence note must have one bounded source span")
    if not isinstance(candidates, list) or len(candidates) < 8:
        raise ValueError("corpus must contain at least eight candidate definitions")
    if not isinstance(questions, list) or len(questions) != 30:
        raise ValueError("corpus must use the complete 30-question catalogue")
    if not isinstance(worlds, list) or len(worlds) != 9:
        raise ValueError("corpus must retain all nine synthetic worlds")

    source_ids: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("source record must be a mapping")
        missing = SOURCE_REQUIRED - set(source)
        if missing:
            raise ValueError(f"source {source.get('id')} missing {sorted(missing)}")
        source_id = source["id"]
        if source_id in source_ids:
            raise ValueError(f"duplicate source id: {source_id}")
        source_ids.add(source_id)
        if source["authority_tier"] not in ALLOWED_SOURCE_TIERS:
            raise ValueError(f"invalid authority tier for {source_id}")
        if not isinstance(source["canonical_url"], str) or not source["canonical_url"].startswith(
            ("https://", "http://")
        ):
            raise ValueError(f"source {source_id} needs a canonical URL")
        if not source["research_lenses"]:
            raise ValueError(f"source {source_id} needs at least one research lens")

    question_ids = {question["id"] for question in questions}
    world_ids = {world["id"] for world in worlds}
    evidence_ids: set[str] = set()
    covered_questions: set[str] = set()
    for note in evidence:
        if not isinstance(note, dict):
            raise ValueError("evidence note must be a mapping")
        missing = EVIDENCE_REQUIRED - set(note)
        if missing:
            raise ValueError(f"evidence note {note.get('id')} missing {sorted(missing)}")
        if note["id"] in evidence_ids:
            raise ValueError(f"duplicate evidence id: {note['id']}")
        evidence_ids.add(note["id"])
        if note["source_id"] not in source_ids:
            raise ValueError(f"evidence note references unknown source: {note['source_id']}")
        if note["evidence_status"] not in ALLOWED_EVIDENCE_STATUS:
            raise ValueError(f"invalid evidence status: {note['evidence_status']}")
        if not note["supports"]:
            raise ValueError(f"evidence note {note['id']} must support a question")
        unknown = set(note["supports"]) - question_ids
        if unknown:
            raise ValueError(f"evidence note {note['id']} references unknown questions: {unknown}")
        covered_questions.update(note["supports"])

    span_ids: set[str] = set()
    note_ids = {note["id"] for note in evidence}
    span_sources: set[str] = set()
    for span in spans:
        if not isinstance(span, dict):
            raise ValueError("evidence span must be a mapping")
        missing = SPAN_REQUIRED - set(span)
        if missing:
            raise ValueError(f"evidence span {span.get('id')} missing {sorted(missing)}")
        if span["id"] in span_ids:
            raise ValueError(f"duplicate evidence span id: {span['id']}")
        span_ids.add(span["id"])
        if span["source_id"] not in source_ids:
            raise ValueError(f"evidence span references unknown source: {span['source_id']}")
        if span["note_id"] not in note_ids:
            raise ValueError(f"evidence span references unknown note: {span['note_id']}")
        if span["span_mode"] != "faithful_paraphrase":
            raise ValueError(
                "anchor spans must be faithful paraphrases until licensed excerpts exist"
            )
        span_sources.add(span["source_id"])
    if span_sources != source_ids:
        raise ValueError("bounded source spans must cover every anchor source")

    candidate_ids: set[str] = set()
    candidate_statuses: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("candidate definition must be a mapping")
        missing = CANDIDATE_REQUIRED - set(candidate)
        if missing:
            raise ValueError(f"candidate {candidate.get('candidate_id')} missing {sorted(missing)}")
        candidate_id = candidate["candidate_id"]
        if candidate_id in candidate_ids:
            raise ValueError(f"duplicate candidate id: {candidate_id}")
        candidate_ids.add(candidate_id)
        candidate_statuses.add(candidate["status"])
        if candidate["status"] not in ALLOWED_CANDIDATE_STATUS:
            raise ValueError(f"invalid candidate status: {candidate['status']}")
        if len(candidate["source_refs_or_fixture_refs"]) < 2:
            raise ValueError(f"candidate {candidate_id} needs independent source or fixture refs")
        for ref in candidate["source_refs_or_fixture_refs"]:
            if ref.startswith("SRC-") and ref not in source_ids:
                raise ValueError(f"candidate {candidate_id} references unknown source {ref}")
            if ref.startswith("SW-") and ref not in world_ids:
                raise ValueError(f"candidate {candidate_id} references unknown world {ref}")
            if not (ref.startswith("SRC-") or ref.startswith("SW-")):
                raise ValueError(f"candidate {candidate_id} has malformed reference {ref}")
        unknown = set(candidate["competency_question_ids"]) - question_ids
        if unknown:
            raise ValueError(f"candidate {candidate_id} references unknown questions: {unknown}")
        if not candidate["counterexamples"]:
            raise ValueError(f"candidate {candidate_id} needs a counterexample")
        if not candidate["reasoning_operators"]:
            raise ValueError(f"candidate {candidate_id} needs operator receipts")
        receipt = candidate["evaluator_receipt"]
        if not isinstance(receipt, dict) or receipt.get("status") not in {
            "pass",
            "partial",
            "hold",
            "fail",
        }:
            raise ValueError(f"candidate {candidate_id} needs an independent evaluator receipt")
        covered_questions.update(candidate["competency_question_ids"])

    if covered_questions != question_ids:
        raise ValueError(
            f"question coverage incomplete: {sorted(question_ids - covered_questions)}"
        )
    if "held" not in candidate_statuses:
        raise ValueError("at least one candidate must remain held to prove conservative promotion")
    if any(source["authority_tier"] != "A" for source in sources):
        raise ValueError("anchor corpus currently expects authoritative Tier A sources only")

    lens_count = len({lens for source in sources for lens in source["research_lenses"]})
    methodology_count = len({source["methodology"] for source in sources})
    stakeholder_count = len({source["stakeholder_perspective"] for source in sources})
    geography_count = len({source["geography"] for source in sources})
    source_type_count = len({source["source_type"] for source in sources})
    if lens_count < 10 or methodology_count < 8 or stakeholder_count < 8 or geography_count < 4:
        raise ValueError("anchor corpus does not meet its diversity minimums")

    return {
        "source_count": len(sources),
        "evidence_count": len(evidence),
        "span_count": len(spans),
        "candidate_count": len(candidates),
        "question_count": len(question_ids),
        "world_count": len(world_ids),
        "covered_question_count": len(covered_questions),
        "candidate_statuses": sorted(candidate_statuses),
        "diversity": {
            "research_lenses": lens_count,
            "methodologies": methodology_count,
            "stakeholders": stakeholder_count,
            "geographies": geography_count,
            "source_types": source_type_count,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()
    result = validate_corpus(args.root)
    print(
        "validated Brand research corpus: "
        f"sources={result['source_count']} evidence={result['evidence_count']} "
        f"candidates={result['candidate_count']} questions={result['covered_question_count']} "
        f"worlds={result['world_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
