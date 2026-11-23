"""FastAPI endpoint tests with the RAG pipeline dependency mocked."""

from unittest.mock import Mock
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from university_knowledge_assistant import __version__
from university_knowledge_assistant.api.dependencies import get_rag_pipeline
from university_knowledge_assistant.api.main import app
from university_knowledge_assistant.api.schemas import AskRequest
from university_knowledge_assistant.services import LLMHTTPError


@pytest.fixture
def fake_pipeline():
    return SimpleNamespace(answer=Mock())


@pytest.fixture
def client(fake_pipeline):
    app.dependency_overrides[get_rag_pipeline] = lambda: fake_pipeline
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _success_payload() -> dict[str, object]:
    return {
        "question": "What is backprop?",
        "answer": "It adjusts weights using gradients.",
        "sources": [
            {
                "filename": "machine-learning.pdf",
                "page_number": 3,
                "document_id": "ml-course",
                "chunk_id": "chunk-1",
            }
        ],
    }


def test_health_reports_liveness_without_checking_llm(client, fake_pipeline) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": __version__,
        "llm_status": "not_checked",
    }
    fake_pipeline.answer.assert_not_called()


def test_ask_returns_grounded_answer_and_sources(client, fake_pipeline) -> None:
    payload = _success_payload()
    fake_pipeline.answer.return_value = payload

    response = client.post("/ask", json={"question": "What is backprop?"})

    assert response.status_code == 200
    assert response.json() == payload
    fake_pipeline.answer.assert_called_once_with("What is backprop?", top_k=None)


def test_ask_passes_explicit_top_k(client, fake_pipeline) -> None:
    fake_pipeline.answer.return_value = _success_payload()

    response = client.post("/ask", json={"question": "What is backprop?", "top_k": 5})

    assert response.status_code == 200
    fake_pipeline.answer.assert_called_once_with("What is backprop?", top_k=5)


@pytest.mark.parametrize(
    "body",
    [
        {"question": ""},
        {},
        {"question": "What is backprop?", "top_k": 0},
        {"question": "What is backprop?", "top_k": 11},
        {"question": "What is backprop?", "top_k": "many"},
        {"question": "What is backprop?", "unexpected": True},
        {"question": "x" * 2001},
    ],
)
def test_invalid_ask_requests_return_422(client, fake_pipeline, body) -> None:
    response = client.post("/ask", json=body)

    assert response.status_code == 422
    fake_pipeline.answer.assert_not_called()


def test_whitespace_question_returns_400(client, fake_pipeline) -> None:
    fake_pipeline.answer.side_effect = ValueError("question must be a non-empty string")

    response = client.post("/ask", json={"question": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "question must be a non-empty string"


def test_llm_failure_returns_502(client, fake_pipeline) -> None:
    fake_pipeline.answer.side_effect = LLMHTTPError("LM Studio returned HTTP 500")

    response = client.post("/ask", json={"question": "What is backprop?"})

    assert response.status_code == 502
    assert "Local language model request failed" in response.json()["detail"]
    assert "500" in response.json()["detail"]


def test_openapi_docs_are_available(client) -> None:
    response = client.get("/docs")

    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()


def test_ask_request_top_k_is_optional() -> None:
    request = AskRequest(question="What is backprop?")

    assert request.top_k is None
