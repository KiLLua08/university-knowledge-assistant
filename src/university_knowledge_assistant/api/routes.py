"""HTTP routes. Business logic stays in the RAG pipeline."""

from fastapi import APIRouter, Depends, HTTPException

from ..pipelines import RAGPipeline
from ..services import LLMError
from .dependencies import get_rag_pipeline
from .schemas import AskRequest, AskResponse, HealthResponse
from university_knowledge_assistant import __version__

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Basic liveness information; the LLM is deliberately not probed here."""
    return HealthResponse(status="ok", version=__version__)


@router.post("/ask", response_model=AskResponse)
def ask(
    request: AskRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
) -> AskResponse:
    """Answer a question grounded in indexed course material."""
    try:
        result = pipeline.answer(request.question, top_k=request.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Local language model request failed: {exc}",
        ) from exc

    return AskResponse(**result)
