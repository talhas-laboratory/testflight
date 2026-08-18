"""Explicit relationship-weight policies without truth-score collapse."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RelationshipWeightDimensions:
    structural_weight: float | None = None
    evidence_confidence: float | None = None
    source_authority: float | None = None
    salience: float | None = None
    valence: float | None = None

    def validate(self) -> None:
        bounded = {
            "structural_weight": self.structural_weight,
            "evidence_confidence": self.evidence_confidence,
            "source_authority": self.source_authority,
            "salience": self.salience,
        }
        for name, value in bounded.items():
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.valence is not None and not -1.0 <= self.valence <= 1.0:
            raise ValueError("valence must be between -1 and 1")


@dataclass(frozen=True, slots=True)
class RelationshipWeightPolicy:
    """A versioned policy that may derive traversal strength, never truth."""

    policy_id: str = "world://brand/policy/relationship-weight/v1"
    aggregate_enabled: bool = False

    def derive_effective_strength(self, dimensions: RelationshipWeightDimensions) -> float | None:
        dimensions.validate()
        if not self.aggregate_enabled:
            return None
        values = [
            value
            for value in (
                dimensions.structural_weight,
                dimensions.evidence_confidence,
                dimensions.source_authority,
                dimensions.salience,
            )
            if value is not None
        ]
        if not values:
            return None
        return sum(values) / len(values)


__all__ = ["RelationshipWeightDimensions", "RelationshipWeightPolicy"]
