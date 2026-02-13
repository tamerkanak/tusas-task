from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..config import Settings
from ..dependencies import get_document_service, get_settings
from ..schemas import DocumentSummary, UploadResponse
from ..services.documents import DocumentService

router = APIRouter(tags=["documents"])


@router.post("/documents", response_model=UploadResponse)
async def upload_documents(
    files: list[UploadFile] = File(...),
    service: DocumentService = Depends(get_document_service),
    settings: Settings = Depends(get_settings),
) -> UploadResponse:
    if len(files) > settings.max_files_per_request:
        raise HTTPException(
            status_code=400,
            detail=f"Tek seferde en fazla {settings.max_files_per_request} dosya yuklenebilir.",
        )
    return await service.upload_documents(files)


@router.get("/documents", response_model=list[DocumentSummary])
def list_documents(
    service: DocumentService = Depends(get_document_service),
) -> list[DocumentSummary]:
    return service.list_documents()
