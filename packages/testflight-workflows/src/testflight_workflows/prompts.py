"""Strict rendering for versioned workflow prompt contracts."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .models import PromptContract

_PLACEHOLDER = re.compile(r"{{\s*(arguments|inputs)((?:\.[a-zA-Z0-9_-]+)+)\s*}}")


class PromptRenderError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RenderedPrompt:
    prompt_id: str
    prompt_version: int
    system: str
    user: str


def _read_path(value: Any, path: str) -> Any:
    current = value
    for part in path.removeprefix(".").split("."):
        if isinstance(current, Mapping) and part in current:
            current = current[part]
        elif isinstance(current, Sequence) and not isinstance(current, str | bytes):
            try:
                current = current[int(part)]
            except (ValueError, IndexError) as error:
                raise PromptRenderError(f"prompt path does not exist: {path}") from error
        else:
            raise PromptRenderError(f"prompt path does not exist: {path}")
    return current


def _render(template: str, roots: Mapping[str, Mapping[str, Any]]) -> str:
    def replace(match: re.Match[str]) -> str:
        value = _read_path(roots[match.group(1)], match.group(2))
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    rendered = _PLACEHOLDER.sub(replace, template)
    # A rendered JSON object can legitimately end in adjacent closing braces (``}}``). Only an
    # opening marker can denote an unresolved or malformed template expression at this point.
    if "{{" in rendered:
        raise PromptRenderError("prompt contains an unsupported or incomplete placeholder")
    return rendered


def render_prompt(
    contract: PromptContract,
    *,
    inputs: Mapping[str, Any],
    arguments: Mapping[str, Any],
) -> RenderedPrompt:
    roots = {"inputs": inputs, "arguments": arguments}
    return RenderedPrompt(
        prompt_id=contract.id,
        prompt_version=contract.version,
        system=_render(contract.system, roots),
        user=_render(contract.user, roots),
    )


__all__ = ["PromptRenderError", "RenderedPrompt", "render_prompt"]
