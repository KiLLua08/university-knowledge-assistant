"""Pydantic request and response models for the HTTP API."""

from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=10)


class SourceReference(BaseModel):
    filename: str
    page_number: int
    document_id: str
    chunk_id: str


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceReference]


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_status: str = "not_checked"
