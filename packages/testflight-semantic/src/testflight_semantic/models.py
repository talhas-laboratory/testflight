"""Structured extraction models shared by inference providers."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MatchType(StrEnum):
    EXPLICIT = "explicit"
    STRONGLY_IMPLIED = "strongly_implied"


class EntityMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quote: str = Field(min_length=1)
    normalized_content: str = Field(min_length=1)
    match_type: MatchType
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("quote", "normalized_content")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value


class RelationshipMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationship_type: str = Field(min_length=1)
    source_quote: str = Field(min_length=1)
    target_quote: str = Field(min_length=1)
    evidence_quote: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("relationship_type", "source_quote", "target_quote", "evidence_quote")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value


class ExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matches: list[EntityMatch] = Field(default_factory=list)
    relationships: list[RelationshipMatch] = Field(default_factory=list)


__all__ = ["EntityMatch", "ExtractionResult", "MatchType", "RelationshipMatch"]
