import json

from testflight_creative_studio import HttpOperatorExecutor


class FakeResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback) -> None:
        return None

    def read(self) -> bytes:
        return self.body


def test_http_executor_translates_domain_request_and_preserves_runtime_receipt() -> None:
    captured: dict[str, object] = {}

    def open_url(request, timeout):
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["content_type"] = request.headers["Content-type"]
        return FakeResponse(
            json.dumps(
                {
                    "status": "proposal",
                    "output": {"observed_features": []},
                    "errors": [],
                    "receipt": {
                        "operation_key": "observe:asset:one:run:one",
                        "provider_id": "fake",
                        "disclosure_refs": ["license:one", "source:one"],
                    },
                }
            ).encode()
        )

    executor = HttpOperatorExecutor(
        endpoint="http://127.0.0.1:8781/execute",
        workspace_id="world://workspace/client-a",
        timeout_seconds=7.5,
        open_url=open_url,
    )
    result = executor.execute(
        {
            "operator_id": "world://operator/creative/observation-extraction",
            "operator_version": 1,
            "operation_key": "observe:asset:one:run:one",
            "modality": "image/jpeg",
            "project_id": "project:client-a",
            "input": {
                "asset": {"asset_id": "asset:one"},
                "media_parts": [{"type": "image", "data_url": "data:image/jpeg;base64,ZmFrZQ=="}],
            },
            "disclosure_refs": ["license:one", "source:one"],
            "configuration": {"depth": "working"},
        }
    )

    assert result.status == "proposal"
    assert result.output == {"observed_features": []}
    assert result.receipt["provider_id"] == "fake"
    assert captured["timeout"] == 7.5
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["context"] == {
        "workspaceId": "world://workspace/client-a",
        "projectId": "project:client-a",
        "disclosureRefs": ["license:one", "source:one"],
    }
    assert body["input"]["media_parts"][0]["type"] == "image"
    assert captured["content_type"] == "application/json"


def test_http_executor_holds_invalid_requests_without_network_access() -> None:
    called = False

    def open_url(_request, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("network must not be called")

    executor = HttpOperatorExecutor(
        endpoint="http://127.0.0.1:8781/execute",
        workspace_id="world://workspace/client-a",
        open_url=open_url,
    )
    result = executor.execute(
        {
            "operator_id": "world://operator/creative/observation-extraction",
            "operator_version": 1,
            "operation_key": "observe:invalid",
            "modality": "image/jpeg",
            "project_id": "project:client-a",
            "input": {},
            "disclosure_refs": [],
        }
    )

    assert result.status == "failed"
    assert result.errors == ("operator request requires disclosure_refs",)
    assert called is False
