"""Provider-neutral semantic extractor with a lazy Cognee LLM bridge."""

from collections.abc import Awaitable, Callable
from typing import Any

from .definitions import EntityDefinition
from .models import ExtractionResult
from .prompt import compile_extraction_prompt
from .validation import ValidationResult, validate_extraction

StructuredOutputCall = Callable[[str, str, type[ExtractionResult]], Awaitable[Any]]


class SemanticExtractor:
    """Run structured extraction and apply deterministic provenance validation.

    ``llm_call`` is injectable for tests and future providers.  The default path
    imports Cognee only when extraction is actually requested.
    """

    def __init__(self, llm_call: StructuredOutputCall | None = None) -> None:
        self._llm_call = llm_call

    async def extract(
        self,
        text: str,
        definition: EntityDefinition,
        source_id: str,
    ) -> ValidationResult:
        if not text:
            raise ValueError("text must not be empty")

        definition.validate()
        prompt = compile_extraction_prompt(definition)
        llm_call = self._llm_call or self._default_llm_call
        raw_result = await llm_call(text, prompt, ExtractionResult)
        result = (
            raw_result
            if isinstance(raw_result, ExtractionResult)
            else ExtractionResult.model_validate(raw_result)
        )
        return validate_extraction(text, definition, result, source_id)

    @staticmethod
    async def _default_llm_call(
        text: str,
        system_prompt: str,
        response_model: type[ExtractionResult],
    ) -> ExtractionResult:
        try:
            from cognee.infrastructure.llm.LLMGateway import LLMGateway
        except ModuleNotFoundError as error:
            raise RuntimeError(
                "Cognee is required for the default semantic extractor; "
                "install the adapter's cognee extra"
            ) from error
        return await LLMGateway.acreate_structured_output(
            text,
            system_prompt,
            response_model,
        )


__all__ = ["SemanticExtractor", "StructuredOutputCall"]
