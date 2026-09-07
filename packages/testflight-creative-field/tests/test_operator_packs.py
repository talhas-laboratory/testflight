from pathlib import Path

import pytest
from testflight_creative_field import (
    CREATIVE_OPERATOR_IDS,
    load_operator_contract,
    load_operator_contracts,
    load_operator_pack,
    operator_pack_configuration,
)


def test_load_operator_contract_uses_catalog_identity_and_preserves_procedure() -> None:
    contract = load_operator_contract(
        "world://operator/creative/output-evaluation@1",
        index_path=Path("reasoning/operators/index.yaml"),
    )
    assert contract["id"] == "world://operator/creative/output-evaluation"
    assert contract["version"] == 1
    assert contract["invariants"]
    assert contract["hold_when"]


def test_client_pack_is_configuration_over_general_operator_contract(tmp_path: Path) -> None:
    path = tmp_path / "operator-pack.yaml"
    path.write_text(
        """
pack_id: operator-pack:example@1
version: 1
workspace_id: world://workspace/brand/example
operators:
  interpret-reference-role:
    context_selectors: [brand:identity]
    vocabulary_refs: [vocabulary:example]
    priority_principle_refs: [principle:quiet-confidence]
    forbidden_association_refs: [association:clinical-claim]
    evaluator_rubric_ref: rubric:example:creative-field@1
""",
        encoding="utf-8",
    )
    pack = load_operator_pack(
        path,
        expected_workspace_id="world://workspace/brand/example",
    )
    config = operator_pack_configuration(pack, "interpret-reference-role")
    assert config["operator_pack_id"] == "operator-pack:example@1"
    assert config["operator_id"] == "world://operator/creative/reference-interpretation"
    assert config["client_operator_config"]["vocabulary_refs"] == ["vocabulary:example"]
    canonical_config = operator_pack_configuration(
        pack, "world://operator/creative/reference-interpretation@1"
    )
    assert canonical_config["client_operator_config"] == config["client_operator_config"]
    with pytest.raises(ValueError, match="workspace"):
        load_operator_pack(path, expected_workspace_id="world://workspace/brand/other")


def test_load_operator_contracts_is_bounded_to_requested_operator_ids() -> None:
    contracts = load_operator_contracts(
        [CREATIVE_OPERATOR_IDS[0], CREATIVE_OPERATOR_IDS[-1]],
        index_path=Path("reasoning/operators/index.yaml"),
    )
    assert tuple(contracts) == (CREATIVE_OPERATOR_IDS[0], CREATIVE_OPERATOR_IDS[-1])
    assert contracts[CREATIVE_OPERATOR_IDS[0]]["procedure"]
    assert contracts[CREATIVE_OPERATOR_IDS[-1]]["evaluators"]
