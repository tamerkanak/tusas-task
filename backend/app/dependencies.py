from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from .config import Settings
from .database import Database
from .repositories import DocumentRepository
from .services.documents import DocumentService
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


def get_document_service(
    repository: DocumentRepository = Depends(get_document_repository),
    storage_service: FileStorageService = Depends(get_storage_service),
    settings: Settings = Depends(get_settings),
) -> DocumentService:
    return DocumentService(
        repository=repository,
        storage_service=storage_service,
        allowed_extensions=settings.allowed_extensions,
    )
