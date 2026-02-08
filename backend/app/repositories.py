from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Document


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, document: Document) -> Document:
        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)
        return document

    def list_all(self) -> list[Document]:
        statement = select(Document).order_by(Document.created_at.desc())
        return list(self.session.scalars(statement))

    def list_by_ids(self, document_ids: list[str]) -> list[Document]:
        if not document_ids:
            return []
        statement = select(Document).where(Document.id.in_(document_ids))
        return list(self.session.scalars(statement))

    def update_status(
        self,
        document_id: str,
        *,
        status: str,
        language: str | None = None,
        error_message: str | None = None,
    ) -> None:
        document = self.session.get(Document, document_id)
        if document is None:
            return

        document.status = status
        if language is not None:
            document.language = language
        document.error_message = error_message
        self.session.commit()
