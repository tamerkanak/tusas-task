from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from ..dependencies import get_document_service
from ..schemas import DocumentSummary, UploadResponse
from ..services.documents import DocumentService

router = APIRouter(tags=["documents"])


@router.post("/documents", response_model=UploadResponse)
async def upload_documents(
    files: list[UploadFile] = File(...),
    service: DocumentService = Depends(get_document_service),
) -> UploadResponse:
    return await service.upload_documents(files)


@router.get("/documents", response_model=list[DocumentSummary])
def list_documents(
    service: DocumentService = Depends(get_document_service),
) -> list[DocumentSummary]:
    return service.list_documents()
