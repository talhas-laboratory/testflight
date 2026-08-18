"""Provider-neutral structured extractor with deterministic validation."""

from collections.abc import Awaitable, Callable
from typing import Any

from .definitions import EntityDefinition
from .models import ExtractionResult
from .prompt import compile_extraction_prompt
from .validation import ValidationResult, validate_extraction

StructuredOutputCall = Callable[[str, str, type[ExtractionResult]], Awaitable[Any]]


class SemanticExtractor:
    """Run structured extraction without binding the semantic layer to a provider."""

    def __init__(self, llm_call: StructuredOutputCall) -> None:
        self._llm_call = llm_call

    async def extract(
        self,
        text: str,
        definition: EntityDefinition,
        source_id: str,
        *,
        workspace_id: str = "",
    ) -> ValidationResult:
        if not text:
            raise ValueError("text must not be empty")
        definition.validate()
        prompt = compile_extraction_prompt(definition)
        raw_result = await self._llm_call(text, prompt, ExtractionResult)
        result = (
            raw_result
            if isinstance(raw_result, ExtractionResult)
            else ExtractionResult.model_validate(raw_result)
        )
        return validate_extraction(text, definition, result, source_id, workspace_id=workspace_id)


__all__ = ["SemanticExtractor", "StructuredOutputCall"]
