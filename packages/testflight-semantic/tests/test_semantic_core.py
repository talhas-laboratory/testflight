import asyncio

from testflight_semantic import (
    EntityDefinition,
    EntityMatch,
    ExtractionResult,
    MatchType,
    RelationshipDefinition,
    RelationshipMatch,
    SemanticExtractor,
    compile_extraction_prompt,
    validate_extraction,
)


def idea_definition() -> EntityDefinition:
    return EntityDefinition(
        name="Idea",
        definition="A distinct proposal or design direction stated in the source.",
        relationships=(
            RelationshipDefinition(
                name="supports",
                source_entity="Idea",
                target_entity="Idea",
                definition="The source idea provides rationale for the target idea.",
            ),
        ),
    )


def test_validation_preserves_workspace_and_definition_in_stable_identity() -> None:
    result = ExtractionResult(
        matches=[
            EntityMatch(
                quote="graph memory",
                normalized_content="graph memory",
                match_type=MatchType.EXPLICIT,
            )
        ]
    )
    definition = idea_definition()
    first = validate_extraction(
        "A graph memory layer.", definition, result, "source-1", workspace_id="workspace-a"
    )
    second = validate_extraction(
        "A graph memory layer.", definition, result, "source-1", workspace_id="workspace-a"
    )
    other_workspace = validate_extraction(
        "A graph memory layer.", definition, result, "source-1", workspace_id="workspace-b"
    )

    assert first.occurrences[0].occurrence_id == second.occurrences[0].occurrence_id
    assert first.occurrences[0].occurrence_id != other_workspace.occurrences[0].occurrence_id


def test_prompt_exposes_definition_version_and_forbids_invention() -> None:
    prompt = compile_extraction_prompt(idea_definition())

    assert "DEFINITION VERSION: 1.0.0" in prompt
    assert "Do not invent entities" in prompt


def test_relationship_requires_exact_endpoint_and_evidence_quotes() -> None:
    definition = idea_definition()
    text = "Graph memory supports durable recall."
    result = ExtractionResult(
        matches=[
            EntityMatch(
                quote="Graph memory",
                normalized_content="graph memory",
                match_type=MatchType.EXPLICIT,
            ),
            EntityMatch(
                quote="durable recall",
                normalized_content="durable recall",
                match_type=MatchType.EXPLICIT,
            ),
        ],
        relationships=[
            RelationshipMatch(
                relationship_type="supports",
                source_quote="Graph memory",
                target_quote="durable recall",
                evidence_quote="supports",
            )
        ],
    )

    validated = validate_extraction(text, definition, result, "source-2")

    assert len(validated.relationships) == 1
    assert validated.relationships[0].start == text.index("supports")


def test_extractor_keeps_provider_output_separate_from_validation() -> None:
    async def fake_call(text: str, prompt: str, response_model: type[ExtractionResult]):
        assert text == "A graph memory idea."
        assert response_model is ExtractionResult
        return ExtractionResult(
            matches=[
                EntityMatch(
                    quote="graph memory idea",
                    normalized_content="graph memory",
                    match_type=MatchType.EXPLICIT,
                )
            ]
        )

    validated = asyncio.run(
        SemanticExtractor(fake_call).extract(
            "A graph memory idea.", idea_definition(), "source-3", workspace_id="w"
        )
    )

    assert validated.occurrences[0].quote == "graph memory idea"
