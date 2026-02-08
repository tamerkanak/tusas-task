from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RejectedFile(BaseModel):
    filename: str
    reason: str


class AcceptedFile(BaseModel):
    document_id: str
    filename: str
    status: str


class UploadResponse(BaseModel):
    document_ids: list[str]
    accepted_files: list[AcceptedFile]
    rejected_files: list[RejectedFile]


class DocumentSummary(BaseModel):
    id: str
    filename: str
    file_type: str
    language: str
    status: str
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    services: dict[str, str]


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    document_ids: list[str] = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=15)


class Citation(BaseModel):
    document_id: str
    filename: str
    page: int | None
    chunk_id: str
    snippet: str


class AskResponse(BaseModel):
    answer: str
    mode: str
    citations: list[Citation]
    confidence: float
    used_chunks: int
