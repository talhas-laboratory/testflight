import asyncio
from datetime import UTC, datetime
from pathlib import Path

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
from testflight_adapter_cognee.context_retrieval_bridge import (
    exact_creative_field_items,
    exact_entity_items,
    exact_visual_language_items,
    normalize_items,
)
from testflight_adapter_cognee.world_view_bridge import resolve_world_view
from testflight_brand import BrandAssertion
from testflight_core import Capability, HealthState
from testflight_semantic import EpistemicStatus, Perspective


def test_context_retrieval_bridge_preserves_scope_and_source() -> None:
    items = normalize_items(
        [
            {
                "text": "WORKSPACE_ID: workspace-a\nBRAND_ID: brand-a\nSOURCE_URL: repo://evidence.md\nSOURCE_BEGIN\nEvidence\nSOURCE_END",
                "metadata": {"task_view": "asset-context", "doc_type": "evidence"},
            }
        ]
    )
    assert items[0]["workspaceId"] == "workspace-a"
    assert items[0]["brandId"] == "brand-a"
    assert items[0]["sourceUrl"] == "repo://evidence.md"
    assert items[0]["taskView"] == "asset-context"


def test_context_retrieval_bridge_preserves_branch_and_perspective_metadata() -> None:
    items = normalize_items(
        [
            {
                "text": "Evidence",
                "metadata": {
                    "source_url": "repo://evidence.md",
                    "branch_id": "branch:confidence",
                    "perspective_ids": ["perspective:customer"],
                },
            }
        ]
    )

    assert items[0]["branchId"] == "branch:confidence"
    assert items[0]["perspectiveIds"] == ["perspective:customer"]


def test_context_retrieval_bridge_normalizes_one_perspective_id_to_an_array() -> None:
    items = normalize_items(
        [
            {
                "text": "Evidence",
                "metadata": {
                    "source_url": "repo://evidence.md",
                    "perspective_ids": "perspective:customer",
                },
            }
        ]
    )

    assert items[0]["perspectiveIds"] == ["perspective:customer"]


def test_world_view_bridge_returns_only_selected_canonical_records() -> None:
    root = Path(__file__).resolve().parents[3]
    result = resolve_world_view(
        {
            "workspaceId": "world://workspace/brand/nike-research",
            "contextId": "CTX-NIKE-DIGITAL-MEMBERSHIP-CURRENT",
            "branchId": "BR-NIKE-MEMBER-DISCOVERY-LENS-001",
            "taskType": "brief",
            "perspectiveIds": ["PERS-NIKE-MEMBER-PROSPECTIVE-001"],
            "permittedRecordIds": [],
        },
        root / "workspaces/brand-nike-research/artifacts/world-modeling.yaml",
    )

    assert result["status"] == "hit"
    assert result["records"]["states"][0]["stateId"] == "STATE-NIKE-MEMBERSHIP-SERVICE-001"
    assert (
        result["records"]["perspectives"][0]["perspectiveId"] == "PERS-NIKE-MEMBER-PROSPECTIVE-001"
    )
    assert (
        result["records"]["relationshipFrames"][0]["frameId"]
        == "FRAME-NIKE-MEMBER-APP-DISCOVERY-001"
    )
    assert result["records"]["evidenceLinks"][0]["linkId"] == "EVIDLINK-NIKE-MEMBER-001"
    assert (
        result["records"]["hypotheses"][0]["hypothesisId"] == "HYP-NIKE-MEMBER-BENEFIT-CLARITY-001"
    )
    assert (
        result["records"]["experiments"][0]["experimentId"] == "EXP-NIKE-MEMBER-BENEFIT-CLARITY-001"
    )


def test_world_view_bridge_selects_a_context_from_declared_request_scope() -> None:
    root = Path(__file__).resolve().parents[3]
    result = resolve_world_view(
        {
            "workspaceId": "world://workspace/brand/nike-research",
            "taskType": "brief",
            "audience": "prospective members",
            "channel": "Nike App",
            "validTime": "2026-08-25",
            "perspectiveIds": [],
            "permittedRecordIds": [],
        },
        root / "workspaces/brand-nike-research/artifacts/world-modeling.yaml",
    )

    assert result["status"] == "hit"
    assert result["contextId"] == "CTX-NIKE-DIGITAL-MEMBERSHIP-CURRENT"
    assert result["branchId"] == "research-main"
    assert result["records"]["states"][0]["stateId"] == "STATE-NIKE-MEMBERSHIP-SERVICE-001"
    assert result["records"]["perspectives"] == []


