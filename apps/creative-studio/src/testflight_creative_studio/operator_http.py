"""HTTP adapter from the Python Creative Field executor seam to the TS runtime."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from http.client import HTTPResponse
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from testflight_creative_field import OperatorExecution


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list | tuple):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def _required_string(request: Mapping[str, Any], name: str) -> str:
    value = request.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"operator request requires {name}")
    return value


class HttpOperatorExecutor:
    """Call a local runtime HTTP endpoint using the domain ``OperatorExecutor`` contract.

    The adapter owns only transport translation. It does not import a provider SDK, inspect model
    output, or turn a non-success runtime status into a semantic fallback.
    """

    def __init__(
        self,
        *,
        endpoint: str,
        workspace_id: str,
        timeout_seconds: float = 120.0,
        open_url: Callable[..., HTTPResponse] | None = None,
    ) -> None:
        if not endpoint.strip():
            raise ValueError("operator runtime endpoint is required")
        if not workspace_id.strip():
            raise ValueError("operator runtime workspace_id is required")
        if timeout_seconds <= 0:
            raise ValueError("operator runtime timeout must be positive")
        self.endpoint = endpoint
        self.workspace_id = workspace_id
        self.timeout_seconds = timeout_seconds
        self._open_url = open_url or urlopen

    def execute(self, request: Mapping[str, Any]) -> OperatorExecution:
        try:
            payload = self._payload(request)
        except (TypeError, ValueError) as error:
            return OperatorExecution(
                status="failed",
                errors=(str(error),),
                receipt={"transport": "http", "preflight": "invalid_request"},
            )
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        http_request = Request(
            self.endpoint,
            data=body,
            headers={
                "accept": "application/json",
                "content-type": "application/json",
            },
            method="POST",
        )
        try:
            with self._open_url(http_request, timeout=self.timeout_seconds) as response:
                raw = response.read()
        except HTTPError as error:
            return OperatorExecution(
                status="failed",
                errors=(f"operator runtime returned HTTP {error.code}",),
                receipt={
                    "transport": "http",
                    "status_code": error.code,
                    "endpoint": self.endpoint,
                },
            )
        except (OSError, URLError, TimeoutError) as error:
            return OperatorExecution(
                status="failed",
                errors=(f"operator runtime request failed: {error}",),
                receipt={"transport": "http", "endpoint": self.endpoint},
            )
        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            return OperatorExecution(
                status="failed",
                errors=(f"operator runtime returned invalid JSON: {error}",),
                receipt={"transport": "http", "endpoint": self.endpoint},
            )
        if not isinstance(result, Mapping):
            return OperatorExecution(
                status="failed",
                errors=("operator runtime response must be an object",),
                receipt={"transport": "http", "endpoint": self.endpoint},
            )
        status = result.get("status")
        if not isinstance(status, str) or not status.strip():
            return OperatorExecution(
                status="failed",
                errors=("operator runtime response has no status",),
                receipt={"transport": "http", "endpoint": self.endpoint},
            )
        receipt = result.get("receipt")
        return OperatorExecution(
            status=status,
            output=result.get("output"),
            errors=_strings(result.get("errors")),
            hold_reason=(
                result["hold_reason"] if isinstance(result.get("hold_reason"), str) else None
            ),
            receipt=(
                dict(receipt)
                if isinstance(receipt, Mapping)
                else {"transport": "http", "endpoint": self.endpoint}
            ),
        )

    def _payload(self, request: Mapping[str, Any]) -> dict[str, Any]:
        project_id = _required_string(request, "project_id")
        operator_id = _required_string(request, "operator_id")
        operation_key = _required_string(request, "operation_key")
        modality = _required_string(request, "modality")
        operator_version = request.get("operator_version")
        if not isinstance(operator_version, int) or operator_version < 1:
            raise ValueError("operator request requires a positive integer operator_version")
        disclosure_refs = _strings(request.get("disclosure_refs"))
        if not disclosure_refs:
            raise ValueError("operator request requires disclosure_refs")
        context_payload = request.get("context")
        context = dict(context_payload) if isinstance(context_payload, Mapping) else {}
        context.update(
            {
                "workspaceId": self.workspace_id,
                "projectId": project_id,
                "disclosureRefs": list(disclosure_refs),
            }
        )
        configuration = request.get("configuration", {})
        if not isinstance(configuration, Mapping):
            raise ValueError("operator request configuration must be an object")
        payload: dict[str, Any] = {
            "operator_id": operator_id,
            "operator_version": operator_version,
            "operation_key": operation_key,
            "modality": modality,
            "input": request.get("input"),
            "context": context,
            "configuration": dict(configuration),
        }
        requested_status = request.get("requested_status")
        if requested_status is not None:
            payload["requested_status"] = requested_status
        return payload


__all__ = ["HttpOperatorExecutor"]
