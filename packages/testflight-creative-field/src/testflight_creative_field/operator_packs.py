"""Portable operator-contract and client-pack loading for Creative Field composition roots."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

CREATIVE_OPERATOR_IDS = (
    "world://operator/creative/observation-extraction",
    "world://operator/creative/reference-interpretation",
    "world://operator/creative/field-synthesis",
    "world://operator/creative/output-evaluation",
)

_OPERATOR_ALIASES = {
    "observation-extraction": "world://operator/creative/observation-extraction",
    "observe-reference": "world://operator/creative/observation-extraction",
    "reference-interpretation": "world://operator/creative/reference-interpretation",
    "interpret-reference-role": "world://operator/creative/reference-interpretation",
    "field-synthesis": "world://operator/creative/field-synthesis",
    "synthesize-creative-field": "world://operator/creative/field-synthesis",
    "output-evaluation": "world://operator/creative/output-evaluation",
    "evaluate-creative-output": "world://operator/creative/output-evaluation",
}


class OperatorPackEntry(BaseModel):
    """Client configuration over a general operator; references stay external and scoped."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    context_selectors: tuple[str, ...] = ()
    vocabulary_refs: tuple[str, ...] = ()
    priority_principle_refs: tuple[str, ...] = ()
    forbidden_association_refs: tuple[str, ...] = ()
    evaluator_rubric_ref: str | None = None


class OperatorPack(BaseModel):
    """A versioned client/operator binding without copying Brand-world facts into prompts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    pack_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    workspace_id: str = Field(min_length=1)
    operators: dict[str, OperatorPackEntry] = Field(default_factory=dict)


def load_operator_pack(path: Path, *, expected_workspace_id: str | None = None) -> OperatorPack:
    """Load and validate one client pack from YAML."""

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"operator pack must be a YAML object: {path}")
    if isinstance(payload.get("operator_pack"), dict):
        payload = payload["operator_pack"]
    pack = OperatorPack.model_validate(payload)
    if expected_workspace_id is not None and pack.workspace_id != expected_workspace_id:
        raise ValueError("operator pack workspace does not match the expected workspace")
    return pack


def operator_pack_configuration(pack: OperatorPack, operator_key: str) -> dict[str, Any]:
    """Return JSON-safe configuration for one operator invocation."""

    canonical_id = operator_key.rsplit("@", 1)[0]
    short_key = canonical_id.rsplit("/", 1)[-1]
    canonical_id = _OPERATOR_ALIASES.get(short_key, canonical_id)
    aliases = (
        operator_key,
        canonical_id,
        canonical_id.rsplit("/", 1)[-1],
        *_matching_aliases(canonical_id),
    )
    entry = next((pack.operators[key] for key in aliases if key in pack.operators), None)
    return {
        "operator_pack_id": pack.pack_id,
        "operator_pack_version": pack.version,
        "operator_pack_workspace_id": pack.workspace_id,
        "operator_key": operator_key,
        "operator_id": canonical_id,
        "client_operator_config": entry.model_dump(mode="json") if entry is not None else {},
    }


def _matching_aliases(canonical_id: str) -> tuple[str, ...]:
    return tuple(alias for alias, target in _OPERATOR_ALIASES.items() if target == canonical_id)


def load_operator_contracts(
    operator_ids: tuple[str, ...] | list[str], *, index_path: Path
) -> dict[str, dict[str, Any]]:
    """Load a bounded set of canonical YAML contracts keyed by stable operator ID."""

    return {
        operator_id: load_operator_contract(operator_id, index_path=index_path)
        for operator_id in operator_ids
    }


def load_operator_contract(operator_id: str, *, index_path: Path) -> dict[str, Any]:
    """Load one portable reasoning contract selected by ``reasoning/operators/index.yaml``."""

    if not operator_id.strip():
        raise ValueError("operator_id is required")
    index = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    if not isinstance(index, dict) or not isinstance(index.get("operators"), list):
        raise ValueError(f"operator catalog must contain an operators list: {index_path}")
    lookup_id = operator_id.rsplit("@", 1)[0]
    entry = next(
        (
            item
            for item in index["operators"]
            if isinstance(item, dict) and str(item.get("id", "")).rsplit("@", 1)[0] == lookup_id
        ),
        None,
    )
    if entry is None or not isinstance(entry.get("file"), str):
        raise ValueError(f"operator is not registered in the catalog: {operator_id}")
    contract_path = index_path.parent / entry["file"]
    payload = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("operator"), dict):
        raise ValueError(f"operator contract must contain an operator object: {contract_path}")
    contract = payload["operator"]
    contract_id = str(contract.get("id", "")).rsplit("@", 1)[0]
    if contract_id != lookup_id:
        raise ValueError(f"operator contract identity mismatch: {contract_path}")
    if not isinstance(contract.get("version"), int) or contract["version"] < 1:
        raise ValueError(f"operator contract version is invalid: {contract_path}")
    for required in ("purpose", "procedure", "invariants", "hold_when", "evaluators"):
        if not contract.get(required):
            raise ValueError(f"operator contract missing {required}: {contract_path}")
    return contract


__all__ = [
    "CREATIVE_OPERATOR_IDS",
    "OperatorPack",
    "OperatorPackEntry",
    "load_operator_contract",
    "load_operator_contracts",
    "load_operator_pack",
    "operator_pack_configuration",
]
