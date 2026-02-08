from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .config import Settings
from .database import Database
from .repositories import ChunkRepository, DocumentRepository, SegmentRepository
from .services.chunking import ChunkBuilder
from .services.documents import DocumentService
from .services.extraction import DocumentExtractor
from .services.gemini import GeminiClient, MissingApiKeyError
from .services.qa import QAService
from .services.storage import FileStorageService
from .services.vector_store import VectorStoreProtocol


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_database(request: Request) -> Database:
    return request.app.state.database


def get_storage_service(request: Request) -> FileStorageService:
    return request.app.state.storage_service


def get_vector_store(request: Request) -> VectorStoreProtocol:
    return request.app.state.vector_store


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


def get_chunk_repository(
    session: Session = Depends(get_db_session),
) -> ChunkRepository:
    return ChunkRepository(session)


def get_gemini_client(request: Request, settings: Settings = Depends(get_settings)) -> GeminiClient:
    cached_client = getattr(request.app.state, "gemini_client", None)
    if cached_client is not None:
        return cached_client

    try:
        client = GeminiClient(
            api_key=settings.gemini_api_key or "",
            model_name=settings.gemini_model,
            embedding_model=settings.gemini_embedding_model,
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


def get_chunk_builder(settings: Settings = Depends(get_settings)) -> ChunkBuilder:
    return ChunkBuilder(chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)


def get_document_service(
    repository: DocumentRepository = Depends(get_document_repository),
    segment_repository: SegmentRepository = Depends(get_segment_repository),
    chunk_repository: ChunkRepository = Depends(get_chunk_repository),
    storage_service: FileStorageService = Depends(get_storage_service),
    extractor: DocumentExtractor = Depends(get_document_extractor),
    chunk_builder: ChunkBuilder = Depends(get_chunk_builder),
    vector_store: VectorStoreProtocol = Depends(get_vector_store),
    ai_client: GeminiClient = Depends(get_gemini_client),
    settings: Settings = Depends(get_settings),
) -> DocumentService:
    return DocumentService(
        repository=repository,
        segment_repository=segment_repository,
        chunk_repository=chunk_repository,
        storage_service=storage_service,
        extractor=extractor,
        chunk_builder=chunk_builder,
        vector_store=vector_store,
        ai_client=ai_client,
        allowed_extensions=settings.allowed_extensions,
    )


def get_qa_service(
    repository: DocumentRepository = Depends(get_document_repository),
    vector_store: VectorStoreProtocol = Depends(get_vector_store),
    ai_client: GeminiClient = Depends(get_gemini_client),
    settings: Settings = Depends(get_settings),
) -> QAService:
    return QAService(
        document_repository=repository,
        vector_store=vector_store,
        ai_client=ai_client,
        retrieval_max_distance=settings.retrieval_max_distance,
    )
