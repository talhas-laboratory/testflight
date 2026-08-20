"""Universal derivation records and lineage validation."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class DerivationResult(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PARTIAL = "partial"
    NO_HIT = "no_hit"
    HELD = "held"


class DerivationRecord(BaseModel):
    """Why a non-source record exists and which contracts produced it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    derivation_id: str = Field(min_length=1)
    output_ids: tuple[str, ...] = ()
    input_ids: tuple[str, ...] = ()
    operation_id: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    model_or_tool: str | None = None
    ontology_version: str = Field(min_length=1)
    policy_versions: tuple[str, ...] = ()
    reasoning_operators: tuple[str, ...] = ()
    occurred_at: str = Field(min_length=1)
    result: DerivationResult


def validate_derivation_graph(
    records: tuple[DerivationRecord, ...], *, source_ids: frozenset[str] = frozenset()
) -> None:
    """Reject duplicate outputs, missing inputs, and lineage cycles."""

    output_to_record: dict[str, str] = {}
    for record in records:
        for output_id in record.output_ids:
            if output_id in output_to_record:
                raise ValueError(f"multiple derivations produce output: {output_id}")
            output_to_record[output_id] = record.derivation_id

    adjacency: dict[str, tuple[str, ...]] = {}
    for record in records:
        for input_id in record.input_ids:
            if input_id not in output_to_record and input_id not in source_ids:
                raise ValueError(f"derivation input has no source or derivation: {input_id}")
        adjacency[record.derivation_id] = tuple(
            output_to_record[input_id]
            for input_id in record.input_ids
            if input_id in output_to_record
        )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(record_id: str) -> None:
        if record_id in visiting:
            raise ValueError(f"derivation cycle detected at: {record_id}")
        if record_id in visited:
            return
        visiting.add(record_id)
        for parent_id in adjacency.get(record_id, ()):
            visit(parent_id)
        visiting.remove(record_id)
        visited.add(record_id)

    for record_id in adjacency:
        visit(record_id)


__all__ = ["DerivationRecord", "DerivationResult", "validate_derivation_graph"]
