"""LLM service tests with a fake HTTP client (no LM Studio required)."""

import httpx
import pytest

import university_knowledge_assistant.services.llm_service as llm_module
from university_knowledge_assistant.config import Settings
from university_knowledge_assistant.services import (
    LLMService,
    LLMConnectionError,
    LLMHTTPError,
    LLMResponseError,
    LLMTimeoutError,
)


class FakeResponse:
    def __init__(
        self,
        data: object = None,
        status_code: int = 200,
        json_error: Exception | None = None,
    ) -> None:
        self.data = data
        self.status_code = status_code
        self.json_error = json_error

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("POST", "http://test/chat/completions")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("HTTP error", request=request, response=response)

    def json(self) -> object:
        if self.json_error:
            raise self.json_error
        return self.data


class FakeClient:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
        self.post_calls: list[tuple[str, dict[str, object]]] = []
        self.next_response: FakeResponse | None = None
        self.post_error: Exception | None = None
        self.closed = False

    def post(self, path: str, *, json: dict[str, object]) -> FakeResponse:
        if self.post_error:
            raise self.post_error
        self.post_calls.append((path, json))
        assert self.next_response is not None
        return self.next_response

    def close(self) -> None:
        self.closed = True


def _success_response(text: str = "A grounded answer.") -> FakeResponse:
    return FakeResponse({"choices": [{"message": {"content": text}}]})


def _make_service(
    monkeypatch,
    client: FakeClient,
    settings: Settings | None = None,
) -> LLMService:
    def client_factory(**kwargs: object) -> FakeClient:
        client.kwargs = kwargs
        return client

    monkeypatch.setattr(llm_module.httpx, "Client", client_factory)
    return LLMService(settings)


def test_generate_answer_builds_expected_request(monkeypatch) -> None:
    client = FakeClient()
    client.next_response = _success_response("  grounded answer  ")
    settings = Settings(llm_temperature=0.4, llm_max_tokens=321)
    service = _make_service(monkeypatch, client, settings)

    answer = service.generate_answer("system rules", "question + context")

    assert answer == "grounded answer"
    assert client.kwargs["base_url"] == "http://localhost:1234/v1"
    assert client.kwargs["headers"]["Authorization"] == "Bearer lm-studio"
    path, payload = client.post_calls[0]
    assert path == "/chat/completions"
    assert payload["model"] == "qwen3.5-9b"
    assert payload["messages"] == [
        {"role": "system", "content": "system rules"},
        {"role": "user", "content": "question + context"},
    ]
    assert payload["temperature"] == 0.4
    assert payload["max_tokens"] == 321
    assert payload["stream"] is False


def test_per_call_overrides_are_used(monkeypatch) -> None:
    client = FakeClient()
    client.next_response = _success_response()
    service = _make_service(monkeypatch, client)

    service.generate_answer("sys", "user", temperature=0.0, max_tokens=50)

    payload = client.post_calls[0][1]
    assert payload["temperature"] == 0.0
    assert payload["max_tokens"] == 50


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (httpx.TimeoutException("slow"), LLMTimeoutError),
        (httpx.ConnectError("down"), LLMConnectionError),
        (httpx.NetworkError("network"), LLMConnectionError),
    ],
)
def test_connection_and_timeout_errors_are_wrapped(
    monkeypatch, error: Exception, expected: type[Exception]
) -> None:
    client = FakeClient()
    client.post_error = error
    service = _make_service(monkeypatch, client)

    with pytest.raises(expected):
        service.generate_answer("sys", "user")


def test_http_error_is_reported(monkeypatch) -> None:
    client = FakeClient()
    client.next_response = FakeResponse(status_code=500)
    service = _make_service(monkeypatch, client)

    with pytest.raises(LLMHTTPError, match="500"):
        service.generate_answer("sys", "user")


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"choices": []},
        {"choices": [{"message": {}}]},
        {"choices": [{"message": {"content": "   "}}]},
        "not a JSON object",
    ],
)
def test_invalid_response_bodies_are_rejected(monkeypatch, data: object) -> None:
    client = FakeClient()
    client.next_response = FakeResponse(data=data)
    service = _make_service(monkeypatch, client)

    with pytest.raises(LLMResponseError):
        service.generate_answer("sys", "user")


def test_invalid_json_is_reported(monkeypatch) -> None:
    client = FakeClient()
    client.next_response = FakeResponse(json_error=ValueError("bad json"))
    service = _make_service(monkeypatch, client)

    with pytest.raises(LLMResponseError, match="invalid JSON"):
        service.generate_answer("sys", "user")


def test_reasoning_only_response_has_clear_error(monkeypatch) -> None:
    client = FakeClient()
    client.next_response = FakeResponse(
        {
            "choices": [
                {
                    "message": {
                        "content": "",
                        "reasoning_content": "internal reasoning",
                    }
                }
            ]
        }
    )
    service = _make_service(monkeypatch, client)

    with pytest.raises(LLMResponseError, match="increase LLM_MAX_TOKENS"):
        service.generate_answer("sys", "user")


def test_close_closes_owned_client(monkeypatch) -> None:
    client = FakeClient()
    service = _make_service(monkeypatch, client)

    service.close()

    assert client.closed is True
