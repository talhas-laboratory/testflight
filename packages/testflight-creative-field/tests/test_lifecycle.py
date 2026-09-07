from testflight_creative_field import (
    ArtifactStatus,
    CreativeFieldLifecycle,
    FieldDimension,
    OperatorExecution,
    ReferenceContribution,
    ReferenceInterpretation,
    ReviewAction,
    ReviewDecision,
)


class FakeExecutor:
    def __init__(self, output, status="proposal") -> None:
        self.output = output
        self.status = status

    def execute(self, request):
        return OperatorExecution(
            status=self.status, output=self.output, receipt={"run": request["operation_key"]}
        )


def _inputs():
    contribution = ReferenceContribution(
        contribution_id="contribution:softness",
        interpretation_id="interpretation:one",
        reference_asset_id="asset:one",
        dimension_id="material",
        role="tactility",
        transfer_instruction="preserve softness",
        anti_transfer_instruction="do not copy the object",
        evidence_refs=("region:1",),
        derivation_id="derivation:interpretation",
    )
    interpretation = ReferenceInterpretation(
        interpretation_id="interpretation:one",
        project_id="project:one",
        reference_asset_id="asset:one",
        observation_ids=("observation:one",),
        proposed_role="carry tactility",
        dimension_contributions=(contribution,),
        evidence_refs=("region:1",),
        authority="project-proposal",
        derivation_id="derivation:interpretation",
    )
    dimensions = (
        FieldDimension(dimension_id="material", label="Material", definition="tactility"),
    )
    return interpretation, contribution, dimensions


def _proposal_output():
    return {
        "source_contribution_ids": ["contribution:softness"],
        "principles": [
            {
                "principle_id": "principle:quiet",
                "statement": "Use precise form with soft tactility.",
                "dimension_ids": ["material"],
                "source_contribution_ids": ["contribution:softness"],
            }
        ],
        "tensions": [
            {
                "tension_id": "tension:precise-soft",
                "statement": "Precision should hold softness, not erase it.",
                "poles": ["precise", "soft"],
                "source_contribution_ids": ["contribution:softness"],
            }
        ],
        "exclusions": [
            {
                "exclusion_id": "exclusion:literal",
                "statement": "Do not reproduce the reference object.",
                "category": "literal-copy",
                "source_contribution_ids": ["contribution:softness"],
            }
        ],
        "dimension_states": [
            {
                "dimension_id": "material",
                "summary": "soft but controlled",
                "source_contribution_ids": ["contribution:softness"],
            }
        ],
    }


def test_synthesis_preserves_tension_outlier_lineage_and_produces_deterministic_diff() -> None:
    interpretation, contribution, dimensions = _inputs()
    lifecycle = CreativeFieldLifecycle()
    result = lifecycle.synthesize(
        project_id="project:one",
        field_id="field:one",
        interpretations=(interpretation,),
        contributions=(contribution,),
        dimensions=dimensions,
        project_purpose="quiet launch",
        derivation_id="derivation:synthesis:one",
        executor=FakeExecutor(_proposal_output()),
    )
    assert result.status is ArtifactStatus.SUCCESS
    assert result.proposal is not None
    assert result.proposal.tensions[0].poles == ("precise", "soft")
    assert result.proposal.tensions[0].source_contribution_ids == ("contribution:softness",)
    assert result.proposal.semantic_diff["added"] == (
        "principles",
        "tensions",
        "exclusions",
        "dimensions",
    )


def test_review_requires_authority_and_acceptance_creates_an_immutable_successor() -> None:
    interpretation, contribution, dimensions = _inputs()
    lifecycle = CreativeFieldLifecycle()
    proposal = lifecycle.synthesize(
        project_id="project:one",
        field_id="field:one",
        interpretations=(interpretation,),
        contributions=(contribution,),
        dimensions=dimensions,
        project_purpose="quiet launch",
        derivation_id="derivation:synthesis:one",
        executor=FakeExecutor(_proposal_output()),
    ).proposal
    assert proposal is not None
    no_authority = lifecycle.review_and_version(
        proposal=proposal,
        decision=ReviewDecision(
            review_id="review:no-authority",
            target_id=proposal.proposal_id,
            action=ReviewAction.ACCEPT,
            actor_id="actor:one",
            rationale="approve",
            created_at="2026-09-03T00:00:00Z",
        ),
        version_id="field:one@1",
        reviewed_at="2026-09-03T00:00:00Z",
    )
    accepted = lifecycle.review_and_version(
        proposal=proposal,
        decision=ReviewDecision(
            review_id="review:accepted",
            target_id=proposal.proposal_id,
            action=ReviewAction.ACCEPT,
            actor_id="actor:one",
            rationale="approve",
            created_at="2026-09-03T00:00:00Z",
            authority_grant_id="grant:project-one",
        ),
        version_id="field:one@1",
        reviewed_at="2026-09-03T00:00:00Z",
    )
    assert no_authority.status is ArtifactStatus.HELD
    assert accepted.status is ArtifactStatus.SUCCESS
    assert accepted.version is not None
    assert accepted.version.version_id == "field:one@1"
    assert accepted.version.review_record_ids == ("review:accepted",)
    assert proposal.status.value == "proposed"


def test_correction_creates_new_version_and_only_affected_dependents_are_stale() -> None:
    interpretation, contribution, dimensions = _inputs()
    lifecycle = CreativeFieldLifecycle()
    proposal = lifecycle.synthesize(
        project_id="project:one",
        field_id="field:one",
        interpretations=(interpretation,),
        contributions=(contribution,),
        dimensions=dimensions,
        project_purpose="quiet launch",
        derivation_id="derivation:synthesis:one",
        executor=FakeExecutor(_proposal_output()),
    ).proposal
    assert proposal is not None
    first = lifecycle.review_and_version(
        proposal=proposal,
        decision=ReviewDecision(
            review_id="review:one",
            target_id=proposal.proposal_id,
            action=ReviewAction.ACCEPT,
            actor_id="actor:one",
            rationale="approve",
            created_at="2026-09-03T00:00:00Z",
            authority_grant_id="grant:one",
        ),
        version_id="field:one@1",
        reviewed_at="2026-09-03T00:00:00Z",
    ).version
    assert first is not None
    corrected = proposal.model_copy(
        update={
            "principles": (
                proposal.principles[0].model_copy(
                    update={"statement": "Use softness deliberately."}
                ),
            )
        }
    )
    second = lifecycle.review_and_version(
        proposal=proposal,
        replacement_proposal=corrected,
        decision=ReviewDecision(
            review_id="review:two",
            target_id=proposal.proposal_id,
            action=ReviewAction.MODIFY,
            actor_id="actor:one",
            rationale="correct principle",
            created_at="2026-09-03T00:00:00Z",
            authority_grant_id="grant:one",
        ),
        version_id="field:one@2",
        reviewed_at="2026-09-03T00:00:00Z",
        parent_version=first,
    ).version
    assert second is not None
    assert second.parent_version_ids == ("field:one@1",)
    assert first.principles[0].statement != second.principles[0].statement
    assert lifecycle.affected_dependents(
        (
            {"record_id": "projection:one", "dependency_ids": ["contribution:softness"]},
            {"record_id": "projection:two", "dependency_ids": ["contribution:other"]},
        ),
        ("contribution:softness",),
    ) == ("projection:one",)
