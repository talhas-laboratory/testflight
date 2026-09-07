"""Bounded HTTP client for the shared provider-neutral operator runtime."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Mapping
from http.client import HTTPResponse
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OperatorRuntimeClient(Protocol):
    async def execute(self, payload: Mapping[str, Any]) -> Mapping[str, Any]: ...


class HttpOperatorRuntimeClient:
    def __init__(
        self,
        endpoint: str,
        *,
        timeout_seconds: float = 120,
        open_url: Callable[..., HTTPResponse] | None = None,
    ) -> None:
        if not endpoint.strip():
            raise ValueError("operator runtime endpoint is required")
        if timeout_seconds <= 0:
            raise ValueError("operator runtime timeout must be positive")
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self._open_url = open_url or urlopen

    async def execute(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return await asyncio.to_thread(self._execute_sync, payload)

    def _execute_sync(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        request = Request(
            self.endpoint,
            data=body,
            headers={"accept": "application/json", "content-type": "application/json"},
            method="POST",
        )
        try:
            with self._open_url(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
        except HTTPError as error:
            raise RuntimeError(f"operator runtime returned HTTP {error.code}") from error
        except (OSError, URLError, TimeoutError) as error:
            raise RuntimeError(f"operator runtime request failed: {error}") from error
        try:
            result = json.loads(raw.decode())
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RuntimeError("operator runtime returned invalid JSON") from error
        if not isinstance(result, Mapping):
            raise RuntimeError("operator runtime response must be an object")
        return result


__all__ = ["HttpOperatorRuntimeClient", "OperatorRuntimeClient"]
