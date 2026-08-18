import asyncio
from datetime import UTC, datetime

from testflight_adapter_cognee import (
    CogneeAdapter,
    DefinitionExample,
    EntityDefinition,
    EntityMatch,
    ExtractionResult,
    MatchType,
    RelationshipDefinition,
    RelationshipMatch,
    SemanticExtractor,
    compile_extraction_prompt,
    relationship_custom_edges,
    validate_extraction,
)
from testflight_adapter_cognee.brand_projection import brand_assertion_custom_edges
from testflight_brand import BrandAssertion
from testflight_core import Capability, HealthState
from testflight_semantic import EpistemicStatus, Perspective


def test_descriptor_and_dependency_free_probe() -> None:
    adapter = CogneeAdapter()

    assert adapter.descriptor.capabilities == {Capability.MEMORY}
    assert adapter.health().state in {HealthState.AVAILABLE, HealthState.UNAVAILABLE}


def idea_definition() -> EntityDefinition:
    return EntityDefinition(
        name="Idea",
        definition="A distinct proposal, hypothesis, or design direction stated in the source.",
        include_rules=("Include proposals that could be evaluated or acted on.",),
        exclude_rules=("Exclude generic praise and isolated facts with no proposal.",),
        examples=(
            DefinitionExample("Use a graph as the durable memory layer.", True),
            DefinitionExample("This is interesting.", False),
        ),
        relationships=(
            RelationshipDefinition(
                name="supports",
                source_entity="Idea",
                target_entity="Idea",
                definition="The source idea provides rationale or evidence for the target idea.",
            ),
        ),
    )


def test_prompt_contains_definition_and_relationship_contract() -> None:
    prompt = compile_extraction_prompt(idea_definition())

    assert "ENTITY TYPE: Idea" in prompt
    assert "Exclude generic praise" in prompt
    assert "supports (Idea -> Idea)" in prompt
    assert "Do not return character offsets" in prompt


def test_validation_adds_offsets_and_stable_ids_and_rejects_bad_quotes() -> None:
    text = "Use a graph as memory. Use a graph as memory."
    result = ExtractionResult(
        matches=[
            EntityMatch(
                quote="Use a graph as memory.",
                normalized_content="graph memory",
                match_type=MatchType.EXPLICIT,
            ),
            EntityMatch(
                quote="not in source",
                normalized_content="hallucination",
                match_type=MatchType.EXPLICIT,
            ),
        ]
    )

    validated = validate_extraction(text, idea_definition(), result, "note-1")

    assert len(validated.occurrences) == 1
    assert validated.occurrences[0].start == 0
    assert validated.occurrences[0].end == len("Use a graph as memory.")
    assert (
        validated.occurrences[0].occurrence_id
        == validate_extraction(text, idea_definition(), result, "note-1")
        .occurrences[0]
        .occurrence_id
    )
    assert validated.rejections[0].kind == "entity"


def test_relationship_requires_defined_type_and_exact_evidence() -> None:
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

    validated = validate_extraction(text, idea_definition(), result, "note-2")

    assert len(validated.relationships) == 1
    assert validated.relationships[0].start == text.index("supports")
    edges = relationship_custom_edges(validated)
    assert edges[0][2] == "supports"
    assert edges[0][3]["evidence_quote"] == "supports"


def test_extractor_accepts_injected_structured_output() -> None:
    async def fake_call(
        text: str, prompt: str, response_model: type[ExtractionResult]
    ) -> ExtractionResult:
        assert text == "A graph memory idea."
        assert "ENTITY TYPE: Idea" in prompt
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
        SemanticExtractor(fake_call).extract("A graph memory idea.", idea_definition(), "note-3")
    )

    assert validated.occurrences[0].quote == "graph memory idea"


def test_brand_projection_keeps_accepted_assertions_as_direct_edges() -> None:
    common = {
        "workspace_id": "workspace-1",
        "brand_id": "brand-1",
        "subject_id": "brand-1",
        "predicate": "has_component",
        "object_id": "component-1",
        "relationship_definition_id": "has_component",
        "perspective": Perspective.INTENDED,
        "epistemic_status": EpistemicStatus.NORMATIVE,
        "recorded_at": datetime.now(UTC),
    }
    accepted = BrandAssertion(assertion_id="assertion-1", status="accepted", **common)
    held = BrandAssertion(assertion_id="assertion-2", status="held", **common)

    edges = brand_assertion_custom_edges([accepted, held])

    assert len(edges) == 1
    assert edges[0][:3] == ("brand-1", "component-1", "has_component")
    assert edges[0][3]["assertion_id"] == "assertion-1"