def test_context_retrieval_bridge_returns_exact_entities_not_mentions() -> None:
    text = """WORKSPACE_ID: world://workspace/brand/example
BRAND_ID: world://brand/example
SOURCE_URL: repo://entity-inventory.yaml
DOC_TYPE: entity_inventory
TASK_VIEW: entity
PROMOTION_STATUS: proposal_only
SOURCE_BEGIN
version: 1
entities:
  - {id: ENT-EXAMPLE-001, entity_type: identity, label: Exact entity}
  - {id: ENT-EXAMPLE-002, entity_type: identity, label: Mere neighbor}
SOURCE_END
"""
    items = exact_entity_items(
        [{"id": "chunk", "text": text, "sourceUrl": "repo://entity-inventory.yaml"}],
        ["ENT-EXAMPLE-001"],
    )
    assert len(items) == 1
    assert items[0]["entityIds"] == ["ENT-EXAMPLE-001"]
    assert "ENT-EXAMPLE-002" not in items[0]["text"]
    assert items[0]["retrievalKind"] == "exact_entity"
    assert items[0]["taskView"] == "entity"


def test_context_retrieval_bridge_returns_exact_visual_reference_not_neighbor() -> None:
    text = """WORKSPACE_ID: world://workspace/brand/example
BRAND_ID: world://brand/example
SOURCE_URL: repo://visual-language/manifest.json
DOC_TYPE: visual_language_manifest
TASK_VIEW: visual-language
PROMOTION_STATUS: proposal_only
SOURCE_BEGIN
{"version":1,"workspaceId":"world://workspace/brand/example","brandId":"world://brand/example","profiles":[],"revisions":[],"references":[
  {"id":"VR-1","kind":"color.palette","label":"Exact palette"},
  {"id":"VR-2","kind":"typography.role","label":"Neighbor type"}
],"bindings":[]}
SOURCE_END
"""
    items = exact_visual_language_items(
        [{"id": "chunk", "text": text, "sourceUrl": "repo://visual-language/manifest.json"}],
        [],
        [],
        ["VR-1"],
    )
    assert len(items) == 1
    assert items[0]["referenceId"] == "VR-1"
    assert "VR-2" not in items[0]["text"]
    assert items[0]["retrievalKind"] == "visual_reference"


def test_context_retrieval_bridge_returns_exact_creative_field_record_in_project_scope() -> None:
    items = normalize_items(
        [
            {
                "text": (
                    "WORKSPACE_ID: child/creative-field\n"
                    "PROJECT_ID: project:one\n"
                    "RECORD_ID: field:one@1\n"
                    "RECORD_TYPE: CreativeFieldVersion\n"
                    "SOURCE_URL: creative://project:one/CreativeFieldVersion/field:one@1\n"
                    "SOURCE_BEGIN\nfield\nSOURCE_END"
                )
            },
            {
                "text": (
                    "WORKSPACE_ID: child/creative-field\n"
                    "PROJECT_ID: project:one\n"
                    "RECORD_ID: field:one@10\n"
                    "RECORD_TYPE: CreativeFieldVersion\n"
                    "SOURCE_URL: creative://project:one/CreativeFieldVersion/field:one@10\n"
                    "SOURCE_BEGIN\nneighbor\nSOURCE_END"
                )
            },
        ]
    )
    exact = exact_creative_field_items(items, ["field:one@1"], project_id="project:one")
    assert len(exact) == 1
    assert exact[0]["recordId"] == "field:one@1"
    assert exact[0]["retrievalKind"] == "exact_creative_field"


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
    assert edges[0][0] != "brand-1"
    assert edges[0][1] != "component-1"
    assert edges[0][2] == "has_component"
    assert edges[0][3]["assertion_id"] == "assertion-1"
