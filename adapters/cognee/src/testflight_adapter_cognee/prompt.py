"""Deterministic prompt compilation for semantic extraction."""

from .definitions import EntityDefinition


def _bullet_lines(values: tuple[str, ...], empty: str = "(none)") -> str:
    return "\n".join(f"- {value}" for value in values) if values else empty


def compile_extraction_prompt(definition: EntityDefinition) -> str:
    """Compile semantic rules into a provider-neutral system prompt."""

    definition.validate()
    examples = []
    for example in definition.examples:
        status = "qualifies" if example.qualifies else "does not qualify"
        rationale = f" Rationale: {example.rationale}" if example.rationale else ""
        examples.append(f"- {status}: {example.text!r}.{rationale}")

    relationships = []
    for relationship in definition.relationships:
        examples_text = (
            f" Examples: {', '.join(relationship.examples)}." if relationship.examples else ""
        )
        relationships.append(
            "- "
            f"{relationship.name} ({relationship.source_entity} -> {relationship.target_entity}): "
            f"{relationship.definition}.{examples_text}"
        )

    return "\n".join(
        (
            "You are a conservative semantic extraction component.",
            "Extract only the configured entity type and the configured relationships.",
            "Every quote must be copied verbatim and contiguously from the source text.",
            "Do not return character offsets; the validator computes offsets from quotes.",
            "Do not invent entities, aliases, relationships, or facts.",
            "",
            f"ENTITY TYPE: {definition.name}",
            f"DEFINITION: {definition.definition}",
            "INCLUDE RULES:",
            _bullet_lines(definition.include_rules),
            "EXCLUDE RULES:",
            _bullet_lines(definition.exclude_rules),
            f"BOUNDARY RULE: {definition.boundary_rule}",
            f"INFERENCE RULE: {definition.inference_rule}",
            "EXAMPLES:",
            "\n".join(examples) if examples else "(none)",
            "RELATIONSHIP DEFINITIONS:",
            "\n".join(relationships) if relationships else "(none)",
            "",
            "Return JSON matching the supplied ExtractionResult schema.",
            "Use match_type=explicit for a direct mention and strongly_implied only when the "
            "definition explicitly permits it.",
            "A relationship is valid only when both endpoint quotes are entity quotes and "
            "evidence_quote appears verbatim in the source.",
        )
    )


__all__ = ["compile_extraction_prompt"]
