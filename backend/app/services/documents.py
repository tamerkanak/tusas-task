from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from langdetect import LangDetectException, detect

from ..models import Document
from ..repositories import ChunkRepository, DocumentRepository, SegmentRepository
from ..schemas import AcceptedFile, DocumentSummary, RejectedFile, UploadResponse
from .chunking import ChunkBuilder
from .extraction import DocumentExtractor
from .gemini import GeminiClient
from .storage import FileStorageService
from .vector_store import ChromaVectorStore


class DocumentService:
    def __init__(
        self,
        repository: DocumentRepository,
        segment_repository: SegmentRepository,
        chunk_repository: ChunkRepository,
        storage_service: FileStorageService,
        extractor: DocumentExtractor,
        chunk_builder: ChunkBuilder,
        vector_store: ChromaVectorStore,
        ai_client: GeminiClient,
        allowed_extensions: set[str],
    ) -> None:
        self.repository = repository
        self.segment_repository = segment_repository
        self.chunk_repository = chunk_repository
        self.storage_service = storage_service
        self.extractor = extractor
        self.chunk_builder = chunk_builder
        self.vector_store = vector_store
        self.ai_client = ai_client
        self.allowed_extensions = {value.lower() for value in allowed_extensions}

    async def upload_documents(self, files: list[UploadFile]) -> UploadResponse:
        document_ids: list[str] = []
        accepted_files: list[AcceptedFile] = []
        rejected_files: list[RejectedFile] = []

        for file in files:
            filename = file.filename or "unknown"
            suffix = Path(filename).suffix.lower()

            if suffix not in self.allowed_extensions:
                rejected_files.append(
                    RejectedFile(filename=filename, reason="Desteklenmeyen dosya uzantisi")
                )
                continue

            content = await file.read()
            if not content:
                rejected_files.append(RejectedFile(filename=filename, reason="Dosya bos"))
                continue

            document_id = uuid4().hex
            saved = self.storage_service.save(document_id, filename, content)
            document = Document(
                id=document_id,
                filename=filename,
                file_type=suffix.lstrip("."),
                mime_type=file.content_type or "application/octet-stream",
                storage_path=str(saved.storage_path),
                file_size=saved.file_size,
                status="processing",
                language="unknown",
            )
            self.repository.create(document)

            try:
                segments = self.extractor.extract(saved.storage_path, document.file_type)
                if not segments:
                    raise ValueError("Metin cikarimi basarisiz")

                self.segment_repository.replace_for_document(document_id, segments)
                chunks = self.chunk_builder.build(
                    document_id=document_id,
                    filename=filename,
                    segments=segments,
                )
                if not chunks:
                    raise ValueError("Chunk olusturulamadi")

                embeddings = self.ai_client.embed_texts(
                    [chunk.text for chunk in chunks],
                    task_type="retrieval_document",
                )
                self.chunk_repository.replace_for_document(document_id, chunks)
                self.vector_store.upsert(chunks, embeddings)

                full_text = "\n".join(segment.text for segment in segments)
                language = self._detect_language(full_text)
                self.repository.update_status(
                    document_id,
                    status="indexed",
                    language=language,
                    error_message=None,
                )

                document_ids.append(document_id)
                accepted_files.append(
                    AcceptedFile(
                        document_id=document_id,
                        filename=filename,
                        status="indexed",
                    )
                )
            except Exception as exc:
                self.repository.update_status(
                    document_id,
                    status="failed",
                    error_message=str(exc),
                )
                rejected_files.append(
                    RejectedFile(filename=filename, reason=f"Isleme hatasi: {exc}")
                )

        return UploadResponse(
            document_ids=document_ids,
            accepted_files=accepted_files,
            rejected_files=rejected_files,
        )

    def list_documents(self) -> list[DocumentSummary]:
        records = self.repository.list_all()
        return [
            DocumentSummary(
                id=record.id,
                filename=record.filename,
                file_type=record.file_type,
                language=record.language,
                status=record.status,
                created_at=record.created_at,
            )
            for record in records
        ]

    @staticmethod
    def _detect_language(text: str) -> str:
        sample = text.strip()
        if len(sample) < 20:
            return "unknown"

        try:
            lang = detect(sample)
        except LangDetectException:
            return "unknown"

        if lang in {"tr", "en"}:
            return lang
        return "other"
