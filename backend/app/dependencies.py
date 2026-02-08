from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .config import Settings
from .database import Database
from .repositories import DocumentRepository, SegmentRepository
from .services.documents import DocumentService
from .services.extraction import DocumentExtractor
from .services.gemini import GeminiClient, MissingApiKeyError
from .services.storage import FileStorageService


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_database(request: Request) -> Database:
    return request.app.state.database


def get_storage_service(request: Request) -> FileStorageService:
    return request.app.state.storage_service


def get_db_session(database: Database = Depends(get_database)) -> Generator[Session, None, None]:
    yield from database.session()


def get_document_repository(
    session: Session = Depends(get_db_session),
) -> DocumentRepository:
    return DocumentRepository(session)


def get_segment_repository(
    session: Session = Depends(get_db_session),
) -> SegmentRepository:
    return SegmentRepository(session)


def get_gemini_client(request: Request, settings: Settings = Depends(get_settings)) -> GeminiClient:
    cached_client = getattr(request.app.state, "gemini_client", None)
    if cached_client is not None:
        return cached_client

    try:
        client = GeminiClient(
            api_key=settings.gemini_api_key or "",
            model_name=settings.gemini_model,
        )
    except MissingApiKeyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    request.app.state.gemini_client = client
    return client


def get_document_extractor(
    ai_client: GeminiClient = Depends(get_gemini_client),
    settings: Settings = Depends(get_settings),
) -> DocumentExtractor:
    return DocumentExtractor(
        ai_client=ai_client,
        min_chars_before_ocr=settings.pdf_min_chars_before_ocr,
    )


def get_document_service(
    repository: DocumentRepository = Depends(get_document_repository),
    segment_repository: SegmentRepository = Depends(get_segment_repository),
    storage_service: FileStorageService = Depends(get_storage_service),
    extractor: DocumentExtractor = Depends(get_document_extractor),
    settings: Settings = Depends(get_settings),
) -> DocumentService:
    return DocumentService(
        repository=repository,
        segment_repository=segment_repository,
        storage_service=storage_service,
        extractor=extractor,
        allowed_extensions=settings.allowed_extensions,
    )
